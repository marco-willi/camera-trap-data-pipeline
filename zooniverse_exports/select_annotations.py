""" Select Annotations in Subject Export Only """
import os
import logging
import argparse

import pandas as pd

from utils.logger import set_logging
from utils.utils import set_file_permission


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", type=str, required=True)
    parser.add_argument("--subjects", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument("--log_filename", type=str, default='select_annotations')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['annotations']):
        raise FileNotFoundError("annotations: {} not found".format(
                                args['annotations']))

    if not os.path.isfile(args['subjects']):
        raise FileNotFoundError("subjects: {} not found".format(
                                args['subjects']))

    ######################################
    # Configuration
    ######################################

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    ######################################
    # Read Data
    ######################################

    df_annotations = pd.read_csv(
        args['annotations'], dtype='str')
    df_annotations.fillna('', inplace=True)

    logger.info("Read {} records from {}".format(
        df_annotations.shape[0], args['annotations']))

    df_subjects = pd.read_csv(
        args['subjects'], dtype='str')
    df_subjects.fillna('', inplace=True)

    logger.info("Read {} records from {}".format(
        df_subjects.shape[0], args['subjects']))

    df_subjects = df_subjects[['subject_id']]
    df_subjects.drop_duplicates(subset=['subject_id'], keep='first', inplace=True)

    ######################################
    # Merge
    ######################################

    df = pd.merge(
        left=df_annotations,
        right=df_subjects,
        how='inner'
    )

    logger.info("{} annotations remaining after join".format(df.shape[0]))

    ######################################
    # Export
    ######################################

    df.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} records to {}".format(
        df.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
