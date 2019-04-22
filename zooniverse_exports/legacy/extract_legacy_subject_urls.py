""" Extract Legacy ULRs from Oruboros Exports
"""
import json
from collections import OrderedDict
import argparse
import os
import logging

import pandas as pd

from utils.utils import set_file_permission
from utils.logger import create_log_file, setup_logger


# args = dict()
# args['oruboros_export'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subjects_ouroboros.json'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_subject_urls.csv'
#

def extract_image_urls(subject_data, quality):
    """ extract relevant info from pages """
    try:
        url_list = subject_data['location'][quality]
    except:
        url_list = subject_data['location']['standard']
    if len(url_list) > 3:
        url_list = url_list[0:3]
    return url_list


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--oruboros_export", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='extract_legacy_subject_urls')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['oruboros_export']):
        raise FileNotFoundError("oruboros_export: {} not found".format(
                                args['oruboros_export']))

    ######################################
    # Configuration
    ######################################

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    with open(args['oruboros_export'], 'r') as f:
        data = json.load(f)

    logger.info("Imported {} records from {}".format(
        len(data.keys()), args['oruboros_export']))

    capture_images = OrderedDict()
    for capture_id, subject_data in data.items():
        img_list = extract_image_urls(subject_data, 'standard')
        capture_images[capture_id] = {
            'zooniverse_url_{}'.format(i):
                img for i, img in enumerate(img_list)}

    df = pd.DataFrame.from_dict(capture_images, orient='index')
    df.fillna('', inplace=True)
    df.index.name = 'subject_id'
    # export
    df.to_csv(args['output_csv'], index=True)

    logger.info("Exported {} records to {}".format(
        df.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
