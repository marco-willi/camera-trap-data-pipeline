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

from utils.logger import setup_logger, create_log_file


# args = dict()
# args['root_dir'] = '/home/packerc/shared/albums/ENO/ENO_S1'
# args['root_dir'] = '/home/packerc/shared/albums/KAR/KAR_S1'
# args['root_dir'] = '/home/packerc/shared/albums/EFA/EFA_S1'


def is_ok_site_code(site):
    """ Check if site code is correct, must be alphanumerics only """
    if not site.isalnum():
        return False
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
    if not is_ok_roll_code(roll):
        return False
    return True


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
            logger.error(
                textwrap.shorten(
                  "site directory {} has incorrect format, \
                  must only consist of alphanumeric characters".format(
                    site_directory_name),
                  width=msg_width))
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
                logger.error(
                    textwrap.shorten(
                      "invalid roll directory: {} at {}, must be \
                      in the format '[site_code]_R1': \
                      [site_code] and \
                      [R][one or more numerics] separated by a '_'".format(
                        roll_directory_name, roll_directory_path),
                      width=msg_width))
            else:
                # split directory name into site and roll identifiers
                (site, roll) = roll_directory_name.split('_')
                # site part must be idential to site directory
                if site != site_directory_name:
                    logger.error(
                        textwrap.shorten(
                          "First part of roll directory {} is {}, is not \
                          identical to site directory {}: \
                          change either of them to matching names, \
                          Example: C06/C06_R1".format(
                            roll_directory_name, site, site_directory_name,
                            ), width=msg_width))
                # check each file in a roll directory
                image_file_names = os.listdir(roll_directory_path)
                for image_file_name in image_file_names:
                    # check file ending
                    if not image_file_name.lower().endswith('.jpg'):
                        image_path = os.path.join(
                            roll_directory_path, image_file_name)
                        logger.error(
                            textwrap.shorten(
                                "File {} at {} must end in .jpg / .JPG".format(
                                 image_file_name, roll_directory_name
                                 ), width=msg_width))

    logger.info("Finished checking input structure")
