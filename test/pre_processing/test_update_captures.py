import unittest
import logging
from collections import OrderedDict
from unittest.mock import patch

from pre_processing.group_inventory_into_captures import (
        calculate_time_deltas, group_images_into_captures,
        update_inventory_with_capture_id, update_inventory_with_image_names,
        update_inventory_with_capture_data,
        update_time_checks_inventory)
from pre_processing.generate_actions import generate_actions
from pre_processing.utils import read_image_inventory
from pre_processing.update_captures import select_valid_images
from pre_processing.actions import apply_action
from utils.utils import create_capture_id
from config.cfg import cfg_default as cfg

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


flags = cfg['pre_processing_flags']


class GenerateActionsTests(unittest.TestCase):
    """ Test Import from CSV """
    def setUp(self):
        # test files
        file_inventory = './test/files/test_inventory.csv'
        file = './test/files/test_action_list.csv'
        self.inventory = read_image_inventory(file_inventory)
        time_deltas = calculate_time_deltas(self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, time_deltas)
        image_to_capture = group_images_into_captures(
            self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        update_inventory_with_image_names(self.inventory)
        self.action_list = read_image_inventory(file, unique_id=None)
        self.captures = OrderedDict()
        for v in self.inventory.values():
            self.captures[v['image_name']] = v
        self.actions = generate_actions(
            self.action_list, self.captures)

        @patch('pre_processing.actions.os.remove')
        def mock_apply_action(image_data, action_dict, flags, mock_remove):
            apply_action(image_data, action_dict, flags)

        for action_obj in self.actions:
            mock_apply_action(self.captures[action_obj.image], action_obj, flags)

        self.captures_updated = select_valid_images(self.captures)

        # re-calculate time_deltas
        time_deltas = calculate_time_deltas(self.captures_updated, flags)
        update_inventory_with_capture_data(self.captures_updated, time_deltas)

        # update image to capture association
        image_to_capture = group_images_into_captures(
            self.captures_updated, flags)
        update_inventory_with_capture_data(
            self.captures_updated, image_to_capture)

        update_inventory_with_capture_id(self.captures_updated)

        update_time_checks_inventory(self.captures_updated, flags)

    def testNewCaptureOrderAfterTimeChanges(self):
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R1_IMAG0004.JPG']['capture'],
                1)
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R1_IMAG0001.JPG']['capture'],
                4)

    def testNoDeletedImagesInUpdatedCaptures(self):
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0011.JPG']
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0012.JPG']
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0013.JPG']

    def testInvalidImagesFlaggedInUpdatedCaptures(self):
        self.assertEqual(
            self.captures_updated['APN_S2_A1_R2_IMAG0006.JPG']['image_is_invalid'],
            '1'
        )

    def testStatusChanges(self):
        self.assertIn(
            'timechange',
            self.captures_updated['APN_S2_A1_R2_IMAG0008.JPG']['action_taken'],
        )
        self.assertIn(
            'timechange',
            self.captures_updated['APN_S2_A1_R1_IMAG0003.JPG']['action_taken'],
        )

    def testCaptureIdUpdated(self):
        for k, v in self.captures_updated.items():
            capture_id_expected = create_capture_id(
                v['season'], v['site'], v['roll'], v['capture'])
            self.assertEqual(capture_id_expected, v['capture_id'])

    def testCaptureIdNoGap(self):
        self.assertEqual(
            self.captures_updated['APN_S2_A1_R2_IMAG0014.JPG']['capture_id'],
            'APN_S2#A1#2#4')

if __name__ == '__main__':
    unittest.main()
