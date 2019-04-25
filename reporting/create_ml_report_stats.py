""" Create Statistics Over all TopPredictions """
from collections import Counter, defaultdict
import logging
import argparse
import os

import pandas as pd

from utils.logger import set_logging
from utils.utils import set_file_permission


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--report_path", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='create_ml_report_stats')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['report_path']):
        raise FileNotFoundError("report_path: {} not found".format(
                                args['report_path']))

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    df = pd.read_csv(args['report_path'], dtype='str')
    df.fillna('', inplace=True)

    #####################################
    # Generate Stats
    ######################################

    pred_stats = defaultdict(Counter)
    cols_all = df.columns.tolist()
    toppred_cols = [x for x in cols_all if 'topprediction' in x]

    for _id, pred_data in df.iterrows():
        subject_id = pred_data['capture_id']
        # try to infer whether this prediction is empty
        # and exclude all other columns if so
        try:
            empty_pred = pred_data['machine_topprediction_is_empty']
            is_empty = (empty_pred in ['empty', 'blank'])
        except:
            is_empty = False
        for pred_col in toppred_cols:
            if is_empty:
                if pred_col != 'machine_topprediction_is_empty':
                    continue
            pred = pred_data[pred_col]
            pred_stats[pred_col].update({pred})

    # Print Stats per Question - All Answers
    stats_list = []
    for pred, preds_data in pred_stats.items():
        logger.info(
            "Stats for: {}".format(pred))
        total = sum([x for x in preds_data.values()])
        for answer, count in preds_data.most_common():
            logger.info(
                "Prediction: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                 answer, count, total, 100*count/total))
            stats_list.append(
                [pred, answer, count, total, round(100*count/total, 1)])

    # build df
    df_stats = pd.DataFrame(stats_list)
    df_stats.columns = ['question', 'answer', 'count', 'total', 'percent']

    # export df
    df_stats.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df_stats.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
