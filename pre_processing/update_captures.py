""" Update Captures after applying actions"""
import os
import argparse
import logging
from collections import OrderedDict

from logger import setup_logger, create_log_file
from global_vars import pre_processing_flags as flags
from pre_processing.utils import (
    read_image_inventory, export_inventory_to_csv, image_check_stats)
from pre_processing.group_inventory_into_captures import (
    group_images_into_captures,
    update_inventory_with_capture_data,
    update_time_checks_inventory
)


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=str, required=True)
    parser.add_argument("--captures_updated", type=str, required=True)
    parser.add_argument("--log_dir", type=str, default=None)
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['captures']):
        raise FileNotFoundError(
            "captures {} does not exist -- must be a file".format(
                args['captures']))

    # Logging
    if args['log_dir'] is not None:
        log_file_dir = args['log_dir']
    else:
        log_file_dir = os.path.dirname(args['captures_cleaned'])
    log_file_path = create_log_file(
        log_file_dir,
        'update_captures')
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    def include_image(image_data):
        if 'action_taken' in image_data:
            if image_data['action_taken'] == 'delete':
                return False
        return True

    # read grouped data
    captures = read_image_inventory(
        args['captures'],
        unique_id='image_name')

    # select relevant columns
    captures_updated = OrderedDict()
    cols_to_export = [
        'capture_id', 'season', 'site', 'roll', 'capture',
        'image_rank_in_capture', 'image_path', 'image_path_rel',
        'invalid', 'date', 'time']
    for image_name, image_data in captures.items():
        if not include_image(image_data):
            continue
        try:
            image_data['invalid'] = image_data['action_taken']
        except:
            image_data['invalid'] = ''
        image_data['capture_id'] = '#'.join(
            [image_data['season'], image_data['site'],
             image_data['roll'], image_data['capture']])
        # image_data_new = {k: v for k, v in image_data if k in cols_to_export}
        captures_updated[image_name] = {k: v for k, v in image_data.items()}

    # update image to capture association
    image_to_capture = group_images_into_captures(captures_updated, flags)

    update_inventory_with_capture_data(captures_updated, image_to_capture)

    update_time_checks_inventory(captures_updated, flags)

    image_check_stats(captures, logger)

    export_inventory_to_csv(
            captures_updated,
            args['captures_updated'],
            first_cols=cols_to_export)
