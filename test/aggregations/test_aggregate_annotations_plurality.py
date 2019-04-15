""" Test Plurality Aggregations """
import unittest
import logging

from utils.logger import setup_logger

from aggregations.aggregate_annotations_plurality import (
    aggregate_subject_annotations)
from config.cfg import cfg_default as cfg
from aggregations import aggregator


flags = cfg['plurality_aggregation_flags']
flags_global = cfg['global_processing_flags']
setup_logger()
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class AggregateAnnotationsPluralityTests(unittest.TestCase):

    def setUp(self):
        self.required_fields = [
            'user_name', 'classification_id',
            'question__species', 'question__count', 'question__standing']
        self.questions = ['question__species', 'question__count',
                          'question__standing']
        self.annotation_id_to_name_mapper = \
            {i: f for i, f in enumerate(self.required_fields)}

        self.question_main_id = flags_global['QUESTION_DELIMITER'].join(
            [flags_global['QUESTION_PREFIX'], flags_global['QUESTION_MAIN']])

        self.question_type_map = aggregator.create_question_type_map(
            self.questions, flags, flags_global)

        self.test_subjects = {
            'test_standard': [
                ['u1', 'cid1', 'zebra', '1', '0'],
                ['u2', 'cid2', 'zebra', '2', '0'],
                ['u3', 'cid3', 'zebra', '2', '0']],
            'test_minority': [
                ['u1', 'cid1', 'zebra', '1', '0'],
                ['u2', 'cid2', 'zebra', '2', '0'],
                ['u3', 'cid3', 'eland', '2', '0']],
            'test_tie_zebra': [
                ['u1', 'cid1', 'zebra', '1', '0'],
                ['u2', 'cid2', 'zebra', '2', '0'],
                ['u3', 'cid3', 'eland', '2', '0'],
                ['u4', 'cid4', 'eland', '2', '0']],
            'test_tie_eland': [
                ['u1', 'cid1', 'eland', '1', '0'],
                ['u2', 'cid2', 'eland', '2', '0'],
                ['u3', 'cid3', 'zebra', '2', '0'],
                ['u4', 'cid4', 'zebra', '2', '0']],
            'test_count_4': [
                ['u1', 'cid1', 'zebra', '1', '0'],
                ['u2', 'cid2', 'zebra', '4', '0'],
                ['u3', 'cid3', 'zebra', '4', '0'],
                ['u4', 'cid4', 'zebra', '6', '0']],
            'test_count_10': [
                ['u1', 'cid1', 'zebra', '11-50', '0'],
                ['u2', 'cid2', 'zebra', '10', '0'],
                ['u3', 'cid3', 'zebra', '10', '0'],
                ['u4', 'cid4', 'zebra', '9', '0']],
            'test_blank': [
                ['u1', 'cid1', 'blank', '', ''],
                ['u2', 'cid2', 'blank', '', ''],
                ['u3', 'cid3', 'blank', '', ''],
                ['u4', 'cid4', 'zebra', '9', '0']],
            'test_not_blank': [
                ['u1', 'cid1', 'blank', '', ''],
                ['u2', 'cid2', 'blank', '', ''],
                ['u3', 'cid3', 'elephant', '1', '1'],
                ['u4', 'cid4', 'zebra', '9', '0']],
            'test_prop_025': [
                ['u1', 'cid1', 'zebra', '1', '1'],
                ['u2', 'cid2', 'zebra', '4', '0'],
                ['u3', 'cid3', 'zebra', '4', '0'],
                ['u4', 'cid4', 'zebra', '6', '0']],
            'test_prop_1': [
                ['u1', 'cid1', 'zebra', '1', '1'],
                ['u2', 'cid2', 'zebra', '4', '1'],
                ['u3', 'cid3', 'zebra', '4', '1'],
                ['u4', 'cid4', 'zebra', '6', '1']],
            'test_multi': [
                ['u1', 'cid1', 'zebra', '4', '0'],
                ['u1', 'cid1', 'elephant', '3', '1'],
                ['u2', 'cid3', 'zebra', '6', '0'],
                ['u2', 'cid3', 'elephant', '3', '1']],
            'test_multi2': [
                ['u1', 'cid1', 'zebra', '4', '0'],
                ['u1', 'cid1', 'elephant', '3', '1'],
                ['u2', 'cid3', 'zebra', '6', '0'],
                ['u2', 'cid3', 'elephant', '3', '1'],
                ['u3', 'cid4', 'zebra', '6', '0'],
                ['u3', 'cid4', 'elephant', '3', '1'],
                ['u3', 'cid4', 'cheetah', '1', '1']],
            'test_blind_user': [
                ['u1', 'cid1', 'zebra', '1', '1'],
                ['u2', 'cid2', 'zebra', '1', '0'],
                ['u3', 'cid3', 'zebra', '4', '0'],
                ['u4', 'cid4', 'blank', '', '']]
        }

    def testStandardAggregation(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_standard'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = actual['consensus_species'][0]
        actual_agg_info = actual['aggregation_info']
        expected_consensus = 'zebra'
        expected_agg_info = {
            'n_species_ids_per_user_max': 1,
            'n_species_ids_per_user_median': 1,
            'n_users_classified_this_subject': 3,
            'n_users_saw_a_species': 3,
            'n_users_saw_no_species': 0,
            'p_users_saw_a_species': '1.00',
            'pielous_evenness_index': '0.00'}
        self.assertEqual(expected_agg_info, actual_agg_info)
        self.assertEqual(actual_consensus, expected_consensus)

    def testMultiSpeciesAggregation(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_multi'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}
        expected_consensus = {'zebra', 'elephant'}

        actual_agg_info = actual['aggregation_info']
        expected_agg_info = {
            'n_species_ids_per_user_max': 2,
            'n_species_ids_per_user_median': 2,
            'n_users_classified_this_subject': 2,
            'n_users_saw_a_species': 2,
            'n_users_saw_no_species': 0,
            'p_users_saw_a_species': '1.00',
            'pielous_evenness_index': '1.00'}
        self.assertEqual(expected_agg_info, actual_agg_info)
        self.assertEqual(actual_consensus, expected_consensus)

    def testProportionAggFull(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_prop_1'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_species_aggs = actual['species_aggregations']
        expected_spcies_aggs = {'zebra': {
               'n_users_identified_this_species': 4,
               'p_users_identified_this_species': '1.00',
               'question__count_max': '6',
               'question__count_median': '4',
               'question__count_min': '1',
               'question__standing': '1.00'}}

        self.assertEqual(actual_species_aggs, expected_spcies_aggs)

    def testProportionAggPartial(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_prop_025'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_species_aggs = actual['species_aggregations']
        expected_spcies_aggs = {'zebra': {
               'n_users_identified_this_species': 4,
               'p_users_identified_this_species': '1.00',
               'question__count_max': '6',
               'question__count_median': '4',
               'question__count_min': '1',
               'question__standing': '0.25'}}

        self.assertEqual(actual_species_aggs, expected_spcies_aggs)

    def testNotBlankOn50To50(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_not_blank'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}

        self.assertNotIn('blank', actual_consensus)

    def testIsBlank(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_blank'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}

        self.assertIn('blank', actual_consensus)
        self.assertEqual(1, len(actual_consensus))

    def testCountAgg(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_count_10'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_species_aggs = actual['species_aggregations']
        expected_spcies_aggs = {'zebra': {
               'n_users_identified_this_species': 4,
               'p_users_identified_this_species': '1.00',
               'question__count_max': '11-50',
               'question__count_median': '10',
               'question__count_min': '9',
               'question__standing': '0.00'}}

        self.assertEqual(actual_species_aggs, expected_spcies_aggs)

    def testConsensusFirstOnTie(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_tie_zebra'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}

        self.assertIn('zebra', actual_consensus)
        self.assertEqual(1, len(actual_consensus))

    def testConsensusFirstOnTie2(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_tie_eland'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}

        self.assertIn('eland', actual_consensus)
        self.assertEqual(1, len(actual_consensus))

    def testMinorityAgg(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_minority'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_species_aggs = actual['species_aggregations']
        expected_spcies_aggs = {'zebra': {
               'n_users_identified_this_species': 2,
               'p_users_identified_this_species': '0.67',
               'question__count_max': '2',
               'question__count_median': '2',
               'question__count_min': '1',
               'question__standing': '0.00'},
               'eland': {
                  'n_users_identified_this_species': 1,
                  'p_users_identified_this_species': '0.33',
                  'question__count_max': '2',
                  'question__count_median': '2',
                  'question__count_min': '2',
                  'question__standing': '0.00'}}

        self.assertEqual(actual_species_aggs, expected_spcies_aggs)

    def testMulti2SpeciesAggregation(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_multi2'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}
        expected_consensus = {'zebra', 'elephant'}

        actual_agg_info = actual['aggregation_info']
        expected_agg_info = {
            'n_species_ids_per_user_max': 3,
            'n_species_ids_per_user_median': 2,
            'n_users_classified_this_subject': 3,
            'n_users_saw_a_species': 3,
            'n_users_saw_no_species': 0,
            'p_users_saw_a_species': '1.00',
            'pielous_evenness_index': '0.91'}
        self.assertEqual(expected_agg_info, actual_agg_info)
        self.assertEqual(actual_consensus, expected_consensus)

    def testBlindUserAggregation(self):
        actual = aggregate_subject_annotations(
                self.test_subjects['test_blind_user'],
                self.questions,
                self.question_type_map,
                self.question_main_id,
                self.annotation_id_to_name_mapper)

        actual_consensus = {x for x in actual['consensus_species']}
        expected_consensus = {'zebra'}

        actual_agg_info = actual['aggregation_info']
        expected_agg_info = {
            'n_species_ids_per_user_max': 1,
            'n_species_ids_per_user_median': 1,
            'n_users_classified_this_subject': 4,
            'n_users_saw_a_species': 3,
            'n_users_saw_no_species': 1,
            'p_users_saw_a_species': '0.75',
            'pielous_evenness_index': '0.00'}
        self.assertEqual(expected_agg_info, actual_agg_info)
        self.assertEqual(actual_consensus, expected_consensus)

        actual_species_aggs = actual['species_aggregations']
        expected_spcies_aggs = {'zebra': {
               'n_users_identified_this_species': 3,
               'p_users_identified_this_species': '1.00',
               'question__count_max': '4',
               'question__count_median': '1',
               'question__count_min': '1',
               'question__standing': '0.33'}}
        self.assertEqual(actual_species_aggs, expected_spcies_aggs)


if __name__ == '__main__':
    unittest.main()
