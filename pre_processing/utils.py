import os
import platform

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
        for check, check_result in image_data['image_checks'].items():
            image_check_stats[check].update({check_result})
            # if check not passed log
            if check_result == 1:
                logger.info("Check {} Failed for image {}".format(
                    check, image_data['image_name_original']))
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
            logger.info("Check for: {:15}: result: {} -- count: {:6} ({:.2f}%)".format(
                check, check_result, count, 100*(count / n_tot)
            ))
    total = sum([x for x in season_site_roll_stats.values()])
    for season_site_roll, count in season_site_roll_stats.most_common():
        logger.info("Season/Site/Roll: {:10} -- counts: {:10} / {} ({:.2f} %)".format(
            season_site_roll, count, total, 100*count/total))
    logger.info("Found total {} images".format(n_tot))



def image_check_stats2(image_inventory, logger):
    """ Create and print image stats """
    image_check_stats = defaultdict(Counter)
    season_site_roll_stats = Counter()
    for img_no, (image_path, image_data) in enumerate(image_inventory.items()):
        # Get image checks
        for check, check_result in image_data.items():
            if not (check.startswith('image_check__') or (check.startswith('image_checks__'))):
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
                logger.info("Failed {:35}: -- count: {:6}/{:6} ({:.2f}%)".format(
                    check, count, n_tot, 100*(count / n_tot)
                ))
    total = sum([x for x in season_site_roll_stats.values()])
    for season_site_roll, count in season_site_roll_stats.most_common():
        logger.info("Season/Site/Roll: {:35} -- counts: {:10} / {} ({:.2f} %)".format(
            season_site_roll, count, total, 100*count/total))
    logger.info("Found total {} images".format(n_tot))
