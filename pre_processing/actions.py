""" Define Actions """
import logging
import os
from collections import namedtuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Format of an Action
Action = namedtuple(
    'Action',
    ['image', 'action', 'reason', 'shift_time_by_seconds'])


def _concat_string(old, new):
    """ Concatenate by # """
    return '#'.join(old.split('#') + [new])


def apply_action(image_data, action_dict, flags):
    """ apply an action to an image """
    if isinstance(action_dict, dict):
        action = Action(**action_dict)
    elif isinstance(action_dict, Action):
        action = action_dict
    else:
        raise ValueError("action_dict has wrong type: {}".format(
            type(action_dict)))
    # create empty flags
    for flag in flags['image_flags_to_create']:
        if flag not in image_data:
            image_data[flag] = ''
    if action.action == 'delete':
        _delete(image_data, action)
    elif action.action == 'timechange':
        _change_time(image_data, action, flags)
    if action.action in flags['map_actions_to_flags']:
        _create_flag(image_data, action, flags)
    # add action taken
    if 'action_taken' in image_data:
        image_data['action_taken'] = _concat_string(
            image_data['action_taken'], action.action)
    else:
        image_data['action_taken'] = action.action
    if 'action_taken_reason' in image_data:
        image_data['action_taken_reason'] = _concat_string(
            image_data['action_taken_reason'], action.reason)
    else:
        image_data['action_taken_reason'] = action.reason


def _delete(image_data, action):
    """ delete image """
    image_path = image_data['image_path']
    try:
        os.remove(image_path)
        logger.info("Reason: {:20} Action: deleted image: {}".format(
            action.reason, image_path))
    except FileNotFoundError:
        logger.warning(
            "Failed to remove {} - file not found".format(image_path))


def _change_time(image_data, action, flags):
    """ Shift time by seconds """
    old_time = image_data['datetime']
    new_time = _add_seconds_to_time(
        image_data['datetime'],
        action.shift_time_by_seconds, flags['time_formats']['output_datetime_format'])
    image_data['datetime'] = new_time.strftime(
        flags['time_formats']['output_datetime_format'])
    logging.info("Changed datetime for image {} from {} to {}".format(
        action.image, old_time, image_data['datetime']))


def _add_seconds_to_time(date_time, seconds_to_add, format):
    """ Add seconds to time """
    from_datetime = datetime.strptime(
        date_time, format)
    shifted_time = from_datetime + timedelta(seconds=float(seconds_to_add))
    return shifted_time


def _create_flag(image_data, action, flags):
    """ Create a flag """
    get_flag_cols_list = flags['map_actions_to_flags'][action.action]
    for flag_col in get_flag_cols_list:
        image_data[flag_col] = '1'
        logging.info("Reason: {:20} Action: set flag: {} to '1'".format(
            action.reason,
            flag_col
        ))
