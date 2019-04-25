""" Create a Machine Learning Input File from a Cleaned Season Captures CSV
    to generate predictions for the captures
"""
import os
import csv
import argparse
import logging

from collections import OrderedDict

from utils.logger import set_logging
from utils.utils import (
    set_file_permission, read_cleaned_season_file_df)

# #For Testing
# args = dict()
# args['cleaned_csv'] = "/home/packerc/shared/season_captures/SER/cleaned/SER_S1_cleaned.csv"
# args['output_csv'] = "/home/packerc/shared/zooniverse/MachineLearning/SER/SER_S1_machine_learning_input.csv"
# args['max_images_per_capture'] = 3

if __name__ == "__main__":

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cleaned_csv", type=str, required=True,
        help="Cleaned season captures csv")
    parser.add_argument(
        "--output_csv", type=str, default=None,
        help="Output file with one row per capture and image paths.")
    parser.add_argument(
        "--max_images_per_capture", type=int, default=3,
        help="The maximum number of images per capture event (default 3)")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='create_machine_learning_file')

    args = vars(parser.parse_args())

    # Check Inputs
    if not os.path.exists(args['cleaned_csv']):
        raise FileNotFoundError("cleaned_csv: %s not found" %
                                args['cleaned_csv'])

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # Read the Manifest
    cleaned_csv = read_cleaned_season_file_df(args['cleaned_csv'])

    if 'capture_id' not in cleaned_csv.columns:
        logger.error("Column 'capture_id' not found in cleaned_csv: {}".format(
            args['cleaned_csv']
        ))
        raise ImportError("cleaned_csv must have column capture_id")

    logger.info("Found {} images in {}".format(
                cleaned_csv.shape[0], args['cleaned_csv']))

    # collect all images per capture
    capture_to_images = OrderedDict()

    for row_no, row in cleaned_csv.iterrows():
        if row.capture_id not in capture_to_images:
            capture_to_images[row.capture_id] = list()
        if len(capture_to_images[row.capture_id]) < args['max_images_per_capture']:
            capture_to_images[row.capture_id].append(row.path)

    logger.info("Found {} captures with images".format(
        len(capture_to_images.keys())))

    with open(args['output_csv'], 'w') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',')
        # write header
        n_images = args['max_images_per_capture']
        image_cols = ['image%s' % x for x in range(1,  n_images + 1)]
        header = ['capture_id'] + image_cols
        csvwriter.writerow(header)
        # Write each capture event and the associated images
        for capture_id, image_paths in capture_to_images.items():
            image_paths_to_write = ['' for i in range(0, n_images)]
            for i, image in enumerate(image_paths):
                image_paths_to_write[i] = image
            row_to_write = [capture_id]
            row_to_write += image_paths_to_write
            csvwriter.writerow(row_to_write)

    logger.info("Wrote {} records to {}".format(
        len(capture_to_images.keys()), args['output_csv']))

    set_file_permission(args['output_csv'])
