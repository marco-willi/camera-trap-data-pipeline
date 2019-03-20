""" Sample Report
    - select a small sample and export
"""
import pandas as pd
import os
import argparse
import logging

from logger import setup_logger, create_log_file
from config.cfg import cfg
from utils import (
    set_file_permission, balanced_sample_best_effort, print_nested_dict)


flags = cfg['plurality_aggregation_flags']
flags_global = cfg['global_processing_flags']


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--report_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--sample_size", type=int, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='sample_report')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['report_csv']):
        raise FileNotFoundError("report_csv: {} not found".format(
                                args['report_csv']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # logging flags
    print_nested_dict('', flags)

    question_main_id = flags_global['QUESTION_DELIMITER'].join(
        [flags_global['QUESTION_PREFIX'], flags_global['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags_global['QUESTION_PREFIX'],
        flags_global['QUESTION_DELIMITER'])

    # read report
    df_report = pd.read_csv(args['report_csv'], dtype='str')
    df_report.fillna('', inplace=True)

    # get main answer of each record to sample from it
    main_answers = df_report[question_main_id]

    _ids_all = [i for i in range(0, df_report.shape[0])]

    _ids_sampled = \
        balanced_sample_best_effort(
            main_answers, args['sample_size'])

    _ids_sampled_mapped = [_ids_all[i] for i in _ids_sampled]

    # keep only specific rows
    df_sampled = df_report.iloc[_ids_sampled_mapped, :]

    # export df
    df_sampled.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_sampled.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
