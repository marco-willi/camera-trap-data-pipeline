import unittest
import os
from pre_processing.group_inventory_into_captures import (
        calculate_time_deltas, group_images_into_captures,
        update_inventory_with_capture_id, update_inventory_with_image_names,
        update_inventory_with_capture_data,
        create_new_image_path_rel)
from pre_processing.utils import read_image_inventory

from config.cfg import cfg_default as cfg

flags = cfg['pre_processing_flags']


class GroupCapturesTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        file = './test/files/test_inventory.csv'
        self.inventory = read_image_inventory(file)
        time_deltas = calculate_time_deltas(self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, time_deltas)

    def testGroupingIntoCaptures(self):
        image_to_capture = group_images_into_captures(
            self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        for k, v in self.inventory.items():
            self.assertEqual('{}'.format(v['capture_expected']),
                             '{}'.format(v['capture']))

    def testCaptureIDGeneration(self):
        image_to_capture = group_images_into_captures(
            self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        for k, v in self.inventory.items():
            self.assertEqual(v['capture_id'],
                             '#'.join([v['season'], v['site'], v['roll'],
                                       str(v['capture'])]))

    def testImageNameGeneration(self):
        image_to_capture = group_images_into_captures(
            self.inventory, flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        update_inventory_with_image_names(self.inventory)
        for k, v in self.inventory.items():
            if int(v['image_rank_in_roll_expected']) < 10:
                self.assertEqual(
                        v['image_name'],
                        v['image_name_new_expected'])

    def testImageNameGenerationRel(self):
        """ Test Relative Image Name Generation """
        # TEST CASE 1
        input1 = \
            {'image_path_original_rel': os.path.sep.join(
                ['TEST_S1', 'A01', 'R1', 'IMG01.JPG']),
             'season': 'TEST_S1',
             'site': 'A01',
             'roll': '1',
             'image_rank_in_roll': 2,
             'image_name_original': 'IMG01.JPG'}
        expected1 = os.path.sep.join(
            ['TEST_S1', 'A01', 'R1', 'TEST_S1_A01_R1_IMAG0002.JPG'])
        actual1 = create_new_image_path_rel(input1)
        # TEST CASE 2
        input2 = \
            {'image_path_original_rel': os.path.sep.join(
                ['my_images', 'TEST_S1', 'A01', 'R1', 'IMG01.JPG']),
             'season': 'TEST_S1',
             'site': 'A01',
             'roll': '1',
             'image_rank_in_roll': 3,
             'image_name_original': 'IMG01.JPG'}
        expected2 = os.path.sep.join(
            ['my_images', 'TEST_S1', 'A01', 'R1', 'TEST_S1_A01_R1_IMAG0003.JPG'])
        actual2 = create_new_image_path_rel(input2)
        self.assertEqual(expected1, actual1)
        self.assertEqual(expected2, actual2)


if __name__ == '__main__':
    unittest.main()
