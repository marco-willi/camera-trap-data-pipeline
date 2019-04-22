"""" Utils for Report Creations """
import logging
from datetime import datetime
from collections import OrderedDict

from config.cfg import cfg

logger = logging.getLogger(__name__)


flags_global = cfg['global_processing_flags']
flags_report = cfg['report_flags']


def _get_datetime_obj(date_str):
    """ Get DateTime object from a str with unknown format """
    try:
        time_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
    except ValueError:
        try:
            time_obj = datetime.strptime(
                date_str,
                '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                time_obj = datetime.strptime(
                    date_str,
                    '%Y-%m-%d %H:%M:%SZ')
            except ValueError:
                logger.debug(
                    "could not convert {} to datetime".format(date_str))
    return time_obj


def _extract_datetime(image_record):
    """ Extract Date and Time from Image Record in Cleaned Season File
        - handle different cases
    """
    res = {'date': '', 'time': ''}
    # handle legacy case
    if 'timestamp' in image_record:
        try:
            time_obj = _get_datetime_obj(image_record['timestamp'])
            res['date'] = time_obj.strftime("%Y-%m-%d")
            res['time'] = time_obj.strftime("%H:%M:%S")
        except:
            pass
    # handle standard case
    elif all([x in image_record for x in ['date', 'time']]):
        res['date'] = image_record['date']
        res['time'] = image_record['time']
    # handle datetime only case
    elif 'datetime' in image_record:
        try:
            time_obj = _get_datetime_obj(image_record['datetime'])
            res['date'] = time_obj.strftime("%Y-%m-%d")
            res['time'] = time_obj.strftime("%H:%M:%S")
        except:
            pass
    # handle file creation date only
    elif 'datetime_file_creation' in image_record:
        try:
            time_obj = _get_datetime_obj(image_record['datetime_file_creation'])
            res['date'] = time_obj.strftime("%Y-%m-%d")
            res['time'] = time_obj.strftime("%H:%M:%S")
        except:
            pass
    if (res['date'] == '') or (res['time'] == ''):
        raise ValueError("could not extract date/time from image record")
    return res


def exclude_cols(cols, not_in):
    """ Remove any element of 'cols' that has elements in 'not_in' that
        start with elements in 'cols'
        Example: ['abc', 'def'] and ['ab'] -> ['def']
    """
    return [c for c in cols if not any([c.startswith(n) for n in not_in])]


def create_season_dict(season_data_df):
    """ Create Dict of Season Data """
    season_dict = OrderedDict()
    season_dict_input = season_data_df.to_dict(orient='index')
    for _id, image_record in season_dict_input.items():
        try:
            capture_id = image_record['capture_id']
        except:
            capture_id = '#'.join([
                image_record['season'],
                image_record['site'],
                image_record['roll'],
                image_record['capture']])
        if capture_id not in season_dict:
            try:
                date_time = _extract_datetime(image_record)
            except:
                date_time = {'date': '', 'time': ''}
                logger.info("Failed to extract date/time for {}".format(
                    capture_id))
                logger.debug("Full record: {}".format(image_record))
            season_dict[capture_id] = {
                'capture_id': capture_id,
                'season': image_record['season'],
                'site': image_record['site'],
                'roll': image_record['roll'],
                'capture': image_record['capture'],
                'capture_date_local': date_time['date'],
                'capture_time_local': date_time['time']}
    return season_dict
