""" Generate Actions from Actions List """
import os
import argparse
import logging
import pandas as pd
import textwrap
from datetime import datetime

from utils.logger import set_logging
from pre_processing.utils import read_image_inventory
from pre_processing.actions import Action
from config.cfg import cfg
from utils.utils import set_file_permission


flags = cfg['pre_processing_flags']
msg_width = 150

logger = logging.getLogger(__name__)

# args = dict()
# args['action_list'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_action_list_TEST1.csv'
# args['actions_to_perform'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_actions_inventory.csv'
# args['captures'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_captures.csv'
# args['log_dir'] = '/home/packerc/shared/season_captures/APN/log_files/'


###############################
# Define Validity Checks
###############################

def _check_site_specified_if_roll_action(action):
    """ Check that site is specified if roll is """
    if action['action_roll'] != '':
        if action['action_site'] == '':
            msg = textwrap.shorten(
                    "if action_roll is specified so must action_site",
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)


def _check_action_has_action_item(action):
    """ Check that action has an item to act on """
    if action['action_site'] == '':
        if action['action_roll'] == '':
            if action['action_from_image'] == '':
                msg = textwrap.shorten(
                        "any of action_site, action_roll, \
                         action_from_image must be specified",
                        width=msg_width)
                logger.error(msg)
                raise ImportError(msg)


def _check_site_roll_not_specified_if_image(action):
    """ Check that site and roll not specified if image is specified """
    if action['action_from_image'] != '':
        if any([x != '' for x in [action['action_roll'], action['action_site']]]):
            msg = textwrap.shorten(
                    "if action_from_image specified, action_roll \
                     and action_site must be empty",
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)


def _check_image_to_if_image_from(action):
    """ Check if image_to is specified if image_from is """
    if action['action_from_image'] != '':
        if action['action_to_image'] == '':
            msg = textwrap.shorten(
                    "action_from_image is specified, therefore \
                    action_to_image must not be empty",
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)


def _check_image_from_if_image_to(action):
    """ Check that image_from is specified if image_to is """
    if action['action_to_image'] != '':
        if action['action_from_image'] == '':
            msg = textwrap.shorten(
                    "action_to_image is specified, therefore \
                     action_from_image must not be empty",
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)


def _check_datetime_format(action, date_format):
    print_date = datetime.strptime('2000-01-01', '%Y-%m-%d')
    print_date_format = print_date.strftime(date_format)
    if action['datetime_current'] != '':
        try:
            datetime.strptime(action['datetime_current'], date_format)
        except:
            msg = textwrap.shorten(
                    "datetime format in datetime_current invalid, \
                     must be {}, is {}".format(
                     print_date_format, action['datetime_current']),
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)
    if action['datetime_new'] != '':
        try:
            datetime.strptime(action['datetime_new'], date_format)
        except:
            msg = textwrap.shorten(
                    "datetime format in datetime_new invalid, \
                     must be {}, is {}".format(
                     print_date_format, action['datetime_new']),
                    width=msg_width)
            logger.error(msg)
            raise ImportError(msg)


def _check_action_is_allowed(action):
    """ Check if action is allowed """
    if action['action_to_take'] not in flags['allowed_actions_to_take']:
        msg = textwrap.shorten(
                "action {} not a valid action, valid actions are {}".format(
                 action['action_to_take'], flags['allowed_actions_to_take']),
                width=msg_width)
        logger.error(msg)
        raise ImportError(msg)


def _check_timechange_action_is_correct(action):
    """ Check if timechange action is correctly specified """
    if action['action_to_take'] == 'timechange':
        assert ((action['datetime_current'] != '') and
                (action['datetime_new'] != '')), \
            textwrap.shorten(
                "if action_to_take is 'timechange' \
                datetime_current \
                and datetime_new must be specified", width=msg_width)


def _check_datetime_fields(action):
    """ Check datetime_current / datetime_new """
    if any([x != '' for x in [action['datetime_current'],
                              action['datetime_new']]]):
        assert action['action_to_take'] == 'timechange', \
            textwrap.shorten(
                "If 'datetime_current' / 'datetime_new' are \
                specified, 'action_to_take' must be 'timechange', is '{}'",
                width=msg_width).format(action['action_to_take'])


def _check_action_reason_is_valid(action):
    if action['action_to_take_reason'] == '':
        msg = textwrap.shorten(
                "action_to_take_reason must be specified",
                width=msg_width)
        logger.error(msg)
        raise ImportError(msg)
    elif '#' in action['action_to_take_reason']:
        msg = textwrap.shorten(
                " '#' in action_to_take_reason not allowed",
                width=msg_width)
        logger.error(msg)
        raise ImportError(msg)


def check_action_is_valid(action, flags):
    """ Check action format """
    _check_action_is_allowed(action)
    _check_timechange_action_is_correct(action)
    _check_datetime_fields(action)
    _check_action_reason_is_valid(action)
    _check_datetime_format(
        action,
        flags['time_formats']['output_datetime_format'])
    _check_site_specified_if_roll_action(action)
    _check_action_has_action_item(action)
    _check_site_roll_not_specified_if_image(action)
    _check_image_from_if_image_to(action)
    _check_image_to_if_image_from(action)


