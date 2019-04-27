""" Rename images in inventory """
import os
import argparse
import logging

from pre_processing.utils import (read_image_inventory)
from utils.logger import set_logging


def rename_files(source_paths, dest_paths, logger):
    """ Rename Files """
    n_total = len(source_paths)
    for i, (src, dst) in enumerate(zip(source_paths, dest_paths)):
        try:
            os.rename(src, dst)
            logger.debug("renamed {} to {}".format(src, dst))
        except:
            msg_fail = "Failed to rename {} to {}".format(src, dst)
            if not os.path.isfile(src):
                msg_source = "Source: {} does not exist".format(src)
            if os.path.isfile(dst):
                logger.warning("{} - {} - dest: {} already exists".format(
                    msg_fail, msg_source, dst))
            else:
                logger.warning("{} - {} - dest: {} does not exist".format(
                    msg_fail, msg_source, dst))
        if ((i+1) % 1000) == 0:
            logger.info("Renamed {:10}/{} files".format(i+1, n_total))
    logger.info("Finished, renamed {:10}/{} files".format(i+1, n_total))


def rename_images_in_inventory(inventory, logger):
    """ Rename all images in inventory """
    source_paths = list()
    dest_paths = list()
    for data in inventory.values():
        source_paths.append(data['image_path_original'])
        dest_paths.append(data['image_path'])
    rename_files(source_paths, dest_paths, logger)


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='rename_images')
    args = vars(parser.parse_args())

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    inventory = read_image_inventory(args['inventory'])

    logger.info("Starting to rename images")
    rename_images_in_inventory(inventory, logger)
    logger.info("Finished renaming images")
