import unittest
import logging
from collections import OrderedDict

from pre_processing.group_inventory_into_captures import (
        calculate_time_deltas, group_images_into_captures,
        update_inventory_with_capture_id, update_inventory_with_image_names,
        update_inventory_with_capture_data,
        update_time_checks_inventory)
from pre_processing.generate_actions import generate_actions
from pre_processing.utils import read_image_inventory
from pre_processing.update_captures import select_valid_images
from pre_processing.apply_actions import apply_actions
from logger import setup_logger


class GenerateActionsTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        # test files
        file_inventory = './test/files/test_inventory.csv'
        file = './test/files/test_action_list.csv'
        # fix flags
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
        setup_logger()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)
        self.inventory = read_image_inventory(file_inventory)
        time_deltas = calculate_time_deltas(self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, time_deltas)
        image_to_capture = group_images_into_captures(
            self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        update_inventory_with_image_names(self.inventory)
        self.action_list = read_image_inventory(file, unique_id=None)
        self.captures = OrderedDict()
        for v in self.inventory.values():
            self.captures[v['image_name']] = v
        self.actions = generate_actions(
            self.action_list, self.captures, self.logger)
        self.actions_no_deletions = OrderedDict()

        for img, action in self.actions.items():
            self.actions_no_deletions[img] = action
            if action['action_to_take'] == 'delete':
                self.actions_no_deletions[img]['action_to_take'] = 'invalidate'

        apply_actions(self.actions_no_deletions, self.captures, self.logger)

        self.captures_updated = select_valid_images(self.captures)

        # re-calculate time_deltas
        time_deltas = calculate_time_deltas(self.captures_updated, self.flags)
        update_inventory_with_capture_data(self.captures_updated, time_deltas)

        # update image to capture association
        image_to_capture = group_images_into_captures(
            self.captures_updated, self.flags)
        update_inventory_with_capture_data(
            self.captures_updated, image_to_capture)

        update_inventory_with_capture_id(self.captures_updated)

        update_time_checks_inventory(self.captures_updated, self.flags)

    def testNewCaptureOrderAfterTimeChanges(self):
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R1_IMAG0004.JPG']['capture'],
                1)
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R1_IMAG0001.JPG']['capture'],
                4)

    def testNoInvalidImagesInUpdatedCaptures(self):
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0011.JPG']
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0006.JPG']


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
#
#actions = generate_actions(action_list, captures, logger)
#
#actions_no_deletions = OrderedDict()
#
#for img, action in actions.items():
#    actions_no_deletions[img] = action
#    if action['action_to_take'] == 'delete':
#        actions_no_deletions[img]['action_to_take'] = 'invalidate'
#
#
#apply_actions(actions_no_deletions, captures, logger)
#
#captures_updated = select_valid_images(captures)
#
## re-calculate time_deltas
#time_deltas = calculate_time_deltas(captures_updated, flags)
#update_inventory_with_capture_data(captures_updated, time_deltas)
#
## update image to capture association
#image_to_capture = group_images_into_captures(captures_updated, flags)
#update_inventory_with_capture_data(captures_updated, image_to_capture)
#
#update_inventory_with_capture_id(captures_updated)
#
#update_time_checks_inventory(captures_updated, flags)
#
#
#
## new first capture
#captures_updated['APN_S2_A1_R1_IMAG0004.JPG']
#
## now fourth capture
#captures_updated['APN_S2_A1_R1_IMAG0001.JPG']
#
#
## search for invalid
#captures_updated['APN_S2_A1_R2_IMAG0011.JPG']
#captures_updated['APN_S2_A1_R2_IMAG0006.JPG']
#
#
#captures_updated['APN_S2_A1_R2_IMAG0004.JPG']
