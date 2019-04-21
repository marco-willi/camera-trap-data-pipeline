""" Test Input Structure """
import unittest

from pre_processing.check_input_structure import (
    is_ok_site_code, is_ok_roll_code, is_ok_roll_directory_name
)


class InputStructureTests(unittest.TestCase):
    """ Test Input Structure """

    def testSiteCodeNormal(self):
        self.assertTrue(is_ok_site_code('A01'))
        self.assertTrue(is_ok_site_code('B'))
        self.assertTrue(is_ok_site_code('b'))
        self.assertTrue(is_ok_site_code('1'))

    def testSiteCodeNonAlphanum(self):
        self.assertFalse(is_ok_site_code('A_01'))
        self.assertFalse(is_ok_site_code('-1'))
        self.assertFalse(is_ok_site_code('A.1'))
        self.assertFalse(is_ok_site_code('AA*B'))

    def testSiteCodeEmpty(self):
        self.assertFalse(is_ok_site_code(''))

    def testRollCodeNormal(self):
        self.assertTrue(is_ok_roll_code('R1'))
        self.assertTrue(is_ok_roll_code('R12323'))
        self.assertTrue(is_ok_roll_code('R0'))

    def testRollCodeNonNum(self):
        self.assertFalse(is_ok_roll_code('RR12'))
        self.assertFalse(is_ok_roll_code('R23_'))
        self.assertFalse(is_ok_roll_code('R2B'))

    def testRollCodeEmpty(self):
        self.assertFalse(is_ok_roll_code(''))
        self.assertFalse(is_ok_roll_code('R'))

    def testRollCodeWrongStart(self):
        self.assertFalse(is_ok_roll_code('r1'))

    def testRollSiteDirCodeNormal(self):
        self.assertTrue(is_ok_roll_directory_name('A01_R1'))
        self.assertTrue(is_ok_roll_directory_name('A1_R12'))

    def testRollSiteDirCodeFaultySep(self):
        self.assertFalse(is_ok_roll_directory_name('A01_R1_'))
        self.assertFalse(is_ok_roll_directory_name('A01__R1'))
        self.assertFalse(is_ok_roll_directory_name('A01-R1'))
        self.assertFalse(is_ok_roll_directory_name('A01R1'))
