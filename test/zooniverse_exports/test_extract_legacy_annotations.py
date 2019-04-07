""" Test Extraction of Annotations """
import unittest
import logging
import csv
from collections import Counter

from logger import setup_logger

from zooniverse_exports import legacy_extractor
from config.cfg import cfg

flags = cfg['legacy_extractor_flags']

setup_logger()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class ExtractLegacyClassificationsTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        file_classifications = './test/files/raw_legacy_classifications.csv'
        raw_classifications = list()
        with open(file_classifications, "r") as ins:
            csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
            header = next(csv_reader)
            for line_no, line in enumerate(csv_reader):
                raw_classifications.append(
                    {h: line[i] for i, h in enumerate(header)})
        self.raw_classifications = raw_classifications

        img_to_capture = {
                'SER_S10#H04#R2#S10_H04_R2_IMAG0251.JPG': 'SER_S10#H04#R2#1',
                'SER_S9#C13#R1#S9_C13_R1_IMAG1034.JPG': 'SER_S9#C13#R1#2'}
        stats = Counter()
        user_subject_tracker = dict()
        extracted_all = dict()
        for i, cl in enumerate(self.raw_classifications):
            cls_dict = cl
            extracted = legacy_extractor.extract_raw_classification(
                    cls_dict,
                    img_to_capture,
                    flags,
                    stats,
                    user_subject_tracker)
            try:
                cl_id = extracted['classification_id']
                if cl_id not in extracted_all:
                    extracted_all[cl_id] = list()
                extracted_all[cl_id].append(extracted)
            except:
                pass

        self.extracted_all = extracted_all

    def testNeedsConsolidation(self):
        input1 = [
            {'species': 'lionFemale', 'count': '1'},
            {'species': 'lionFemale', 'count': '2'},
            {'species': 'wildebeest', 'count': '11-50'}]
        input2 = [
            {'species': 'lionFemale', 'count': '1'},
            {'species': 'lionMale', 'count': '2'},
            {'species': 'wildebeest', 'count': '11-50'}]
        input3 = [
            {'species': 'lionFemale', 'count': '1'},
            {'species': 'lionMale', 'count': '1'},
            {'species': 'wildebeest', 'count': '11-50'}]

        self.assertTrue(legacy_extractor.needs_consolidation(input1))
        self.assertFalse(legacy_extractor.needs_consolidation(input2))
        self.assertFalse(legacy_extractor.needs_consolidation(input3))

    def testMapAnswers(self):

        input_map = {'ANSWER_TYPE_MAPPER':
            {'species': {'NOTHING': 'nothinghere'}}}
        answers1 = {'species': 'NOTHING'}
        answers2 = {'species': 'nada'}

        legacy_extractor.map_answers(answers1, input_map)
        expected1 = {'species': 'nothinghere'}

        legacy_extractor.map_answers(answers2, input_map)
        expected2 = {'species': 'nada'}

        self.assertEqual(answers1, expected1)
        self.assertEqual(answers2, expected2)

    def testExtractAnnotations(self):
        expected_1 = {'species': 'cattle', 'count': '8', 'resting': 1,
                      'moving': 0, 'interacting': 0,
                      'young_present': 0,
                      'eating': 0, 'standing': 0,
                      'classification_id': 'cl_2',
                      'user_name': 'standard_cattle',
                      'subject_id': "ASG001xfu1",
                      'capture_id': 'SER_S10#H04#R2#1'}
        actual_1 = self.extracted_all['cl_2'][0]

        expected_2 = {'species': 'elephant', 'count': '3', 'resting': 0,
                      'moving': 0, 'interacting': 0,
                      'young_present': 0,
                      'eating': 0, 'standing': 1}
        actual_2 = self.extracted_all['cl_3'][0]

        expected_1_false = {
            'species': 'cattle', 'count': '8', 'resting': 1,
            'moving': 1, 'interacting': 0,
            'young_present': 0,
            'eating': 0, 'standing': 0,
            'classification_id': 'cl_2',
            'user_name': 'standard_cattle',
            'subject_id': "ASG001xfu1",
            'capture_id': 'SER_S10#H04#R2#1'}

        self.assertTrue(
            set(expected_1.items()).issubset(set(actual_1.items())))

        self.assertTrue(
            set(expected_2.items()).issubset(set(actual_2.items())))

        self.assertFalse(
            set(expected_1_false.items()).issubset(
                set(actual_1.items())))

    def testConsolidateAnnotations(self):
        self.assertEqual(len(self.extracted_all['cl_5']), 2)

        consolidated_classifications =  \
            legacy_extractor.consolidate_all_classifications(
                self.extracted_all, flags)

        self.assertEqual(len(consolidated_classifications['cl_5']), 1)

        expected = {'species': 'elephant', 'count': '2', 'resting': 1,
                      'moving': 0, 'interacting': 0,
                      'young_present': 0,
                      'eating': 0, 'standing': 1}
        actual = consolidated_classifications['cl_5'][0]
        self.assertTrue(
            set(expected.items()).issubset(set(actual.items())))

    def testRemoveDuplicates(self):
        self.assertNotIn('cl_8', self.extracted_all)


if __name__ == '__main__':
    unittest.main()
