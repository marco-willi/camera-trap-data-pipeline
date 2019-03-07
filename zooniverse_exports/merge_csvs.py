""" Merge CSVs based on common key """
import os
import logging
import argparse

from logger import setup_logger
from utils import merge_csvs, sort_df_by_capture_id, set_file_permission

# args = dict()
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_subjects_extracted.csv'
# args['input_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated_subject_info.csv'

# args = dict()
# args['base_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_annotations.csv'
# args['to_add_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_subjects_extracted.csv'
# args['output_csv'] = ''
# args['key'] = 'subject_id'


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_csv", type=str, required=True)
    parser.add_argument("--to_add_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--key", type=str, required=True)

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['input_csv']):
        raise FileNotFoundError("input_csv: {} not found".format(
                                args['input_csv']))

    if not os.path.isfile(args['subject_csv']):
        raise FileNotFoundError("subject_csv: {} not found".format(
                                args['subject_csv']))

    if args['output_csv'] is None:
        args['output_csv'] = args['input_csv']

    ######################################
    # Configuration
    ######################################

    setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    df = merge_csvs(args['base_csv'], args['to_add_csv'], args['key'])
    # sort by capture_id
    if args['key'] == 'capture_id':
        sort_df_by_capture_id(df)

    df.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
