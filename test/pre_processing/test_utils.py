import unittest
from datetime import datetime

from pre_processing.utils import (
    convert_datetime_utc_to_timezone, convert_ctime_to_datetime)

from config.cfg import cfg


flags = cfg['pre_processing_flags']


class PreProcessingUtilsTests(unittest.TestCase):
    """ Test Import from CSV """

    def testDatetimeTimezoneConversion(self):
        # Example from an actual camera trap image
        input = "2016-02-13 03:26:07"
        expected = "2016-02-13 05:26:07"
        target_tz = 'Africa/Maputo'
        input_datetime = datetime.strptime(input, "%Y-%m-%d %H:%M:%S")
        actual_datetime = convert_datetime_utc_to_timezone(
            input_datetime, target_tz)
        actual = actual_datetime.strftime("%Y-%m-%d %H:%M:%S")
        self.assertEqual(actual, expected)

    def testDatetimeTimezoneConversionFullExample(self):
        img_creation_date = 1455333968.0
        img_creation_date_dt = \
            convert_ctime_to_datetime(img_creation_date)
        target_tz = 'Africa/Johannesburg'
        if target_tz != '':
            img_creation_date_local = \
                convert_datetime_utc_to_timezone(
                    img_creation_date_dt, target_tz)
        else:
            img_creation_date_local = img_creation_date_dt
        actual = img_creation_date_local.strftime(
            flags['time_formats']['output_datetime_format'])
        # rounding errors possible
        expected1 = "2016-02-13 05:26:07"
        expected2 = "2016-02-13 05:26:08"
        self.assertIn(actual, [expected1, expected2])
