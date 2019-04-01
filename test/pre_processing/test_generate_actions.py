import unittest
import logging
from collections import OrderedDict

from pre_processing.group_inventory_into_captures import (
        calculate_time_deltas, flags, group_images_into_captures,
        update_inventory_with_capture_id, update_inventory_with_image_names,
        update_inventory_with_capture_data,
        update_time_checks_inventory)
from pre_processing.generate_actions import (
    generate_actions, check_action_is_valid, check_datetime_format)
from pre_processing.utils import read_image_inventory
from logger import setup_logger

setup_logger()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class GenerateActionsTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        file_inventory = './test/files/test_inventory.csv'
        file = './test/files/test_action_list.csv'
        self.flags = {
           'exif_data_timestamps': ['DateTime',
          'DateTimeOriginal',
          'EXIF:DateTime',
          'EXIF:DateTimeOriginal'],
         'exif_tag_groups_to_extract': ['EXIF', 'MakerNotes', 'Composite'],
         'exif_tags_to_exclude': ['EXIF:ThumbnailImage', 'MakerNotes:PreviewImage'],
         'general': {'capture_delta_seconds': 5},
         'image_check_parameters': {'all_black': {'percent': 0.8, 'thresh': 30},
          'all_white': {'percent': 0.8, 'thresh': 200},
          'captures_with_too_many_images': {'max_images': 3},
          'time_lapse_days': {'max_days': 30},
          'time_too_new': {'max_year': 2018},
          'time_too_old': {'min_year': 2012}},
         'image_checks': ['all_black',
          'all_white',
          'corrupt_file',
          'corrupt_exif',
          'empty_exif',
          'time_lapse',
          'time_too_new',
          'time_too_old',
          'captures_with_too_many_images'],
         'image_checks_basic': ['all_black',
          'all_white',
          'corrupt_file',
          'corrupt_exif',
          'empty_exif'],
         'image_checks_time': ['time_lapse',
          'time_too_new',
          'time_too_old',
          'captures_with_too_many_images'],
         'time_formats': {'exif_input_datetime_format': '%Y:%m:%d %H:%M:%S',
          'output_date_format': '%Y-%m-%d',
          'output_datetime_format': '%Y-%m-%d %H:%M:%S',
          'output_time_format': '%H:%M:%S'}}
        self.inventory = read_image_inventory(file_inventory)
        time_deltas = calculate_time_deltas(self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, time_deltas)
        image_to_capture = group_images_into_captures(self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        update_inventory_with_image_names(self.inventory)
        self.action_list = read_image_inventory(file, unique_id=None)
        self.captures = OrderedDict()
        for v in self.inventory.values():
            self.captures[v['image_name']] = v
        self.actions = generate_actions(self.action_list, self.captures, logger)

    def testTimechanges(self):
        self.assertEqual(
                self.actions['APN_S2_A1_R1_IMAG0001.JPG']['action_to_take'],
                'timechange')
        self.assertEqual(
                self.actions['APN_S2_A1_R1_IMAG0002.JPG']['action_to_take'],
                'timechange')
        self.assertEqual(
                self.actions['APN_S2_A1_R1_IMAG0003.JPG']['action_to_take'],
                'timechange')
        self.assertEqual(
                int(self.actions['APN_S2_A1_R1_IMAG0003.JPG']['action_shift_time_by_seconds']),
                int(86400))
        self.assertEqual(
                int(self.actions['APN_S2_A1_R2_IMAG0010.JPG']['action_shift_time_by_seconds']),
                int(-60))

    def testPrioritizactions(self):
        self.assertNotEqual(
                self.actions['APN_S2_A1_R2_IMAG0005.JPG']['action_to_take'],
                'timechange')
        self.assertEqual(
                self.actions['APN_S2_A1_R2_IMAG0011.JPG']['action_to_take'],
                'delete')

    def testRollSelection(self):
        self.assertEqual(
                self.actions['APN_S2_A1_R2_IMAG0001.JPG']['action_to_take'],
                'timechange')
        self.assertEqual(
                self.actions['APN_S2_A1_R2_IMAG0012.JPG']['action_to_take'],
                'delete')
        self.assertEqual(
                self.actions['APN_S2_A1_R2_IMAG0001.JPG']['action_to_take_reason'],
                'one_hour_too_late')
        self.assertEqual(
                self.actions['APN_S2_A1_R2_IMAG0012.JPG']['action_to_take_reason'],
                'test_delete')

    def testActionIsValid(self):
        test_wrong_action_if_datetime = {
         'action_to_take': 'ok',
         'datetime_current': '2000-01-01 00:00:00',
         'datetime_new': '2000-01-01 00:00:01'
         }
        with self.assertRaises(AssertionError):
            check_action_is_valid(test_wrong_action_if_datetime)
        test_correct_action_if_datetime = {
         'action_to_take': 'timechange',
         'datetime_current': '2000-01-01 00:00:00',
         'datetime_new': '2000-01-01 00:00:01'
         }
        check_action_is_valid(test_correct_action_if_datetime)
        test_invalid_action = {
         'action_to_take': 'dummy',
         'datetime_current': '',
         'datetime_new': ''
         }
        with self.assertRaises(ImportError):
            check_action_is_valid(test_invalid_action)

    def testTimeFormatIsValid(self):
        test_wrong_format = {
        'datetime_current': '2000-01-01 00:00:00 PM',
        'datetime_new': '2000-01-01 00:00:01 AM'}
        with self.assertRaises(ImportError):
            check_datetime_format(test_wrong_format, '%Y-%m-%d %H:%M:%S')
        test_correct_format = {
        'datetime_current': '2000-01-01 00:00:00',
        'datetime_new': '2000-01-01 00:00:01'}
        check_datetime_format(test_correct_format, '%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    unittest.main()




#file_inventory = './test/files/test_inventory.csv'
#file = './test/files/test_action_list.csv'
#
#inventory = read_image_inventory(file_inventory)
#time_deltas = calculate_time_deltas(inventory, flags)
#update_inventory_with_capture_data(inventory, time_deltas)
#image_to_capture = group_images_into_captures(inventory, flags)
#update_inventory_with_capture_data(inventory, image_to_capture)
#update_inventory_with_capture_id(inventory)
#update_inventory_with_image_names(inventory)
#
#captures = OrderedDict()
#for v in inventory.values():
#    captures[v['image_name']] = v
#
#action_list = read_image_inventory(file, unique_id=None)
#
#action_list[0]
#
#actions = generate_actions(action_list, captures, logger)
