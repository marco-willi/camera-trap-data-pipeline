""" Create image inventory """
import os
import argparse
import logging
from collections import OrderedDict


from utils.logger import set_logging
from utils.utils import check_dir_existence
from pre_processing.utils import (
    image_check_stats, export_inventory_to_csv,
    get_rollnum_from_roll_directory)
from config.cfg import cfg


flags = cfg['pre_processing_flags']


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--root_dir", type=str, required=True)
    parser.add_argument(
        "--season_id", type=str, default="",
        help="identifier that is exported to the inventory")
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='create_image_inventory')
    args = vars(parser.parse_args())

    # image check parameters
    msg_width = 99

    check_dir_existence(args['root_dir'])

    set_logging(args['log_dir'], args['log_filename'])

    logger = logging.getLogger(__name__)

    last_dir = os.path.basename(os.path.normpath(args['root_dir']))
    if args['season_id'] == '':
        args['season_id'] = last_dir
        logger.info("Updating 'season_id' with {}".format(
            args['season_id']))

    site_directory_names = os.listdir(args['root_dir'])

    image_inventory = OrderedDict()

    # Loop over site directories
    for site_directory_name in site_directory_names:
        current_dir_full_path = os.path.join(
            args['root_dir'], site_directory_name)
        roll_directory_names = os.listdir(current_dir_full_path)
        # Loop over roll directories
        for roll_directory_name in roll_directory_names:
            roll = get_rollnum_from_roll_directory(roll_directory_name)
            roll_directory_path = os.path.join(
                current_dir_full_path, roll_directory_name)
            roll_directory_path_rel = os.path.join(
                site_directory_name, roll_directory_name)
            image_file_names = os.listdir(roll_directory_path)
            # Loop over image files
            for image_file_name in image_file_names:
                image_path = os.path.join(roll_directory_path, image_file_name)
                image_path_rel = os.path.join(
                    last_dir,
                    roll_directory_path_rel,
                    image_file_name)
                image_inventory[image_path] = {
                    'season': args['season_id'],
                    'site': site_directory_name,
                    'roll': roll,
                    'image_name_original': image_file_name,
                    'image_path_original': image_path,
                    'image_path_original_rel': image_path_rel}

    image_check_stats(image_inventory, logger)

    export_inventory_to_csv(image_inventory, args['output_csv'])
