import os
import platform
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import csv

from collections import defaultdict, Counter, OrderedDict
from utils.utils import set_file_permission

plt.switch_backend('agg')


def file_creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288/1709587 for explanation.
    https://stackoverflow.com/questions/237079/how-to-get-file-creation-modification-date-times-in-python
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime


def image_check_stats(image_inventory, logger):
    """ Create and print image stats """
    image_check_stats = defaultdict(Counter)
    season_site_roll_stats = Counter()
    for img_no, (image_path, image_data) in enumerate(image_inventory.items()):
        # Get image checks
        for check, check_result in image_data.items():
            if not check.startswith('image_check__'):
                continue
            image_check_stats[check].update({check_result})
            # if check not passed log
            if check_result == 1:
                logger.info("Check {} Failed for image {}".format(
                    check, image_path))
        # site roll stats
        season = image_data['season']
        site = image_data['site']
        roll = image_data['roll']
        season_roll_site_key = '#'.join([season, site, roll])
        season_site_roll_stats.update({season_roll_site_key})
    # Print Check Results
    for check, check_results in image_check_stats.items():
        n_tot = sum([x for x in check_results.values()])
        for check_result, count in check_results.items():
            if float(check_result) == 1:
                logger.info(
                    "Failed {:35}: -- count: {:6}/{:6} ({:.2f}%)".format(
                     check, count, n_tot, 100*(count / n_tot)))
    total = sum([x for x in season_site_roll_stats.values()])
    for season_site_roll, count in season_site_roll_stats.most_common():
        logger.info(
            "Season/Site/Roll: {:35} -- counts: {:10} / {} ({:.2f} %)".format(
             season_site_roll, count, total, 100*count/total))
    logger.info("Found total {} images".format(len(image_inventory.keys())))


def p_pixels_above_threshold(pixel_data, pixel_threshold):
    """ Calculate share of pixels above threshold """
    n_pixels_total = np.multiply(pixel_data.shape[0], pixel_data.shape[1])
    pixels_2D = np.sum(pixel_data > pixel_threshold, axis=(2))
    n_pixels_above_threshold = np.sum(pixels_2D == 3)
    p_pixels_above_threshold = n_pixels_above_threshold / n_pixels_total
    return p_pixels_above_threshold


def p_pixels_below_threshold(pixel_data, pixel_threshold):
    """ Calculate share of pixels below threshold """
    n_pixels_total = np.multiply(pixel_data.shape[0], pixel_data.shape[1])
    pixels_2D = np.sum(pixel_data < pixel_threshold, axis=(2))
    n_pixels_below_threshold = np.sum(pixels_2D == 3)
    p_pixels_below_threshold = n_pixels_below_threshold / n_pixels_total
    return p_pixels_below_threshold


def plot_site_roll_timelines(
        df,
        output_path,
        date_col='datetime',
        date_format='%Y-%m-%d %H:%M:%S'):
    """ Plot timelines for site_roll combination """
    df_copy = df.loc[df[date_col] != ''].copy()
    date_time_obj = \
        [datetime.strptime(x, date_format) for x in df_copy[date_col].values]
    df_copy['date_time'] = date_time_obj
    roll_site_group = \
        df_copy.groupby(by=['site', 'roll', 'date_time']).size().unstack(
                level=[0, 1], fill_value=0)
    # Aggregate per Day - count number of instances
    roll_site_group.index = roll_site_group.index.to_period('D')
    roll_site_group = roll_site_group.groupby(roll_site_group.index).sum()
    # Plot
    n_subplots = roll_site_group.shape[1]
    fig, ax = plt.subplots(figsize=(8, n_subplots*2), sharex=True)
    plt.subplots_adjust(bottom=0.5, top=1.5, hspace=1)
    plt.tight_layout()
    roll_site_group.plot(subplots=True, ax=ax)
    fig.savefig(output_path)
    set_file_permission(output_path)


def read_image_inventory_old(path, unique_id='image_path_original'):
    """ Import image inventory into dictionary """
    inventory = OrderedDict()
    with open(path, "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Read {:,} records".format(line_no))
            image_path_original = \
                line[row_name_to_id_mapper[unique_id]]
            inventory[image_path_original] = {
                k: line[v] for k, v in row_name_to_id_mapper.items()}
    return inventory


def read_image_inventory(path, unique_id='image_path_original'):
    df = pd.read_csv(path, dtype='str')
    df.fillna('', inplace=True)
    inventory = df.to_dict('index', into=OrderedDict)
    inventory_with_index_as_col = OrderedDict()
    for i, (_id, data) in enumerate(inventory.items()):
        if unique_id is not None:
            inventory_with_index_as_col[data[unique_id]] = data
        else:
            inventory_with_index_as_col[i] = data
    return inventory_with_index_as_col


def export_inventory_to_csv(
        inventory,
        output_path,
        first_cols=['season', 'site', 'roll', 'image_rank_in_roll',
                    'capture', 'image_rank_in_capture'],
        return_df=False):
    """ Export Inventory to CSV
        inventory: dict
        output_path: path to a file that is being created
    """
    df = pd.DataFrame.from_dict(inventory, orient='index')

    # re-arrange columns
    cols = df.columns.tolist()

    first_cols = [x for x in first_cols if x in cols]

    cols_rearranged = first_cols + [x for x in cols if x not in first_cols]
    df = df[cols_rearranged]

    # sort rows
    df.sort_values(by=first_cols, inplace=True)

    # export
    df.to_csv(output_path, index=False)

    # change permmissions to read/write for group
    set_file_permission(output_path)

    if return_df:
        return df


def update_time_checks(image_data, flags):
    checks = flags['image_check_parameters']
    # perform time checks
    time_checks = {
        'image_check__{}'.format(x): 0
        for x in flags['image_checks_time']}
    # check for timelapse
    if 'image_check__time_lapse' in time_checks:
        max_days = \
            checks['time_lapse_days']['max_days']
        if float(image_data['days_to_next_image_taken']) > max_days:
            time_checks['image_check__time_lapse'] = 1
    # check for too_old / too new
    date_format = flags['time_formats']['output_date_format']
    date_obj = datetime.strptime(image_data['date'], date_format)
    year_num = int(date_obj.strftime('%Y'))
    if 'image_check__time_too_old' in time_checks:
        min_year = \
            checks['time_too_old']['min_year']
        if not year_num >= min_year:
            time_checks['image_check__time_too_old'] = 1
    if 'image_check__time_too_new' in time_checks:
        max_year = \
            checks['time_too_new']['max_year']
        if not year_num <= max_year:
            time_checks['image_check__time_too_new'] = 1
    # check for captures with too many images
    if 'image_check__captures_with_too_many_images' in time_checks:
        max_imgs = \
            checks['captures_with_too_many_images']['max_images']
        if float(image_data['image_rank_in_capture']) > float(max_imgs):
            time_checks['image_check__captures_with_too_many_images'] = 1
    image_data.update(time_checks)
