""" Test Extraction of Classifications with multiple Workflows """
import unittest
import logging
import csv
from collections import Counter

from zooniverse_exports.extract_annotations import extract_raw_classification

from zooniverse_exports import extractor

logger = logging.getLogger(__name__)


class ExtractMultiWorfklow(unittest.TestCase):

    def setUp(self):

        """ Read Classifications """
        file_classifications = './test/files/raw_classifications_multi_workflow.csv'
        raw_classifications = list()
        with open(file_classifications, "r") as ins:
            csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
            header = next(csv_reader)
            for line_no, line in enumerate(csv_reader):
                raw_classifications.append(
                    {h: line[i] for i, h in enumerate(header)})
        raw_classifications = raw_classifications

        stats = Counter()
        duplicate_tracker = set()
        extracted_classifications = list()
        args = {
            'workflow_id': None,
            'workflow_version_min': None,
            'no_earlier_than_date': None,
            'no_later_than_date': None}
        for i, cl in enumerate(raw_classifications):
            if not extractor.is_in_date_range(
                    cl,
                    args['no_earlier_than_date'],
                    args['no_later_than_date']):
                continue
            if not extractor.is_eligible_workflow(
                    cl,
                    args['workflow_id'],
                    args['workflow_version_min']):
                continue
            if extractor.subject_already_seen(cl):
                continue
            if extractor.classification_is_duplicate(
                    cl, duplicate_tracker):
                continue
            extracted = extract_raw_classification(
                    cl,
                    args,
                    stats)
            extracted_classifications += extracted
        self.extracted_classifications = extracted_classifications

    def testDummy(self):
        pass

if __name__ == '__main__':
    unittest.main()
