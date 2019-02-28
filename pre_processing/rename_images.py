""" Rename images in inventory """
import os
import argparse
import logging

from pre_processing.utils import (read_image_inventory)
from logger import create_log_file, setup_logger


def rename_files(source_path, dest_path, logger):
    """ Rename Files """
    for src, dst in zip(source_path, dest_path):
        try:
            os.rename(src, dst)
        except:
            logger.warning("Failed to rename {} to {}".format(src, dst))
            if not os.isfile(src):
                logger.warning("Source: {} does not exist".format(src))
            if os.isfile(dst):
                logger.warning("Dest: {} already exists".format(dst))
            else:
                logger.warning("Dest: {} does not exist".format(dst))


def rename_images_in_inventory(inventory, logger):
    """ Rename all images in inventory """
    source_paths = list()
    dest_paths = list()
    for data in inventory.values():
        source_paths.append(data['image_path_original'])
        dest_paths.append(data['image_path_new'])
    rename_files(source_paths, dest_paths, logger)


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    args = vars(parser.parse_args())

    # Logging
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['inventory'])
    log_file_path = create_log_file(
        log_file_dir,
        'rename_images')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    inventory = read_image_inventory(args['inventory'])

    logger.info("Starting to rename images")
    rename_images_in_inventory(inventory, logger)
    logger.info("Finished renaming images")
