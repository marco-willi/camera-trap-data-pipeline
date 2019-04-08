""" Update Captures after applying actions"""
import os
import argparse
import logging
from collections import OrderedDict

from utils.logger import setup_logger, create_log_file
from config.cfg import cfg
from pre_processing.utils import (
    read_image_inventory, export_inventory_to_csv, image_check_stats)
from pre_processing.group_inventory_into_captures import (
    group_images_into_captures,
    update_inventory_with_capture_data,
    update_time_checks_inventory,
    calculate_time_deltas,
    update_inventory_with_capture_id
)


flags = cfg['pre_processing_flags']

# args = dict()
# args['captures'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_captures.csv'
# args['captures_updated'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_captures_updated2.csv'
# args['no_older_than_year'] = 0000
# args['no_newer_than_year'] = 9999


def include_image(image_data):
    """ Rule to include only certain images """
    if 'action_taken' in image_data:
        if image_data['action_taken'] in ('delete', 'invalidate'):
            return False
    return True


def select_valid_images(captures):
    """ Select valid images """
    captures_updated = OrderedDict()
    for image_name, image_data in captures.items():
        if not include_image(image_data):
            continue
        try:
            image_data['invalid'] = image_data['action_taken']
        except:
            image_data['invalid'] = ''
        captures_updated[image_name] = {k: v for k, v in image_data.items()}
    return captures_updated


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--captures_updated", type=str, required=True)
    parser.add_argument("--no_older_than_year", type=int, default=1970)
    parser.add_argument("--no_newer_than_year", type=int, default=9999)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='update_captures')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    # logging
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    # update time checks
    time_checks = flags['image_check_parameters']
    time_checks['time_too_old']['min_year'] = args['no_older_than_year']
    time_checks['time_too_new']['max_year'] = args['no_newer_than_year']

    # read captures
    captures = read_image_inventory(
        args['captures'],
        unique_id='image_name')

    captures_updated = select_valid_images(captures)

    # re-calculate time_deltas
    time_deltas = calculate_time_deltas(captures_updated, flags)
    update_inventory_with_capture_data(captures_updated, time_deltas)

    # update image to capture association
    image_to_capture = group_images_into_captures(captures_updated, flags)
    update_inventory_with_capture_data(captures_updated, image_to_capture)

    update_inventory_with_capture_id(captures_updated)

    update_time_checks_inventory(captures_updated, flags)

    image_check_stats(captures_updated, logger)

    # first columns in exported file
    first_cols_to_export = [
        'capture_id', 'season', 'site', 'roll', 'capture',
        'image_rank_in_capture', 'image_path', 'image_path_rel',
        'invalid', 'date', 'time']

    export_inventory_to_csv(
            captures_updated,
            args['captures_updated'],
            first_cols=first_cols_to_export)
