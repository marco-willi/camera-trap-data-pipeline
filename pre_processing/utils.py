import os
import platform
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt

from collections import defaultdict, Counter


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
                    check, image_data['image_path_original']))
        # total number with exclusion reasons
        image_check_stats['exclude_image'].update({
            image_data['exclude_image']})
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
            if int(check_result) == 1:
                logger.info(
                    "Failed {:35}: -- count: {:6}/{:6} ({:.2f}%)".format(
                     check, count, n_tot, 100*(count / n_tot)))
    total = sum([x for x in season_site_roll_stats.values()])
    for season_site_roll, count in season_site_roll_stats.most_common():
        logger.info(
            "Season/Site/Roll: {:35} -- counts: {:10} / {} ({:.2f} %)".format(
             season_site_roll, count, total, 100*count/total))
    logger.info("Found total {} images".format(n_tot))


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

    date_time_obj = \
        [datetime.strptime(x, date_format) for x in df[date_col].values]

    df['date_time'] = date_time_obj

    roll_site_group = \
        df.groupby(by=['site', 'roll', 'date_time']).size().unstack(
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