def get_action_scope(action):
    """ Determine the scope of the action, one of:
        - 'site': action on whole site
        - 'site_roll': action on a roll
        - 'single_image': action on a single image
        - 'image_range': action on a range of images
    """
    if action['action_site'] != '':
        if action['action_roll'] != '':
            return 'site_roll'
        else:
            return 'site'
    elif action['action_from_image'] != '':
        if action['action_to_image'] == action['action_from_image']:
            return 'single_image'
        else:
            return 'image_range'
    else:
        return 'single_image'


def calculate_time_difference_seconds(from_time, to_time, format):
    """ Calculate time difference in seconds """
    from_datetime = datetime.strptime(
        from_time, format)
    to_datetime = datetime.strptime(
        to_time, format)
    from_seconds = (from_datetime-datetime(1970, 1, 1)).total_seconds()
    to_seconds = (to_datetime-datetime(1970, 1, 1)).total_seconds()
    diff = to_seconds - from_seconds
    return diff


def generate_actions_for_images(action, image_list):
    """ Generate Actions for a list of images """
    actions_list = list()
    for image in image_list:
        time_diff = 0
        if action['action_to_take'] == 'timechange':
            time_diff = calculate_time_difference_seconds(
                action['datetime_current'], action['datetime_new'],
                flags['time_formats']['output_datetime_format'])
        current_action = Action(
            image,
            action['action_to_take'],
            action['action_to_take_reason'],
            time_diff)
        actions_list.append(current_action)
    return actions_list


def find_all_images_for_start_end_image(
        first_image, last_image, inventory):
    """ Generate list of all images in a range
        first_image: name of first image in the range
        last_image: name of last image in the range
    """
    images_list = list()
    fetch_images = False
    for image_name, image_data in inventory.items():
        if image_name == first_image:
            fetch_images = True
        if fetch_images:
            images_list.append(image_name)
        if image_name == last_image:
            fetch_images = False
    return images_list


def find_images_for_site_roll(site, roll, inventory):
    """ Find a list of images for a site or a roll """
    images_list = list()
    for image_name, image_data in inventory.items():
        site_match = (image_data['site'] == site)
        roll_match = (image_data['roll'] == roll)
        if site_match and roll_match:
            images_list.append(image_name)
    return images_list


def find_images_for_site(site, inventory):
    """ Find a list of images for a site """
    images_list = list()
    for image_name, image_data in inventory.items():
        site_match = (image_data['site'] == site)
        if site_match:
            images_list.append(image_name)
    return images_list


def generate_actions(action_list, captures):
    """ Generate individual actions from action list """
    actions_inventory = list()
    image_to_action = set()
    for _id, action in action_list.items():
        # check action file
        try:
            check_action_is_valid(action, flags)
        except Exception as e:
            logger.error("error in row {} of action list".format(
                _id+1))
            raise
        # determine the scope of the current action
        action_scope = get_action_scope(action)
        # get all images to perform actions on and
        # assign the specific action
        if action_scope == 'single_image':
            images = [action['action_from_image']]
        elif action_scope == 'image_range':
            images = find_all_images_for_start_end_image(
                action['action_from_image'],
                action['action_to_image'],
                captures)
        elif action_scope == 'site_roll':
            images = find_images_for_site_roll(
                action['action_site'],
                action['action_roll'],
                captures)
        elif action_scope == 'site':
            images = find_images_for_site(
                action['action_site'],
                captures)
        else:
            logger.error(
                "action_scope {} not recognized".format(
                 action_scope))
            raise ValueError(
                "action_scope {} not recognized".format(action_scope))
        # generate actions for all images
        actions_list = generate_actions_for_images(action, images)
        for img_action in actions_list:
            action_key = '{}#{}'.format(img_action.image, img_action.action)
            if action_key in image_to_action:
                if img_action.action == 'timechange':
                    logger.error(
                        "Multiple timechanges for image {} - " +
                        "this can lead to unintended consequences".format(
                         img_action.image))
                    raise ValueError(
                        "Multiple timechanges defined for image {}".format(
                            img_action.image))
                logger.warning(
                    "image {} has identical action type {} twice".format(
                         img_action.image,
                         img_action.action))
            actions_inventory.append(img_action)
            image_to_action.add(action_key)
    return actions_inventory


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--action_list", type=str, required=True)
    parser.add_argument("--actions_to_perform_csv", type=str, required=True)
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str, default='generate_actions')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['action_list']):
        raise FileNotFoundError(
            "action_list {} does not exist -- must be a file".format(
                args['action_list']))

    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    # logging
    set_logging(args['log_dir'], args['log_filename'])
    logger = logging.getLogger(__name__)

    # read files
    captures = read_image_inventory(
        args['captures'], unique_id='image_name')
    action_list = read_image_inventory(
        args['action_list'], unique_id=None)

    actions_inventory = generate_actions(action_list, captures)

    # Export actions list
    df = pd.DataFrame.from_records(actions_inventory, columns=Action._fields)
    df.to_csv(args['actions_to_perform_csv'], index=False)
    set_file_permission(args['actions_to_perform_csv'])
