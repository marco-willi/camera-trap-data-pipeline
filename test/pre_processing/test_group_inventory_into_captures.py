import unittest
from pre_processing.group_inventory_into_captures import (
        calculate_time_deltas, group_images_into_captures,
        update_inventory_with_capture_id, update_inventory_with_image_names,
        update_inventory_with_capture_data)
from pre_processing.utils import read_image_inventory


class GroupCapturesTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        file = './test/files/test_inventory.csv'
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
        self.inventory = read_image_inventory(file)
        time_deltas = calculate_time_deltas(self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, time_deltas)

    def testGroupingIntoCaptures(self):
        image_to_capture = group_images_into_captures(
            self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        for k, v in self.inventory.items():
            self.assertEqual('{}'.format(v['capture_expected']),
                             '{}'.format(v['capture']))

    def testCaptureIDGeneration(self):
        image_to_capture = group_images_into_captures(
            self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        for k, v in self.inventory.items():
            self.assertEqual(v['capture_id'],
                             '#'.join([v['season'], v['site'], v['roll'],
                                       str(v['capture'])]))

    def testImageNameGeneration(self):
        image_to_capture = group_images_into_captures(
            self.inventory, self.flags)
        update_inventory_with_capture_data(self.inventory, image_to_capture)
        update_inventory_with_capture_id(self.inventory)
        update_inventory_with_image_names(self.inventory)
        for k, v in self.inventory.items():
            if int(v['image_rank_in_roll_expected']) < 10:
                self.assertEqual(
                        v['image_name'],
                        v['image_name_new_expected'])

if __name__ == '__main__':
    unittest.main()


#file = './test/files/test_inventory.csv'
#inventory = read_image_inventory(file)
#time_deltas = calculate_time_deltas(inventory, flags)
#update_inventory_with_capture_data(inventory, time_deltas)
#update_inventory_with_capture_id(self.inventory)
#
