""" Generate Actions from Actions List """
import os
import argparse
import logging
import pandas as pd
import textwrap
import traceback
from datetime import datetime
from collections import OrderedDict

from logger import setup_logger, create_log_file
from pre_processing.utils import read_image_inventory
from global_vars import pre_processing_flags as flags
from utils import set_file_permission

# args = dict()
# args['action_list'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_action_list_TEST1.csv'
# args['actions_to_perform'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_actions_inventory.csv'
# args['captures'] = '/home/packerc/shared/season_captures/APN/captures/APN_S2_TEST_canBeDeleted_captures.csv'
# args['log_dir'] = '/home/packerc/shared/season_captures/APN/log_files/'


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--action_list", type=str, required=True)
    parser.add_argument("--actions_to_perform_csv", type=str, required=True)
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
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
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['actions_to_perform_csv'])
    log_file_path = create_log_file(log_file_dir, 'generate_actions_to_peform')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    # Parameters
    msg_width = 150
    valid_actions = ('delete', 'ok', 'invalidate', 'timechange')

    # read files
    captures = read_image_inventory(
        args['captures'], unique_id='image_name')
    action_list = read_image_inventory(
        args['action_list'], unique_id=None)

    def check_site_specified_if_roll_action(action):
        """ Check that site is specified if roll is """
        if action['action_roll'] != '':
            if action['action_site'] == '':
                msg = textwrap.shorten(
                        "if action_roll is specified so must action_site",
                        width=msg_width)
                raise ImportError(msg)

    def check_action_has_action_item(action):
        """ Check that action has an item to act on """
        if action['action_site'] == '':
            if action['action_roll'] == '':
                if action['action_from_image'] == '':
                    msg = textwrap.shorten(
                            "any of action_site, action_roll, \
                             action_from_image must be specified",
                            width=msg_width)
                    raise ImportError(msg)

    def check_site_roll_not_specified_if_image(action):
        """ Check that site and roll not specified if image is specified """
        if action['action_from_image'] != '':
            if any([x != '' for x in [action['action_roll'], action['action_site']]]):
                msg = textwrap.shorten(
                        "if action_from_image specified, action_roll \
                         and action_site must be empty",
                        width=msg_width)
                raise ImportError(msg)

    def check_image_to_if_image_from(action):
        """ Check if image_to is specified if image_from is """
        if action['action_from_image'] != '':
            if action['action_to_image'] == '':
                msg = textwrap.shorten(
                        "action_from_image is specified, therefore \
                        action_to_image must not be empty",
                        width=msg_width)
                raise ImportError(msg)

    def check_image_from_if_image_to(action):
        """ Check that image_from is specified if image_to is """
        if action['action_to_image'] != '':
            if action['action_from_image'] == '':
                msg = textwrap.shorten(
                        "action_to_image is specified, therefore \
                         action_from_image must not be empty",
                        width=msg_width)
                raise ImportError(msg)

    def check_datetime_format(action, date_format):
        if action['datetime_current'] != '':
            try:
                datetime.strptime(action['datetime_current'], date_format)
            except:
                msg = textwrap.shorten(
                        "datetime format in datetime_current invalid, \
                         must be {}, is {}".format(
                         date_format, action['datetime_current']),
                        width=msg_width)
                raise ImportError(msg)
        if action['datetime_new'] != '':
            try:
                datetime.strptime(action['datetime_new'], date_format)
            except:
                msg = textwrap.shorten(
                        "datetime format in datetime_new invalid, \
                         must be {}, is {}".format(
                         date_format, action['datetime_new']),
                        width=msg_width)
                raise ImportError(msg)

    def check_action_is_valid(action):
        if action['action_to_take'] not in valid_actions:
            msg = textwrap.shorten(
                    "action {} not a valid action, valid actions are {}".format(
                     action['action_to_take'], valid_actions),
                    width=msg_width)
            raise ImportError(msg)
        if action['action_to_take'] == 'timechange':
            assert ((action['datetime_current'] != '') and
                    (action['datetime_new'] != '')), \
                textwrap.shorten(
                    "if action_to_take is 'timechange' \
                    datetime_current \
                    and datetime_new must be specified", width=msg_width)

    def check_action_reason_given(action):
        if action['action_to_take_reason'] == '':
            msg = textwrap.shorten(
                    "action_to_take_reason must be specified",
                    width=msg_width)
            raise ImportError(msg)

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
        actions = OrderedDict()
        for image in image_list:
            current_action = {
                'image_name': image,
                'action_to_take_reason': action['action_to_take_reason'],
                'action_to_take': action['action_to_take'],
                'action_shift_time_by_seconds': 0
                }
            if action['action_to_take'] == 'timechange':
                time_diff = calculate_time_difference_seconds(
                    action['datetime_current'], action['datetime_new'],
                    flags['time_formats']['output_datetime_format'])
                current_action['action_shift_time_by_seconds'] = time_diff
            actions[image] = current_action
        return actions

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

    actions_inventory = OrderedDict()
    for _id, action in action_list.items():
        # check action file
        try:
            check_site_specified_if_roll_action(action)
            check_action_has_action_item(action)
            check_site_roll_not_specified_if_image(action)
            check_image_to_if_image_from(action)
            check_image_from_if_image_to(action)
            check_action_is_valid(action)
            check_action_reason_given(action)
            check_datetime_format(
                action,
                flags['time_formats']['output_datetime_format'])
        except Exception:
            print(traceback.format_exc())
            logger.error("error in row {}".format(_id+1))
            raise ValueError("error in row {}".format(_id+1))
        # determine the scope of the current action
        action_scope = get_action_scope(action)
        # get all images to perform actions on and assign the specific action
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
            logger.error("action_scope {} not recognized".format(action_scope))
            raise ValueError(
                "action_scope {} not recognized".format(action_scope))
        # generate actions for all images
        actions_dict = generate_actions_for_images(action, images)
        for img, img_action in actions_dict.items():
            # handle case where multiple actions have been selected for the
            # same image, prioritize delete > timechange > others
            if img in actions_inventory:
                existing_action = actions_dict[img]['action_to_take']
                logger.warning(
                    textwrap.shorten(
                        "image {} has more than one action, \
                         found action {}, additional action {} \
                         prioritizing deletion > timechange > others".format(
                         img,
                         existing_action,
                         img_action['action_to_take']
                        ), width=msg_width))
                if img_action['action_to_take'] == 'delete':
                    actions_dict[img].update(img_action)
                elif existing_action in ('delete', 'timechange'):
                    continue
                else:
                    actions_dict[img].update(img_action)
            actions_inventory[img] = img_action

    # Export actions list
    df = pd.DataFrame.from_dict(actions_inventory, orient='index')
    df.to_csv(args['actions_to_perform_csv'], index=False)
    set_file_permission(args['actions_to_perform_csv'])
