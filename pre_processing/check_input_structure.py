""" Check Input Data
    - expected input, one root directory with:
        - site_folder:
            23
            B01
            - site_roll_folder:
                23_R1
                23_R2
                - image files:
                    *.JPG
                    *.JPG
    - Code checks for correct structure and naming
    - Prints error messages if input is invalid
"""
import os
import argparse
import logging
import textwrap

from utils.logger import set_logging
from utils.utils import check_dir_existence


def is_ok_site_code(site):
    """ Check if site code is correct, must be alphanumerics only """
    if not site.isalnum():
        return False
    else:
        return True


def is_ok_roll_code(roll):
    """ Check if roll code is correct, must be in the format 'R1'
        - one uppercase R
        - followed by numerics
    """
    if not roll.startswith('R'):
        return False
    roll_number = roll[1:]
    if not roll_number.isnumeric():
        return False
    else:
        return True


def is_ok_roll_directory_name(roll_dir):
    """ Check if roll directory is correct, must be in the format 'A01_R1'
        - site code
        - separated by '_'
        - followed by roll code
    """
    underscore_count = sum([1 for x in roll_dir if x == '_'])
    if underscore_count is not 1:
        return False
    (site, roll) = roll_dir.split('_')
    if not is_ok_site_code(site):
        return False
    elif not is_ok_roll_code(roll):
        return False
    else:
        return True


def _create_invalid_roll_msg(roll_dir, roll_path, msg_width=150):
    msg = "invalid roll directory: {} at {}, must be \
          in the format '[site_code]_R1': [site_code] and \
          [R][one or more numerics] separated by a '_'".format(
          roll_dir, roll_path)
    msg_short = textwrap.shorten(msg, width=msg_width)
    return msg_short


def _create_invalid_site_msg(site_dir, msg_width=150):
    msg = "site directory {} has incorrect format, \
           must only consist of alphanumeric characters".format(
           site_dir)
    msg_short = textwrap.shorten(msg, width=msg_width)
    return msg_short


def _create_roll_site_missmatch_msg(roll_dir, site, site_dir, msg_width=150):
    msg = "First part of roll directory {} is {}, is not \
           identical to site directory {}: \
           change either of them to matching names, \
           Example: C06/C06_R1".format(
          roll_dir, site, site_dir)
    msg_short = textwrap.shorten(msg, width=msg_width)
    return msg_short


def _create_invalid_image_msg(image, roll_dir, msg_width=150):
    msg = "File {} at {} must end in .jpg / .JPG".format(
           image, roll_dir)
    msg_short = textwrap.shorten(msg, width=msg_width)
    return msg_short


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root_dir", type=str, required=True,
        help="Root directory of the organized camera-trap data -- \
        contains the site folders.")
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='check_directory_structure')
    args = vars(parser.parse_args())

    check_dir_existence(args['root_dir'])

    set_logging(args['log_dir'], args['log_filename'])

    logger = logging.getLogger(__name__)

    msg_width = 250

    site_directory_names = os.listdir(args['root_dir'])

    # check each site directory
    for site_directory_name in site_directory_names:
        # check if file is a directory
        dir_full_path = os.path.join(args['root_dir'], site_directory_name)
        if not os.path.isdir(dir_full_path):
            logger.error("site_directory_name {} is not a directory, \
                remove file {}".format(site_directory_name, dir_full_path))
        # check site directory name
        if not is_ok_site_code(site_directory_name):
            msg = _create_invalid_site_msg(
                site_directory_name,
                msg_width)
            logger.error(msg)
    # check each roll in a site directory
    for site_directory_name in site_directory_names:
        # get all roll directories in a site directory
        current_dir_full_path = os.path.join(
            args['root_dir'], site_directory_name)
        roll_directory_names = os.listdir(current_dir_full_path)
        # check rolls
        for roll_directory_name in roll_directory_names:
            roll_directory_path = os.path.join(
                current_dir_full_path, roll_directory_name)
            if not is_ok_roll_directory_name(roll_directory_name):
                msg = _create_invalid_roll_msg(
                    roll_directory_name,
                    roll_directory_path,
                    msg_width)
                logger.error(msg)
            else:
                (site, roll) = roll_directory_name.split('_')
                # site part must be idential to site directory
                if site != site_directory_name:
                    msg = _create_roll_site_missmatch_msg(
                        roll_directory_name,
                        site,
                        site_directory_name,
                        msg_width)
                    logger.error(msg)
                # check each file in a roll directory
                image_file_names = os.listdir(roll_directory_path)
                for image_file_name in image_file_names:
                    # check file ending
                    if not image_file_name.lower().endswith('.jpg'):
                        image_path = os.path.join(
                            roll_directory_path, image_file_name)
                        msg = _create_invalid_image_msg(
                            image_file_name,
                            roll_directory_name,
                            msg_width)
                        logger.error(msg)
    logger.info("Finished checking input structure")
