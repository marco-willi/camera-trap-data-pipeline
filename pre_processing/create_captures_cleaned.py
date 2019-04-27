""" Create Final Cleaned Captures file """
import logging
import os
import argparse

import pandas as pd

from utils.logger import set_logging
from utils.utils import set_file_permission, sort_df
from config.cfg import cfg


flags = cfg['pre_processing_flags']


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--captures_cleaned", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='create_captures_cleaned')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    ######################################
    # Configuration
    ######################################

    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    ######################################
    # Read and Prepare Data
    ######################################

    # read captures
    df = pd.read_csv(args['captures'], dtype='str')
    df.fillna('', inplace=True)

    # get flags
    try:
        first_cols = flags['final_cleaned']['first_columns']
    except KeyError:
        first_cols = []

    try:
        exclude_columns = flags['final_cleaned']['exclude_columns']
    except KeyError:
        exclude_columns = []

    try:
        exclude_exif_data = flags['final_cleaned']['exclude_exif_data']
    except KeyError:
        exclude_exif_data = False

    try:
        exclude_image_check_flags = \
            flags['final_cleaned']['exclude_image_check_flags']
    except KeyError:
        exclude_image_check_flags = False

    # determine column order
    all_cols = df.columns

    # get first cols
    output_cols = [x for x in first_cols if x in all_cols]

    # add remaining cols
    remaining_cols = [x for x in all_cols if x not in output_cols]
    output_cols += remaining_cols

    # remove cols
    output_cols = [x for x in output_cols if x not in exclude_columns]
    if exclude_exif_data:
        output_cols = [x for x in output_cols if not x.startswith('exif__')]
    if exclude_image_check_flags:
        output_cols = [x for x in output_cols if not x.startswith('image_check__')]

    # select cols
    df = df[output_cols]
    sort_df(df)

    ######################################
    # Export
    ######################################

    # export
    df.to_csv(args['captures_cleaned'], index=False)

    set_file_permission(args['captures_cleaned'])
