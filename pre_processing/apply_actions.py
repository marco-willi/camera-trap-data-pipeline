""" Apply Actions """
import os
import argparse
import logging
from datetime import datetime, timedelta

from logger import setup_logger, create_log_file
from pre_processing.utils import read_image_inventory, export_inventory_to_csv
from global_vars import pre_processing_flags as flags

# args = dict()
# args['actions_to_perform'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_actions_inventory.csv'
# args['captures'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_captures.csv'
# args['log_dir'] = '/home/packerc/shared/season_captures/APN/log_files/'


def delete_image(captures, image_name, logger):
    """ delete image """
    image_path = captures[image_name]['image_path']
    os.remove(image_path)
    logger.info("Deleted image: {}".format(image_path))


def change_time(captures, image_name, flags, shift_by_seconds):
    """ Shift time by seconds """
    image_data = captures[image_name]
    old_time = image_data['datetime']
    new_time = add_seconds_to_time(
        image_data['datetime'],
        shift_by_seconds, flags['time_formats']['output_datetime_format'])
    image_data['datetime'] = new_time.strftime(
        flags['time_formats']['output_datetime_format'])
    image_data['date'] = new_time.strftime(
        flags['time_formats']['output_date_format'])
    image_data['time'] = new_time.strftime(
        flags['time_formats']['output_time_format'])
    logging.info("Changed date/time for image {} from {} to {}".format(
        image_name, old_time, image_data['datetime']))


def add_seconds_to_time(date_time, seconds_to_add, format):
    """ Add seconds to time """
    from_datetime = datetime.strptime(
        date_time, format)
    shifted_time = from_datetime + timedelta(seconds=float(seconds_to_add))
    return shifted_time


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--actions_to_perform", type=str, required=True)
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['actions_to_perform']):
        raise FileNotFoundError(
            "actions_to_perform {} does not exist -- must be a file".format(
                args['actions_to_perform']))

    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    # logging
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['actions_to_perform'])
    log_file_path = create_log_file(log_file_dir, 'apply_actions')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    actions = read_image_inventory(
        args['actions_to_perform'], unique_id='image_name')
    captures = read_image_inventory(
        args['captures'], unique_id='image_name')

    for image_name, action in actions.items():
        if action['action_to_take'] == 'delete':
            delete_image(captures, image_name, logger)
        elif action['action_to_take'] == 'timechange':
            change_time(
                captures,
                image_name, flags,
                action['action_shift_time_by_seconds'])
        captures[image_name]['action_taken'] = \
            action['action_to_take']
        captures[image_name]['action_reason'] = \
            action['action_to_take_reason']

    export_inventory_to_csv(captures, args['captures'])
