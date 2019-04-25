""" Create an image inventory for all captures in a report
    - creates a file with capture_id -> images path
"""
import logging
import os
import argparse
import pandas as pd

from utils.logger import set_logging
from utils.utils import (
    set_file_permission,
    read_cleaned_season_file_df, remove_images_from_df)
from config.cfg import cfg


flags_report = cfg['report_flags']


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--report_csv", type=str, required=True)
    parser.add_argument("--season_captures_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='create_image_inventory')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['season_captures_csv']):
        raise FileNotFoundError("season_captures_csv: {} not found".format(
                                args['season_captures_csv']))

    if not os.path.isfile(args['report_csv']):
        raise FileNotFoundError("report_csv: {} not found".format(
                                args['report_csv']))

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    ######################################
    # Read Season File
    ######################################

    # read captures data
    season_data_df = read_cleaned_season_file_df(args['season_captures_csv'])
    n_images_in_season_data = season_data_df.shape[0]
    logger.info("Read {} records from {}".format(
        n_images_in_season_data, args['season_captures_csv']))

    # remove ineligible images
    season_data_df = remove_images_from_df(
        season_data_df,
        flags_report['images_to_remove_from_report'])
    n_images_removed = n_images_in_season_data - season_data_df.shape[0]
    logger.info("Removed {} ineligible images from {} -- {} remaining".format(
        n_images_removed, args['season_captures_csv'], season_data_df.shape[0]
    ))

    ######################################
    # Read Report File
    ######################################

    df_report = pd.read_csv(args['report_csv'], index_col=False, dtype=str)

    ######################################
    # Inner Join on Capture ID
    ######################################

    if 'path' in season_data_df.columns:
        path_col = 'path'
    elif 'image_path_rel' in season_data_df.columns:
        path_col = 'image_path_rel'
    else:
        raise ValueError(
            "season_data_df must have one of 'path' or 'image_path_rel'")

    df_images = pd.merge(
        left=season_data_df[['capture_id', path_col]],
        right=df_report[['capture_id']],
        on='capture_id',
        how='inner'
    )

    df_images.columns = ['capture_id', 'image_path_rel']

    logger.info(
        "Merged 'season_captures_csv' with 'report_csv': {} records".format(
            df_images.shape[0]))

    ######################################
    # Export
    ######################################

    # export df
    df_images.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_images.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
