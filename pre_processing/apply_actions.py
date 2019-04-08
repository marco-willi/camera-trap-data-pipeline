""" Apply Actions """
import os
import argparse
import logging
from datetime import datetime, timedelta

from utils.logger import setup_logger, create_log_file
from pre_processing.utils import read_image_inventory, export_inventory_to_csv
from config.cfg import cfg

# args = dict()
# args['actions_to_perform'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_actions_to_perform.csv'
# args['captures'] = '/home/packerc/shared/season_captures/MAD/captures/MAD_S1_captures.csv'
# args['log_dir'] = '/home/packerc/shared/season_captures/APN/log_files/'

flags = cfg['pre_processing_flags']


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


def apply_actions(actions, captures, logger):
    """ apply actions """
    for image_name, action in actions.items():
        reason = action['action_to_take_reason']
        if action['action_to_take'] == 'delete':
            image_path = captures[image_name]['image_path']
            try:
                os.remove(image_path)
                logger.info("Reason: {:20} Action: deleted image: {}".format(
                    reason, image_path))
            except FileNotFoundError:
                logger.warning(
                    "Failed to remove {} - file not found".format(image_path))
        elif action['action_to_take'] == 'timechange':
            change_time(
                captures,
                image_name, flags,
                action['action_shift_time_by_seconds'])
            logger.info("Reason: {:20} Action: timechange for: {}".format(
                reason, image_name))
        captures[image_name]['action_taken'] = \
            action['action_to_take']
        captures[image_name]['action_reason'] = \
            action['action_to_take_reason']


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--actions_to_perform", type=str, required=True)
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='apply_actions')
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
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    logger.info("Reading actions from {}".format(args['actions_to_perform']))
    actions = read_image_inventory(
        args['actions_to_perform'], unique_id='image_name')

    logger.info("Reading captures from {}".format(args['captures']))
    captures = read_image_inventory(
        args['captures'], unique_id='image_name')

    try:
        apply_actions(actions, captures, logger)
        logger.info("Successfully applied actions")
    except:
        logger.error("Failed to apply actions")

    export_inventory_to_csv(captures, args['captures'])

    logger.info("Updated captures file at: {}".format(args['captures']))
