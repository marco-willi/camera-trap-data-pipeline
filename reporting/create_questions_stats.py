""" Create Statistics Over all Questions """
from collections import Counter, defaultdict
import logging
import argparse
import os

import pandas as pd

from config.cfg import cfg
from logger import setup_logger, create_log_file
from utils import set_file_permission


flags = cfg['global_processing_flags']

#report_path = '/home/packerc/shared/zooniverse/ConsensusReports/SER/SER_S1_report_species.csv'

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--report_path", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='crate_question_stats')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['report_path']):
        raise FileNotFoundError("report_path: {} not found".format(
                                args['report_path']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    question_column_prefix = '{}{}'.format(
        flags['QUESTION_PREFIX'],
        flags['QUESTION_DELIMITER'])

    df = pd.read_csv(args['report_path'], dtype='str')
    df.fillna('', inplace=True)

    ##############################
    # Generate Stats
    ######################################

    question_stats = defaultdict(Counter)
    cols_all = df.columns.tolist()
    question_cols = [x for x in cols_all if x.startswith(question_column_prefix)]
    for _id, identification in df.iterrows():
        subject_id = identification['capture_id']
        for question in question_cols:
            try:
                if 'count' in question:
                    answer = identification[question]
                else:
                    answer = int(round(float(identification[question]), 0))
            except:
                answer = identification[question]
            question_stats[question].update({answer})

    # Print Stats per Question - All Answers
    stats_list = []
    for question, answer_data in question_stats.items():
        logger.info(
            "Stats for: {} - All annotations per subject".format(question))
        total = sum([x for x in answer_data.values()])
        for answer, count in answer_data.most_common():
            logger.info("Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                answer, count, total, 100*count/total))
            stats_list.append(
                [question, answer, count, total, round(100*count/total, 1)])

    # build df
    df_stats = pd.DataFrame(stats_list)
    df_stats.columns = ['question', 'answer', 'count', 'total', 'percent']

    # export df
    df_stats.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_stats.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
