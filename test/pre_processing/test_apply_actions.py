""" Apply Actions Tests """
import unittest
import logging
from unittest.mock import patch

from pre_processing.actions import apply_action

from config.cfg import cfg_default as cfg


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

flags = cfg['pre_processing_flags']


class ApplyActionsTests(unittest.TestCase):
    """ Test Action Generation """

    def testNormalCase(self):
        image_data = {'image_name': '1.JPG', 'site': 'a'}
        action_dict = {
            'image': '1.JPG',
            'action': 'mark_no_upload',
            'reason': 'rhino',
            'shift_time_by_seconds': 0}
        apply_action(image_data, action_dict, flags)
        expected = {
                'image_name': '1.JPG',
                'site': 'a',
                'image_no_upload': '1',
                'image_was_deleted': '',
                'image_datetime_uncertain': '',
                'image_is_invalid': '',
                'action_taken': 'mark_no_upload',
                'action_taken_reason': 'rhino'}
        self.assertEqual(image_data, expected)

    def testTimeChange(self):
        image_data = {
            'image_name': '1.JPG', 'site': 'a',
            'datetime': '2000-01-01 00:00:00'}
        action_dict = {
            'image': '1.JPG',
            'action': 'timechange',
            'reason': 'camera clock off',
            'shift_time_by_seconds': 60}
        apply_action(image_data, action_dict, flags)
        expected = {
                'image_name': '1.JPG',
                'site': 'a',
                'image_no_upload': '',
                'image_was_deleted': '',
                'image_datetime_uncertain': '',
                'image_is_invalid': '',
                'datetime': '2000-01-01 00:01:00',
                'action_taken': 'timechange',
                'action_taken_reason': 'camera clock off'}
        self.assertEqual(image_data, expected)

    def testMultipleFlags(self):
        image_data = {'image_name': '1.JPG', 'site': 'a'}
        action_dict = {
            'image': '1.JPG',
            'action': 'invalidate',
            'reason': 'all_black',
            'shift_time_by_seconds': 0}
        apply_action(image_data, action_dict, flags)
        expected = {
                'image_name': '1.JPG',
                'site': 'a',
                'image_no_upload': '1',
                'image_was_deleted': '',
                'image_datetime_uncertain': '',
                'image_is_invalid': '1',
                'action_taken': 'invalidate',
                'action_taken_reason': 'all_black'}
        self.assertEqual(image_data, expected)

    def testMultipleActions(self):
        image_data = {'image_name': '1.JPG', 'site': 'a'}
        action_dict1 = {
            'image': '1.JPG',
            'action': 'invalidate',
            'reason': 'all_black',
            'shift_time_by_seconds': 0}
        action_dict2 = {
            'image': '1.JPG',
            'action': 'mark_datetime_uncertain',
            'reason': 'unclear datetime',
            'shift_time_by_seconds': 0}
        apply_action(image_data, action_dict1, flags)
        apply_action(image_data, action_dict2, flags)
        expected = {
                'image_name': '1.JPG',
                'site': 'a',
                'image_no_upload': '1',
                'image_was_deleted': '',
                'image_datetime_uncertain': '1',
                'image_is_invalid': '1',
                'action_taken': 'invalidate#mark_datetime_uncertain',
                'action_taken_reason': 'all_black#unclear datetime'}
        self.assertEqual(image_data, expected)

    def testMultipleIdenticalActions(self):
        image_data = {'image_name': '1.JPG', 'site': 'a'}
        action_dict1 = {
            'image': '1.JPG',
            'action': 'invalidate',
            'reason': 'all_black',
            'shift_time_by_seconds': 0}
        action_dict2 = {
            'image': '1.JPG',
            'action': 'invalidate',
            'reason': 'human',
            'shift_time_by_seconds': 0}
        apply_action(image_data, action_dict1, flags)
        apply_action(image_data, action_dict2, flags)
        expected = {
                'image_name': '1.JPG',
                'site': 'a',
                'image_no_upload': '1',
                'image_was_deleted': '',
                'image_datetime_uncertain': '',
                'image_is_invalid': '1',
                'action_taken': 'invalidate#invalidate',
                'action_taken_reason': 'all_black#human'}
        self.assertEqual(image_data, expected)

    def testDeletion(self):
        image_data = {'image_name': '1.JPG', 'site': 'a', 'image_path': '/d/dummy.txt'}
        action_dict = {
            'image': '1.JPG',
            'action': 'delete',
            'reason': 'corrupt',
            'shift_time_by_seconds': 0}

        @patch('pre_processing.actions.os.remove')
        def mock_apply_action(image_data, action_dict, flags, mock_remove):
            apply_action(image_data, action_dict, flags)

        mock_apply_action(image_data, action_dict, flags)
        expected = {
                'image_name': '1.JPG',
                'image_path': '/d/dummy.txt',
                'site': 'a',
                'image_no_upload': '1',
                'image_was_deleted': '1',
                'image_datetime_uncertain': '',
                'image_is_invalid': '',
                'action_taken': 'delete',
                'action_taken_reason': 'corrupt'}
        self.assertEqual(image_data, expected)
