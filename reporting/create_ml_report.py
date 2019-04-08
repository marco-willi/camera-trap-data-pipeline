""" Add Machine Predictions to Season Captures """
import logging
import os
import argparse
import pandas as pd

from utils.logger import setup_logger, create_log_file
from utils.utils import (
    read_cleaned_season_file_df, set_file_permission, sort_df_by_capture_id)
from reporting.create_zooniverse_report import create_season_dict

# args = dict()
# args['season_captures_csv'] = '/home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv'
# args['predictions_csv'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/GRU_S1_ml_preds_flat.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/ConsensusReports/GRU/GRU_S1_report_ml.csv'
# args['export_only_with_predictions'] = False

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--season_captures_csv", type=str, required=True)
    parser.add_argument("--predictions_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--export_only_with_predictions", action="store_true")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='create_ml_report')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['season_captures_csv']):
        raise FileNotFoundError("season_captures_csv: {} not found".format(
                                args['season_captures_csv']))

    if not os.path.isfile(args['predictions_csv']):
        raise FileNotFoundError("predictions_csv: {} not found".format(
                                args['predictions_csv']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    season_data_df = read_cleaned_season_file_df(args['season_captures_csv'])
    season_dict = create_season_dict(season_data_df)

    random_record = season_dict[list(season_dict.keys())[0]]
    season_header = list(random_record.keys())

    # Import Flatt Predictions
    df_preds = pd.read_csv(
        args['predictions_csv'], dtype='str',
        index_col='capture_id')
    df_preds.fillna('', inplace=True)
    df_preds.index.name = 'capture_id'

    # Join season captures with preds
    season_df = pd.DataFrame.from_dict(season_dict, orient='index')
    season_df.index.name = 'capture_id'

    if args['export_only_with_predictions']:
        df_merged = pd.merge(
            season_df, df_preds, how='inner',
            left_index=True, right_index=True)
    else:
        df_merged = pd.merge(
            season_df, df_preds, how='left',
            left_index=True, right_index=True)
        df_merged.fillna('', inplace=True)

    # export
    sort_df_by_capture_id(df_merged)
    df_merged.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_merged.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
