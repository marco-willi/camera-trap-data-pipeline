""" Check Captures and Images """
import os
import argparse
import pandas as pd
from collections import OrderedDict
import logging

from pre_processing.utils import (
    plot_site_roll_timelines, read_image_inventory, image_check_stats,
    update_time_checks)
from logger import create_logfile_name, setup_logger
from global_vars import pre_processing_flags as flags

# args = dict()
#
# args['inventory_grouped'] = '/home/packerc/shared/season_captures/ENO/captures/ENO_S1_captures_grouped.csv'
# args['issues_csv'] = '/home/packerc/shared/season_captures/ENO/captures/ENO_S1_images_with_issues.csv'
# args['no_older_than_year'] = 2017
# args['no_newer_than_year'] = 2019
# args['ignore_excluded_images'] = False
# args['plot_timelines'] = True

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory_grouped", type=str, required=True)
    parser.add_argument("--issues_csv", type=str, required=True)
    parser.add_argument("--no_older_than_year", type=int, default=1970)
    parser.add_argument("--no_newer_than_year", type=int, default=9999)
    parser.add_argument("--plot_timelines", action='store_true')
    args = vars(parser.parse_args())

    # check existence of root dir
    if not os.path.isfile(args['inventory_grouped']):
        raise FileNotFoundError(
            "inventory_grouped {} does not exist -- must be a file".format(
                args['inventory_grouped']))

    log_file_name = create_logfile_name('export_issues_csv')
    log_file_path = os.path.join(
        os.path.dirname(args['issues_csv']), log_file_name)
    setup_logger(log_file_path)
    # setup_logger()
    logger = logging.getLogger(__name__)

    time_checks = flags['image_check_parameters']
    if args['no_older_than_year'] is not None:
        time_checks['time_too_old']['min_year'] = args['no_older_than_year']

    if args['no_newer_than_year'] is not None:
        time_checks['time_too_new']['max_year'] = args['no_newer_than_year']

    # read grouped data
    inventory = read_image_inventory(
        args['inventory_grouped'],
        unique_id='image_path_original')

    header = list(inventory[list(inventory.keys())[0]].keys())

    # check columns
    check_columns = [x for x in header if x.startswith('image_check__')]
    basic_checks = ['image_check__{}'.format(x) for x in flags['image_checks_basic']]
    time_checks = ['image_check__{}'.format(x) for x in flags['image_checks_time']]

    # create check columns
    inventory_with_issues = OrderedDict()
    for image_path_original, image_data in inventory.items():
        automatic_status = {
            'recommended_action': '',
            'recommended_action_reason': '',
            'failed_checks_all': '',
            'manual_override_action': '',
            'manual_override_reason': ''
            }
        try:
            update_time_checks(image_data, flags)
        except:
            pass
        at_least_one_basic_check = \
            any([float(image_data[x]) == 1 for x in basic_checks if x in check_columns])
        at_least_one_time_check = \
            any([float(image_data[x]) == 1 for x in time_checks if x in check_columns])
        # generate check-string
        time_checks_list = \
            [x.replace('image_check__', '') for x
             in time_checks if x in check_columns and float(image_data[x]) == 1]
        basic_checks_list = \
            [x.replace('image_check__', '') for x
             in basic_checks if x in check_columns and float(image_data[x]) == 1]
        all_check_string = '#'.join(basic_checks_list + time_checks_list)
        if at_least_one_basic_check:
            automatic_status['recommended_action'] = 'delete'
            automatic_status['recommended_action_reason'] = 'failed_basic_check'
        elif at_least_one_time_check:
            automatic_status['recommended_action'] = 'inspect'
            automatic_status['recommended_action_reason'] = 'failed_time_check'
        automatic_status['failed_checks_all'] = all_check_string
        image_data.update(automatic_status)
        # export problematic cases only
        if at_least_one_basic_check or at_least_one_time_check:
            inventory_with_issues[image_path_original] = image_data

    # Export cases with issues
    logger.info("Images with potential issues")
    image_check_stats(inventory_with_issues, logger)

    # Convert to Pandas DataFrame for exporting
    df = pd.DataFrame.from_dict(inventory_with_issues, orient='index')

    # re-arrange columns
    cols = df.columns.tolist()
    first_cols = [
        'season', 'site', 'roll', 'image_rank_in_roll',
        'capture', 'image_rank_in_capture',
        'recommended_action', 'recommended_action_reason',
        'manual_override_action', 'manual_override_reason',
        'failed_checks_all',
        'image_path_original_rel']
    cols_rearranged = first_cols + [x for x in cols if x not in first_cols]
    df = df[cols_rearranged]

    # sort rows
    df.sort_values(by='image_name_new', inplace=True)

    # export
    df.to_csv(args['issues_csv'], index=False)

    # change permmissions to read/write for group
    os.chmod(args['issues_csv'], 0o660)

    # Export cases with issues
    logger.info("All Images")
    image_check_stats(inventory, logger)

    # Convert to Pandas DataFrame for exporting
    df = pd.DataFrame.from_dict(inventory, orient='index')

    # re-arrange columns
    cols = df.columns.tolist()
    first_cols = [
        'season', 'site', 'roll', 'image_rank_in_roll',
        'capture', 'image_rank_in_capture',
        'recommended_action', 'recommended_action_reason',
        'manual_override_action', 'manual_override_reason',
        'failed_checks_all',
        'image_path_original_rel']
    cols_rearranged = first_cols + [x for x in cols if x not in first_cols]
    df = df[cols_rearranged]

    # sort rows
    df.sort_values(by='image_name_new', inplace=True)

    # export
    df.to_csv(args['inventory_grouped'], index=False)

    # change permmissions to read/write for group
    os.chmod(args['inventory_grouped'], 0o660)

    # create plot for site/roll timelines
    if args['plot_timelines']:
        plot_file_name = 'site_roll_timelines.pdf'
        plot_file_path = os.path.join(
            os.path.dirname(args['inventory_grouped']), plot_file_name)
        plot_site_roll_timelines(
            df=df,
            output_path=plot_file_path,
            date_col='datetime',
            date_format=flags['time_formats']['output_datetime_format'])



# # create CSV to invalidate specific rolls
# header_to_invalidate = [
#     'site', 'season',
#     'from_image', 'to_image',
#     'from_date_time', 'to_date_time',
#     'invalidate_images',
#     'delete_images',
#     'comment']
