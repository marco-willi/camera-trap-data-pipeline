""" Test Extraction of Annotations """
import unittest
import logging
import csv
from collections import Counter

from logger import setup_logger

from zooniverse_exports.extract_annotations import extract_raw_classification

from zooniverse_exports import extractor

setup_logger()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class ExtractClassificationsTests(unittest.TestCase):
    """ Test Import from CSV """

    def setUp(self):
        """ Read Classifications """
        file_classifications = './test/files/raw_classifications.csv'
        raw_classifications = list()
        with open(file_classifications, "r") as ins:
            csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
            header = next(csv_reader)
            for line_no, line in enumerate(csv_reader):
                raw_classifications.append(
                    {h: line[i] for i, h in enumerate(header)})
        self.raw_classifications = raw_classifications

        stats = Counter()
        user_subject_tracker = dict()
        self.extracted_classifications = list()
        args = {'workflow_id': '10337', 'workflow_version_min': '383'}
        for i, cl in enumerate(self.raw_classifications):
            extracted = extract_raw_classification(
                    cl,
                    args,
                    stats,
                    user_subject_tracker)
            self.extracted_classifications += extracted

    def orderListofSingleKeyDicts(self, dict_list):
        return sorted(dict_list, key=lambda x: list(x.keys())[0])

    def testMultiAnswerExtraction(self):
        # multi-answer tasks
        multi_behavior_task = {
                "choice": "GIRAFFE",
                "answers":{"HOWMANY":"5",
                           "WHATBEHAVIORSDOYOUSEE":["EATING", "MOVING"],
                           "ARETHEREANYYOUNGPRESENT":"NO"}}
        actual = extractor.extract_survey_task(
            multi_behavior_task,
            {'QUESTIONS_TO_IGNORE': []})

        expected = [{'arethereanyyoungpresent': 'no'},
                    {'whatbehaviorsdoyousee': ['eating', 'moving']},
                    {'howmany': '5'},
                    {'choice': 'giraffe'}]

        self.assertEqual(
            self.orderListofSingleKeyDicts(expected),
            self.orderListofSingleKeyDicts(actual))

    def testFindQuestionAnswerPairs(self):
        input = [
            {'annos': [
                {'species': 'giraffe',
                 'behaviors': ['eating', 'moving']}]},
            {'annos': [
                {'species': 'elephant',
                 'behaviors': ['eating', 'standing'],
                 'count': '5'}]}
                 ]
        expected = {'species': ['giraffe', 'elephant'],
                    'behaviors': ['standing',  'moving', 'eating'],
                    'count': ['5']}
        expected = {k: v.sort() for k, v in expected.items()}
        actual = extractor.find_question_answer_pairs(input)
        actual = {k: v.sort() for k, v in actual.items()}
        self.assertEqual(expected, actual)

    def testDeduplicateAnswers(self):
        # duplicate answers
        duplicate_blank = [
            [{'count': '1'},
             {'whatbehaviorsdoyousee': ['resting']},
             {'young_present': '0'}, {'species': 'blank'}],
            [{'species': 'blank'}]]
        duplicate_species = [
                [{'count': '1'}, {'whatbehaviorsdoyousee': ['moving']},
                 {'young_present': '0'}, {'species': 'rhinoceros'}],
                [{'count': '1'}, {'whatbehaviorsdoyousee': ['resting']},
                 {'young_present': '0'}, {'species': 'rhinoceros'}]
                ]
        actual_blank = extractor.deduplicate_answers(
            duplicate_blank,
            {'QUESTION_NAME_MAPPER': {'choice': 'species'}})
        expected_blank = [
            [{'count': '1'},
             {'whatbehaviorsdoyousee': ['resting']},
             {'young_present': '0'}, {'species': 'blank'}]]

        self.assertEqual(
            self.orderListofSingleKeyDicts(actual_blank[0]),
            self.orderListofSingleKeyDicts(expected_blank[0]))

        actual_species = extractor.deduplicate_answers(
            duplicate_species,
            {'QUESTION_NAME_MAPPER': {'choice': 'species'}})
        expected_species = [
            [{'count': '1'}, {'whatbehaviorsdoyousee': ['moving']},
             {'young_present': '0'}, {'species': 'rhinoceros'}]]

        self.assertEqual(
            self.orderListofSingleKeyDicts(actual_species[0]),
            self.orderListofSingleKeyDicts(expected_species[0]))

    def testRemoveIneligibleClassifications(self):
        self.assertEqual(
            len([x for x in self.extracted_classifications
                if x['user_name'] == 'user_already_seen']), 0)

        self.assertEqual(
            len([x for x in self.extracted_classifications
                if x['user_name'] == 'invalid_worfklow_id']), 0)

        self.assertEqual(
            len([x for x in self.extracted_classifications
                if x['user_name'] == 'workflow_version_too_low']), 0)

        self.assertEqual(
            len([x for x in self.extracted_classifications
                if x['user_name'] == 'duplicate_class']), 1)

        self.assertEqual(
            len([x for x in self.extracted_classifications
                if x['user_name'] == 'same_user_same_subject']), 1)

    def testExtractAnnotations(self):
        rhino_giraffe = list()
        for cl in self.extracted_classifications:
            if cl['user_name'] == 'rhino_and_giraffe':
                rhino_giraffe.append(cl)
            if cl['user_name'] == 'user_birdother':
                user_birdother = cl
            if cl['user_name'] == 'user_wildebeestblue_5':
                user_wildebeestblue_5 = cl
            if cl['user_name'] == 'rhinos_eating_and_moving':
                rhinos_eating_and_moving = cl

        self.assertEqual(len(rhino_giraffe), 2)
        rhino_anno = rhino_giraffe[0]['annos']
        giraffe_anno = rhino_giraffe[1]['annos']

        self.assertEqual(
            self.orderListofSingleKeyDicts(rhino_anno),
            self.orderListofSingleKeyDicts([
                {'young_present': '0'},
                {'whatbehaviorsdoyousee': ['eating']},
                {'count': '1'},
                {'species': 'rhinoceros'}]))

        self.assertEqual(
            self.orderListofSingleKeyDicts(giraffe_anno),
            self.orderListofSingleKeyDicts([
                {'young_present': '0'},
                {'whatbehaviorsdoyousee': ['eating', 'moving']},
                {'count': '5'},
                {'species': 'giraffe'}]))

        self.assertEqual(
            self.orderListofSingleKeyDicts(user_birdother['annos']),
            self.orderListofSingleKeyDicts([
                {'young_present': '0'},
                {'whatbehaviorsdoyousee': ['moving']},
                {'count': '1'},
                {'species': 'birdother'}]))

        self.assertEqual(
            self.orderListofSingleKeyDicts(user_wildebeestblue_5['annos']),
            self.orderListofSingleKeyDicts([
                 {'young_present': '1'},
                 {'whatbehaviorsdoyousee': ['moving']},
                 {'count': '5'},
                 {'species': 'wildebeestblue'}]))

        self.assertEqual(
            self.orderListofSingleKeyDicts(rhinos_eating_and_moving['annos']),
            self.orderListofSingleKeyDicts([
                {'young_present': '0'},
                {'whatbehaviorsdoyousee': ['eating']},
                {'count': '1'},
                {'species': 'rhinoceros'}]))


if __name__ == '__main__':
    unittest.main()
