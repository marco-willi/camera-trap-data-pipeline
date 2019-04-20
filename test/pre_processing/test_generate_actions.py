""" Test Generation of Action Items """
import unittest
import logging
from collections import OrderedDict

from pre_processing.generate_actions import (
    generate_actions, check_action_is_valid,
    _check_datetime_format)
from config.cfg import cfg_default as cfg


logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)


flags = cfg['pre_processing_flags']


class GenerateActionsTests(unittest.TestCase):
    """ Test Action Generation """
    def setUp(self):
        self.dummy_action = {
              'image_name': '1.JPG',
              'action_roll': '',
              'action_site': '',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '1.JPG',
              'action_to_image': '1.JPG',
              'action_to_take': 'invalidate',
              'action_to_take_reason': 'lala'}

    def testSimpleAction(self):
        """ Test Normal Action """
        captures = {
                '1.JPG': {'site': 'a'}}
        action_list = {
          0: {
              'action_roll': '',
              'action_site': 'a',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '',
              'action_to_image': '',
              'action_to_take': 'mark_no_upload',
              'action_to_take_reason': 'lala'}}

        actions = generate_actions(action_list, captures)
        self.assertEqual(actions[0].action, 'mark_no_upload')

    def testInvalidAction(self):
        """ Invalid Action """
        captures = {
                '1.JPG': {'site': 'a'}}
        action_list = {
          0: {
              'action_roll': '1',
              'action_site': 'a',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '',
              'action_to_image': '',
              'action_to_take': 'dummy',
              'action_to_take_reason': 'lala'}}

        with self.assertRaises(ImportError):
            generate_actions(action_list, captures)

    def testMultipleActions(self):
        """ Multiple Actions Possible """
        captures = {
                '1.JPG': {'site': 'a'},
                '2.JPG': {'site': 'a'}}
        action_list = {
          0: self.dummy_action,
          1: self.dummy_action}
        actions = generate_actions(action_list, captures)
        self.assertEqual(len(actions), 2)
        self.assertEqual([x for x in actions[0]],
                         [x for x in actions[1]])

    def testMultipleTimechanges(self):
        """ RaiseError for Multiple Timechanges """
        captures = {
                '1.JPG': {'site': 'a'},
                '2.JPG': {'site': 'a'}}
        action = {k: v for k, v in self.dummy_action.items()}
        action['action_to_take'] = 'timechange'
        action['datetime_current'] = '2000-01-01 00:00:00'
        action['datetime_new'] = '2000-01-01 00:01:00'
        action_list = {
          0: action,
          1: action}
        with self.assertRaises(ValueError):
            generate_actions(action_list, captures)

    def testTimechangePositive(self):
        captures = {
            '1.JPG': {'site': 'a'}}
        action = {k: v for k, v in self.dummy_action.items()}
        action['action_to_take'] = 'timechange'
        action['datetime_current'] = '2017-10-26 10:38:31'
        action['datetime_new'] = '2017-10-27 10:38:31'
        action_list = {
          0: action}
        actions = generate_actions(action_list, captures)
        self.assertEqual(actions[0].shift_time_by_seconds, int(86400))

    def testTimechangeNegative(self):
        captures = {
            '1.JPG': {'site': 'a'}}
        action = {k: v for k, v in self.dummy_action.items()}
        action['action_to_take'] = 'timechange'
        action['datetime_current'] = '2000-01-01 00:01:00'
        action['datetime_new'] = '2000-01-01 00:00:00'
        action_list = {
          0: action}
        actions = generate_actions(action_list, captures)
        self.assertEqual(actions[0].shift_time_by_seconds, int(-60))

    def testRollSelection(self):
        captures = {
            '1.JPG': {'site': 'a', 'roll': '1'},
            '2.JPG': {'site': 'a', 'roll': '2'},
            '3.JPG': {'site': 'a', 'roll': '1'},
            '4.JPG': {'site': 'b', 'roll': '1'}}
        action_list = {
          0: {
              'action_roll': '1',
              'action_site': 'a',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '',
              'action_to_image': '',
              'action_to_take': 'delete',
              'action_to_take_reason': 'lala'}}
        actions = generate_actions(action_list, captures)
        expected_in = ['1.JPG', '3.JPG']
        actual = [a.image for a in actions]
        self.assertEqual(set(actual), set(expected_in))

    def testSiteSelection(self):
        captures = {
            '1.JPG': {'site': 'a', 'roll': '1'},
            '2.JPG': {'site': 'a', 'roll': '2'},
            '3.JPG': {'site': 'a', 'roll': '1'},
            '4.JPG': {'site': 'b', 'roll': '1'}}
        action_list = {
          0: {
              'action_roll': '',
              'action_site': 'a',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '',
              'action_to_image': '',
              'action_to_take': 'delete',
              'action_to_take_reason': 'lala'}}
        actions = generate_actions(action_list, captures)
        expected_in = ['1.JPG', '2.JPG', '3.JPG']
        actual = [a.image for a in actions]
        self.assertEqual(set(actual), set(expected_in))

    def testImageRangeSelection(self):
        captures = OrderedDict([
            ('1.JPG', {'site': 'a', 'roll': '1'}),
            ('3.JPG', {'site': 'a', 'roll': '2'}),
            ('5.JPG', {'site': 'a', 'roll': '1'}),
            ('4.JPG', {'site': 'b', 'roll': '1'}),
            ('6.JPG', {'site': 'b', 'roll': '1'})])
        action_list = {
          0: {
              'action_roll': '',
              'action_site': '',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '3.JPG',
              'action_to_image': '4.JPG',
              'action_to_take': 'delete',
              'action_to_take_reason': 'lala'}}
        actions = generate_actions(action_list, captures)
        expected_in = ['3.JPG', '5.JPG', '4.JPG']
        actual = [a.image for a in actions]
        self.assertEqual(set(actual), set(expected_in))

    def testImageRangeAndSiteSelectionIsInvalid(self):
        captures = OrderedDict([
            ('1.JPG', {'site': 'a', 'roll': '1'}),
            ('3.JPG', {'site': 'a', 'roll': '2'}),
            ('4.JPG', {'site': 'b', 'roll': '1'}),
            ('6.JPG', {'site': 'b', 'roll': '1'})])
        action_list = {
          0: {
              'action_roll': '',
              'action_site': 'a',
              'datetime_current': '',
              'datetime_new': '',
              'action_from_image': '3.JPG',
              'action_to_image': '4.JPG',
              'action_to_take': 'delete',
              'action_to_take_reason': 'lala'}}
        with self.assertRaises(ImportError):
            generate_actions(action_list, captures)

    def testActionIsValid(self):
        test_wrong_action_if_datetime = {
         'action_to_take': 'ok',
         'action_to_take_reason': 'dummy',
         'action_roll': '',
         'action_site': 'dummy',
         'action_from_image': '',
         'action_to_image': '',
         'datetime_current': '2000-01-01 00:00:00',
         'datetime_new': '2000-01-01 00:00:01'
         }
        with self.assertRaises(AssertionError):
            check_action_is_valid(test_wrong_action_if_datetime, flags)
        test_correct_action_if_datetime = {
         'action_to_take': 'timechange',
         'action_to_take_reason': 'dummy',
         'action_roll': '',
         'action_site': 'dummy',
         'action_from_image': '',
         'action_to_image': '',
         'datetime_current': '2000-01-01 00:00:00',
         'datetime_new': '2000-01-01 00:00:01'
         }
        check_action_is_valid(test_correct_action_if_datetime, flags)
        test_invalid_action = {
         'action_to_take': 'dummy',
         'action_to_take_reason': 'dummy',
         'action_roll': '',
         'action_site': 'dummy',
         'action_from_image': '',
         'action_to_image': '',
         'datetime_current': '',
         'datetime_new': ''
         }
        with self.assertRaises(ImportError):
            check_action_is_valid(test_invalid_action, flags)

    def testTimeFormatIsValid(self):
        test_wrong_format = {
            'datetime_current': '2000-01-01 00:00:00 PM',
            'datetime_new': '2000-01-01 00:00:01 AM'}
        with self.assertRaises(ImportError):
            _check_datetime_format(test_wrong_format, '%Y-%m-%d %H:%M:%S')
        test_correct_format = {
            'datetime_current': '2000-01-01 00:00:00',
            'datetime_new': '2000-01-01 00:00:01'}
        _check_datetime_format(test_correct_format, '%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    unittest.main()
