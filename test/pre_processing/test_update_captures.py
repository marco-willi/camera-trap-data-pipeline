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
from utils.logger import setup_logger
from config.cfg import cfg_default as cfg

flags = cfg['pre_processing_flags']


class GenerateActionsTests(unittest.TestCase):
    """ Test Import from CSV """
    def setUp(self):
        # test files
        file_inventory = './test/files/test_inventory.csv'
        file = './test/files/test_action_list.csv'
        setup_logger()
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.ERROR)
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
            self.action_list, self.captures, self.logger)
        self.actions_no_deletions = OrderedDict()

        for img, action in self.actions.items():
            self.actions_no_deletions[img] = action
            if action['action_to_take'] == 'delete':
                self.actions_no_deletions[img]['action_to_take'] = 'invalidate'

        apply_actions(self.actions_no_deletions, self.captures, self.logger)

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

    def testNoInvalidImagesInUpdatedCaptures(self):
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0011.JPG']
        with self.assertRaises(KeyError):
            self.captures_updated['APN_S2_A1_R2_IMAG0006.JPG']

    def testStatusChanges(self):
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R2_IMAG0008.JPG']['status'],
                'ok')
        self.assertEqual(
                self.captures_updated['APN_S2_A1_R1_IMAG0003.JPG']['status'],
                'ok')


if __name__ == '__main__':
    unittest.main()
