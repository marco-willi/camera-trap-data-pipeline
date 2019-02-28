""" Rename images in inventory """
import os
import argparse
import logging

from pre_processing.utils import (read_image_inventory)
from logger import create_logfile_name, setup_logger


def rename_files(source_path, dest_path):
    """ Rename Files """
    for src, dst in zip(source_path, dest_path):
        os.rename(src, dst)


def rename_images_in_inventory(inventory):
    """ Rename all images in inventory """
    source_paths = list()
    dest_paths = list()
    for data in inventory.values():
        source_paths.append(data['image_path_original'])
        dest_paths.append(data['image_path_new'])
    rename_files(source_paths, dest_paths)


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    args = vars(parser.parse_args())

    # logging
    log_file_name = create_logfile_name('rename_images_in_inventory')
    log_file_path = os.path.join(
        os.path.dirname(args['inventory']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    inventory = read_image_inventory(args['inventory'])

    logger.info("Starting to rename images")
    rename_images_in_inventory(inventory)
    logger.info("Finished renaming images")
