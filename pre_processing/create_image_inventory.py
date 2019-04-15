""" Create image inventory """
import os
import argparse
import logging
from collections import OrderedDict


from utils.logger import setup_logger, create_log_file
from pre_processing.utils import (
    image_check_stats, export_inventory_to_csv)
from config.cfg import cfg


flags = cfg['pre_processing_flags']

# args = dict()
# args['root_dir'] = '/home/packerc/shared/albums/ENO/ENO_S1'
# args['output_csv'] = '/home/packerc/shared/season_captures/ENO/ENO_S1_captures_raw.csv'
# #args['output_csv'] = '/home/packerc/will5448/image_inventory_overview.csv'
# args['season_id'] = ''
# args['n_processes'] = 16

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

    # image check paramters
    msg_width = 99

    # check existence of root dir
    if not os.path.isdir(args['root_dir']):
        raise FileNotFoundError(
            "root_dir {} does not exist -- must be a directory".format(
                args['root_dir']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
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
            roll = roll_directory_name.split('_')[1].split('R')[1]
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
                    'image_path_original_rel': image_path_rel,
                    'datetime': '',
                    'date': '',
                    'time': '',
                    'file_creation_date': '',
                    **{'image_check__{}'.format(k):
                        0 for k in flags['image_checks']}}

    image_check_stats(image_inventory, logger)

    export_inventory_to_csv(image_inventory, args['output_csv'])
