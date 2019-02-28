""" Group Input into Captures """
import numpy as np
import os
import argparse
from datetime import datetime
import logging

from pre_processing.utils import (
    image_check_stats, read_image_inventory,
    export_inventory_to_csv, update_time_checks)
from global_vars import pre_processing_flags as flags
from logger import create_logfile_name, setup_logger

# args = dict()
#
# args['input_inventory'] = '/home/packerc/will5448/image_inventory_overview.csv'
# args['output_csv'] = '/home/packerc/will5448/image_inventory_grouped.csv'
# args['ignore_excluded_images'] = False
# args['check_dir'] = '/home/packerc/will5448/processing_checks'


def create_new_image_path(image_data):
    """ Create new image path """
    image_dir = os.path.dirname(image_data['image_path_original'])
    new_name = create_new_image_name(image_data)
    return os.path.join(image_dir, new_name)


def create_new_image_name(image_data):
    """ Create a new image new based on image_data:
        - PLN_S1_A01_R1_IMAG0001.JPG
    """
    season = image_data['season']
    site = image_data['site']
    roll = 'R{}'.format(image_data['roll'])
    image_no_rank = 'IMAG{:04}'.format(image_data['image_rank_in_roll'])
    ending = '.{}'.format(image_data['image_name_original'].split('.')[1])
    new_name = '_'.join([season, site, roll, image_no_rank])
    return ''.join([new_name, ending])


def group_images_into_site_and_roll(inventory):
    # Group images into site and roll
    site_roll_inventory = dict()
    for image_id, image_data in inventory.items():
        if image_data['datetime'] == '':
            continue
        season = image_data['season']
        site = image_data['site']
        roll = image_data['roll']
        season_site_roll_key = '#'.join([season, site, roll])
        if season_site_roll_key not in site_roll_inventory:
            site_roll_inventory[season_site_roll_key] = dict()
        site_roll_inventory[season_site_roll_key][image_id] = image_data
    return site_roll_inventory


# Group images into site and roll
def group_images_into_captures(inventory, flags):
    """ Group images into capture events """

    site_roll_inventory = group_images_into_site_and_roll(inventory)

    image_to_capture = dict()
    for season_site_roll_key, site_roll_data in site_roll_inventory.items():
        # get all images from the current site and roll
        times = list()
        paths = list()
        for image_id, image_data in site_roll_data.items():
            times.append(image_data['datetime'])
            paths.append(image_id)
        # Define the order of the images by 1) time and 2) by name
        datetimes = [
            datetime.strptime(
                x,
                flags['time_formats']['output_datetime_format'])
            for x in times]
        times_seconds = [
            (x-datetime(1970, 1, 1)).total_seconds()
            for x in datetimes]
        ordered_indexes = np.lexsort((paths, times_seconds))
        # Re-order by the newly defined order
        paths_ordered = [paths[i] for i in ordered_indexes]
        times_seconds_ordered = [times_seconds[i] for i in ordered_indexes]
        # Group images into captures if max_delta of subsequent images
        # is below the max_delta_captures
        delta_times_seconds_ordered = [
            abs(times_seconds_ordered[i-1] - times_seconds_ordered[i])
            for i in range(1, len(times_seconds_ordered))]
        # create delta in days
        delta_times_days_ordered = [
            '{:.2f}'.format((x / (60*60*24)))
            for x in delta_times_seconds_ordered]
        delta_times_days_ordered.insert(0, 0)
        # initialize captures and ranks
        capture_ids_ordered = [1]
        image_rank_in_capture_ordered = [1]
        image_rank_in_roll_ordered = [1]
        current_capture = 1
        current_rank_in_capture = 1
        # loop over all deltas
        # (starting with the delta between first and second)
        for i, delta in enumerate(delta_times_seconds_ordered):
            if delta <= flags['general']['capture_delta_seconds']:
                current_rank_in_capture += 1
            else:
                current_rank_in_capture = 1
                current_capture += 1
            capture_ids_ordered.append(current_capture)
            image_rank_in_capture_ordered.append(current_rank_in_capture)
            image_rank_in_roll_ordered.append(i+2)
        for i in range(0, len(paths_ordered)):
            image_to_capture[paths_ordered[i]] = {
                'capture': capture_ids_ordered[i],
                'image_rank_in_capture': image_rank_in_capture_ordered[i],
                'image_rank_in_roll': image_rank_in_roll_ordered[i],
                'days_to_last_image_taken': delta_times_days_ordered[i],
            }
    return image_to_capture


def update_inventory_with_capture_data(inventory, image_to_capture):
    """ update inventory with capture data """
    # merge capture info with inventory
    # and determine new image names
    for image_path_original, image_capture_data in image_to_capture.items():
        # add capture information
        inventory[image_path_original].update(image_capture_data)
        # create new paths
        image_data = inventory[image_path_original]
        inventory[image_path_original]['image_path_new'] = \
            create_new_image_path(image_data)
        inventory[image_path_original]['image_name_new'] = \
            create_new_image_name(image_data)


def update_time_checks_inventory(inventory, flags):
    """ Update time check flags in inventory """
    for image_id, image_data in inventory.items():
        try:
            update_time_checks(image_data, flags)
        except:
            pass


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument("--no_older_than_year", type=int, default=1970)
    parser.add_argument("--no_newer_than_year", type=int, default=9999)
    args = vars(parser.parse_args())

    # image check paramters
    msg_width = 99

    # logging
    log_file_name = create_logfile_name('group_inventory_into_captures')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
    logger = logging.getLogger(__name__)

    # update time checks
    time_checks = flags['image_check_parameters']
    time_checks['time_too_old']['min_year'] = args['no_older_than_year']
    time_checks['time_too_new']['max_year'] = args['no_newer_than_year']

    inventory = read_image_inventory(
        args['inventory'],
        unique_id='image_path_original')

    image_to_capture = group_images_into_captures(inventory, flags)

    update_inventory_with_capture_data(inventory, image_to_capture)

    update_time_checks_inventory(inventory, flags)

    image_check_stats(inventory, logger)

    export_inventory_to_csv(inventory, args['output_csv'])
