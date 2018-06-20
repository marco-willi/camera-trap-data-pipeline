""" Aggregate Zooniverse Classification Extractions using different
    Logics in how to combine Machine and Human Classifications

    Arguments:
    --------------
    - classifications_extracted (str):
        Path to classification file as extracted by
        extract_classifications.py
    - aggregated_predictions (str):
        Path to a file that contains aggregated machine predictions
    - output_csv (str):
        Path to new aggregated csv file (will be overwritten)

    Example Usage:
    --------------
    python3 aggregate_extractions.py \
            -classifications_extracted classifications_extracted.csv \
            -output_csv classifications_aggregated.csv
"""
import csv
import argparse
import json
import random

from collections import Counter
from statistics import median

from utils import print_progress
from zooniverse_exports.utils import (
    SnapshotSafariAnnotation,
    order_dict_by_values)


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-classifications_extracted", type=str, required=True)
    parser.add_argument("-aggregated_predictions", type=str, required=True)
    parser.add_argument("-output_csv", type=str, required=True)

    args = vars(parser.parse_args())

    # args = dict()
    # args['classifications_extracted'] = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\classifications_extracted_sampled.csv'
    # args['aggregated_predictions'] = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\SER_S11_predictions.json'
    # args['output_csv'] = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\classifications_aggregated_ml_'
    #args['label_mapping'] = 'D:\\Studium_GD\\Zooniverse\\SnapshotSafari\\data\\zooniverse_exports\\SER\\label_mapping.json'

    #############################
    # Parameters
    #############################

    labels_to_export = ['species', 'count', 'moving', 'eating',
                        'standing', 'resting',
                        'interacting', 'young_present']

    output_header = ['subject_id', 'label_num'] + labels_to_export

    input_file = args['classifications_extracted']
    output_file = args['output_csv']
    pred_file = args['aggregated_predictions']

    #############################
    # Functions and Classes
    #############################

    class Subject(object):
        """ a subject """
        def __init__(self, id):
            self.id = id
            self.annotations = list()
            self._annotations_agg = self.annotations
            self.aggregated_annotations = list()
            self.ml_annotation = list()

        def add_ml_annotation(self, annotation):
            self.ml_annotation.append(annotation)

        def add_annotation(self, annotation):
            self.annotations.append(annotation)

        def _get_species(self):
            species = list()
            n_species = self._calc_number_of_annotations()

            for annotation in self._annotations_agg:
                species.append(annotation.labels['species'].value)

            species_counts = Counter(species)
            ordered_species = order_dict_by_values(species_counts)
            self.ordered_species = ordered_species
            self.species = list(self.ordered_species.keys())[0: n_species]

        def _calc_number_of_annotations(self):
            """ Calculate median number of annotations """
            user_ids = list()
            for annotation in self._annotations_agg:
                user_ids.append(annotation.user_id)
            user_counts = Counter(user_ids)
            median_annotations = int(median(list(user_counts.values())))
            return median_annotations

        def aggregateRule(self, rule):
            """ Returns aggregations of a specific rule """

            if rule == 'all':
                res = self.aggregateSpeciesLabels(max_annos=None, ret=True)
            elif rule == 'max_2':
                res = self.subject.aggregateSpeciesLabels(2, ret=True)
            elif rule == 'max_5':
                res = self.subject.aggregateSpeciesLabels(5, ret=True)
            elif rule in ['empty_first_two_95conf', 'empty_first_two_90conf',
                          'empty_first_95conf', 'species_first_two_95conf']:
                res = self.aggregateSpeciesLabelsML(ret=True, rules=[rule])
            return res

        def aggregateSpeciesLabelsML(self, ret=False, rules=[], max_annos=None):
            """ Aggregate Labels per Species Using Rules """

            rule_match = False
            self.n_annos_aggregated = 0

            try:
                species_pred = subject.ml_annotation[0].labels['species'].value
                species_conf = subject.ml_annotation[0].labels['species'].confidence
            except:
                print("Subject prediction not found for id %s" % subject.id)
                return self.aggregateSpeciesLabels(max_annos=max_annos, ret=ret)

            if 'empty_first_two_95conf' in rules:
                if species_pred == 'NOTHINGHERE' and species_conf >= 0.95:
                    human_aggs = self.aggregateSpeciesLabels(max_annos=2, ret=True)
                    n_human_aggs = len(human_aggs)
                    if n_human_aggs == 1:
                        human_species_pred = human_aggs[0].labels['species'].value
                        if human_species_pred == 'NOTHINGHERE':
                            rule_match = True
                            self.n_annos_aggregated = 2
                            if ret:
                                return human_aggs
                            else:
                                self.aggregated_annotations.append(human_aggs)

            if 'empty_first_two_90conf' in rules:
                if species_pred == 'NOTHINGHERE' and species_conf >= 0.90:
                    human_aggs = self.aggregateSpeciesLabels(max_annos=2, ret=True)
                    n_human_aggs = len(human_aggs)
                    if n_human_aggs == 1:
                        human_species_pred = human_aggs[0].labels['species'].value
                        if human_species_pred == 'NOTHINGHERE':
                            rule_match = True
                            self.n_annos_aggregated = 2
                            if ret:
                                return human_aggs
                            else:
                                self.aggregated_annotations.append(human_aggs)

            elif 'empty_first_95conf' in rules:
                if species_pred == 'NOTHINGHERE' and species_conf >= 0.95:
                    human_aggs = self.aggregateSpeciesLabels(max_annos=1, ret=True)
                    n_human_aggs = len(human_aggs)
                    if n_human_aggs == 1:
                        human_species_pred = human_aggs[0].labels['species'].value
                        if human_species_pred == 'NOTHINGHERE':
                            rule_match = True
                            self.n_annos_aggregated = 1
                            if ret:
                                return human_aggs
                            else:
                                self.aggregated_annotations.append(human_aggs)

            elif 'species_first_two_95conf' in rules:
                if not species_pred == 'NOTHINGHERE' and species_conf >= 0.95:
                    human_aggs = self.aggregateSpeciesLabels(max_annos=2, ret=True)
                    n_human_aggs = len(human_aggs)
                    if n_human_aggs == 1:
                        human_species_pred = human_aggs[0].labels['species'].value
                        if human_species_pred == species_pred:
                            rule_match = True
                            self.n_annos_aggregated = 2
                            if ret:
                                return human_aggs
                            else:
                                self.aggregated_annotations.append(human_aggs)

            # If Rules do not match
            if not rule_match:
                if max_annos is None:
                    self._annotations_agg = self.annotations
                else:
                    n_annos = len(self.annotations)
                    n_to_get = min([n_annos, max_annos])
                    self._annotations_agg = [x for x in self.annotations[0:n_to_get]]

                # extract species labels
                self._get_species()

                # Collect all aggregations for the species
                species_annotations = {s: list() for s in self.species}
                for annotation in self._annotations_agg:
                    species_label = annotation.labels['species'].value
                    if species_label in species_annotations.keys():
                        species_annotations[species_label].append(annotation)

                self.n_annos_aggregated = len(self._annotations_agg)

                # create new aggregated annotations for each species
                if ret:
                    to_return = list()
                for species in self.species:
                    aggregated_annotation = SnapshotSafariAnnotation(
                       user_id="aggregated",
                       time="aggregated")

                    aggregated_annotation.create_from_annotations(
                       species,
                       species_annotations[species])
                    if ret:
                        to_return.append(aggregated_annotation)
                    else:

                        self.aggregated_annotations.append(aggregated_annotation)
                if ret:
                    return to_return

        def aggregateSpeciesLabels(self, max_annos=None, ret=False):
            """ Aggregate Labels per Species """

            self.n_annos_aggregated = 0

            if max_annos is None:
                self._annotations_agg = self.annotations
            else:
                n_annos = len(self.annotations)
                n_to_get = min([n_annos, max_annos])
                self._annotations_agg = [x for x in self.annotations[0:n_to_get]]

            # extract species labels
            self._get_species()

            # Collect all aggregations for the species
            species_annotations = {s: list() for s in self.species}
            for annotation in self._annotations_agg:
                species_label = annotation.labels['species'].value
                if species_label in species_annotations.keys():
                    species_annotations[species_label].append(annotation)

            self.n_annos_aggregated = len(self._annotations_agg)
            # create new aggregated annotations for each species
            if ret:
                to_return = list()
            for species in self.species:
                aggregated_annotation = SnapshotSafariAnnotation(
                    user_id="aggregated",
                    time="aggregated")

                aggregated_annotation.create_from_annotations(
                    species,
                    species_annotations[species])
                if ret:
                    to_return.append(aggregated_annotation)
                else:

                    self.aggregated_annotations.append(aggregated_annotation)
            if ret:
                return to_return

    # Read Annotations
    with open(input_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        subject_set = dict()
        for row_id, row in enumerate(reader):
            if (row_id % 10000) == 0:
                print("Processing Classification %s" % row_id)
            if row_id == 0:
                header = row
                column_to_row_mapping = {x: i for i, x in enumerate(header)}
                row_to_column_mapping = {i: x for i, x in enumerate(header)}
                continue
            else:
                annotation = SnapshotSafariAnnotation(
                    user_id=row[column_to_row_mapping['user_name']],
                    time=row[column_to_row_mapping['user_name']])
                annotation.create_annotation_from_row(row, column_to_row_mapping)
                subject_id = row[column_to_row_mapping['subject_id']]
                user_id = row[column_to_row_mapping['user_name']]
                if subject_id not in subject_set:
                    subject = Subject(id=subject_id)
                    subject_set[subject_id] = subject
                subject_set[subject_id].add_annotation(annotation)

    # Read ML Scores
    with open(pred_file, 'r') as f:
        pred_data = json.load(f)

    # Add ML Annotation
    for subject_id, preds in pred_data.items():

        annotation = SnapshotSafariAnnotation(
            user_id='ml_agent',
            time='now')
        annotation.create_annotation_from_ml(preds)
        user_id = 'ml_agent'
        if subject_id in subject_set:
            subject_set[subject_id].add_ml_annotation(annotation)

    # Write to Disk
    rules = ['all', 'max_2', 'max_5', 'empty_first_two_95conf',
             'empty_first_two_90conf', 'empty_first_95conf',
             'species_first_two_95conf']
    with open(output_file, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header + ['n_annos', 'rule'])
        # calculate different rules
        for rule in rules:
            tot_classifications = 0
            for j, subject in enumerate(subject_set.values()):
                aggs = subject.aggregateRule(rule)
                tot_classifications += subject.n_annos_aggregated
                subject.aggregated_annotations = aggs
                n_labels = len(subject.aggregated_annotations)
                # Create a seprate record for each label
                for i in range(0, n_labels):
                    anno = subject.aggregated_annotations[i].labels
                    row = [subject.id, i+1]
                    for label in labels_to_export:
                        row.append(anno[label].value)
                    row.append(subject.n_annos_aggregated)
                    row.append(rule)
                    csv_writer.writerow(row)
            print("Rule %s: %s annotations" % (rule, tot_classifications))

    # # Write to Disk
    # fnam = output_file + "full.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabels(ret=True)
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "only_2.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabels(2, ret=True)
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "only_5.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabels(5, ret=True)
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "empty_first2_95.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_two_95conf'])
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "empty_first2_90.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_two_90conf'])
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "empty_first1_95.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_95conf'])
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)
    #
    # # Write to Disk
    # fnam = output_file + "species_first2_95.csv"
    # with open(fnam, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % fnam)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     tot_classifications = 0
    #     for j, subject in enumerate(subject_set.values()):
    #         aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['species_first_two_95conf'])
    #         tot_classifications += subject.n_annos_aggregated
    #         subject.aggregated_annotations = aggs
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             row.append(subject.n_annos_aggregated)
    #             csv_writer.writerow(row)
    #
    #     print("Used %s annotations" % tot_classifications)


    species_distribution = dict()
    species_counts = list()
    for subject in subject_set.values():
        species_counts.append(len(subject.species))
        for species in subject.species:
            if species not in species_distribution:
                species_distribution[species] = 0
            species_distribution[species] += 1

    n_subjects = len(subject_set.keys())
    print("N Subjects: %s" % n_subjects)
    Counter(species_counts)
    species_distribution = order_dict_by_values(species_distribution)

    for k, v in species_distribution.items():
        print("Class %s - # %s (%s %%)" % (k, v, round(100 * v/n_subjects, 2)))


    # # Create Aggregations
    # for subject in subject_set.values():
    #     subject.aggregateSpeciesLabels()
    #
    #     subject.aggregated_annoations_max5 = subject.aggregateSpeciesLabels(5, ret=True)
    #     subject.aggregated_annoations_max10 = subject.aggregateSpeciesLabels(10, ret=True)
    #
    # # Example
    # subject = subject_set['18870739']
    # subject.aggregateSpeciesLabels()
    # subject.aggregateSpeciesLabels(2, ret=True)
    # subject.aggregateSpeciesLabels(5, ret=True)
    # subject.aggregateSpeciesLabelsML(ret=True, rule_no='empty_first_two_95conf')
    #
    #
    # # Example
    # subject = subject_set['18870739']
    # subject.aggregateSpeciesLabels()
    # subject.aggregateSpeciesLabels(2, ret=True)
    # subject.aggregateSpeciesLabels(5, ret=True)
    # subject.aggregateSpeciesLabelsML(ret=True, rule_no='empty_first_two_95conf')
    #
    #
    #
    # all_keys = list(subject_set.keys())
    # random.shuffle(all_keys)
    # random_keys = all_keys[0:10]
    # for sub in random_keys:
    #     subject = subject_set[sub]
    #     print("=============================================================")
    #     print(sub)
    #     print("Full Label")
    #     print(subject.aggregateSpeciesLabels(ret=True))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #     print("----------------")
    #     print("Only 2 Annos")
    #     print(subject.aggregateSpeciesLabels(2, ret=True))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #     print("----------------")
    #     print("Only 5 Annos")
    #     print(subject.aggregateSpeciesLabels(5, ret=True))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #     print("----------------")
    #     print("Empty after first two")
    #     print(subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_two_95conf']))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #     print("----------------")
    #     print("Empty after first one")
    #     print(subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_95conf']))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #     print("----------------")
    #     print("Species after first two")
    #     print(subject.aggregateSpeciesLabelsML(ret=True, rules=['species_first_two_95conf']))
    #     print("N annos required: %s" % subject.n_annos_aggregated)
    #
    #
    #
    # subject_set['18871707'].annotations
    # subject_set['18871707'].ml_annotation
    # pred_data['18871707']
    # subject_set['18862572'].annotations
    # subject_set['18862572'].ml_annotation[0]
    # # subject = subject_set['19237945']
    # print("Example Subject")
    # for annot in subject.aggregated_annotations:
    #     for k, v in annot.labels.items():
    #         print("Label %s: %s" % (k, v.value))
    #
    # # Write to Disk
    # with open(output_file, "w", newline='') as outs:
    #     csv_writer = csv.writer(outs, delimiter=',')
    #     print("Writing file to %s" % output_file)
    #     csv_writer.writerow(output_header)
    #     tot = len(subject_set)
    #     for j, subject in enumerate(subject_set.values()):
    #         n_labels = len(subject.aggregated_annotations)
    #         print_progress(j, tot)
    #
    #         # Create a seprate record for each label
    #         for i in range(0, n_labels):
    #             anno = subject.aggregated_annotations[i].labels
    #             row = [subject.id, i+1]
    #             for label in labels_to_export:
    #                 row.append(anno[label].value)
    #             csv_writer.writerow(row)
    #
    # #for annotation in subject.annotations:
    #
    #
    # # Examples:
    # # 18877949, counting
