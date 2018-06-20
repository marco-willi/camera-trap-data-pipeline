""" Aggregate Zooniverse Classification Extractions to obtain
    Labels for Subjects using the Plurality Algorithm
    (this is slightly different than using the survey reducer)

    Arguments:
    --------------
    - classifications_extracted (str):
        Path to classification file as extracted by
        extract_classifications.py
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

from collections import OrderedDict, Counter
from statistics import median

from utils import print_progress


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

    def order_dict_by_values(d):
        ordered = OrderedDict()
        for w in sorted(d, key=d.get, reverse=True):
            ordered[w] = d[w]
        return ordered

    class LabelType(object):
        """ Label Type """
        def __init__(self, name, confidence=1):
            self.name = name
            self.confidence = confidence

        def setValue(self, value):
            """ Set Label Value """
            raise NotImplementedError

        def _value_is_valid(self, value):
            """ Check validity of label """
            raise NotImplementedError

        def _aggregateLabels(self, label_list):
            """ Aggregate a list of labels """
            raise NotImplementedError

    class BinaryLabel(LabelType):
        """ Binary Label - allowed values between 0 and 1"""
        def __init__(self, name="binary", confidence=1):
            self.name = name
            self.confidence = confidence
            self.allowed_values = ("",  "0.0", "0", 0, "1.0", 1, "1")
            self.ones = ("1.0", 1, "1")

        def setValue(self, value):
            """ Set Label Value """
            if isinstance(value, list):
                self._setValuesToAggregate(value)
            elif self._value_is_valid(value):
                self.value = value
            else:
                raise ValueError("Value %s is not valid, allowed values: %s" %
                                 (value, self.allowed_values))

        def _setValuesToAggregate(self, values_list):
            """ Aggregate a list of values """
            if not all([self._value_is_valid(value) for value in values_list]):
                raise ValueError("Not all values in values list valid")
            agggregated_value = self._aggregateLabels(values_list)
            self.setValue(agggregated_value)

        def _value_is_valid(self, value):
            """ Check validity of label """
            return value in self.allowed_values

        def _aggregateLabels(self, label_list):
            """ Aggregate a list of 0/1 annotations """
            zero_one_annotation = list()
            for anno in label_list:
                if anno in self.ones:
                    zero_one_annotation.append(1)
                else:
                    zero_one_annotation.append(0)
            share = sum(zero_one_annotation) / len(zero_one_annotation)
            return round(share)

    class CountLabel(LabelType):
        """ Count Label """
        def __init__(self, name="count", confidence=1):
            self.name = name
            self.confidence = confidence
            self.allowed_values = (
                "0", "1", "2", "3", "4", "5", "6",
                "7", "8", "9",
                "10", "1150", "51")

        def setValue(self, value):
            if isinstance(value, list):
                self._setValuesToAggregate(value)
            elif self._value_is_valid(value):
                self.value = value
            else:
                raise ValueError("Value %s is not valid, allowed values: %s" %
                                 (value, self.allowed_values))

        def _setValuesToAggregate(self, values_list):
            """ Aggregate a list of values """
            if not all([self._value_is_valid(value) for value in values_list]):
                raise ValueError("Not all values in values list valid")
            agggregated_value = self._aggregateLabels(values_list)
            self.setValue(agggregated_value)

        def _value_is_valid(self, value):
            """ Check validity of label """
            return value in self.allowed_values

        def _aggregateLabels(self, label_list):
            """ Aggregate list of count annotations """
            counts_map_to_numeric = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
                                     "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
                                     "10": 10, "1150": 11, "51": 12}

            counts_map_to_string = {v: k for k, v in
                                    counts_map_to_numeric.items()}
            counts_numerics = list()
            for count in label_list:
                counts_numerics.append(counts_map_to_numeric[count])

            aggregated_counts = int(median(counts_numerics))
            return counts_map_to_string[aggregated_counts]

    class ClassLabel(LabelType):
        """ Class/String Label """
        def __init__(self, name="species", confidence=1):
            self.name = name
            self.confidence = confidence

        def setValue(self, value):
            if self._value_is_valid(value):
                self.value = value
            else:
                raise ValueError("Value %s is not valid" % value)

        def _value_is_valid(self, value):
            """ Check validity of label """
            return isinstance(value, str)

        def _aggregateLabels(self, label_list):
            """ Aggregate List of Labels """
            raise NotImplementedError

    class SnapshotSafariAnnotation(object):
        """ A Snapshot Safari Type of Annotation"""
        def __init__(self, user_id, time):
            self.user_id = user_id
            self.time = time

        def __repr__(self):
            if self.labels is None:
                return "No Data"
            else:
                print_data = []
                for label, label_values in self.labels.items():
                    pr = "#" + str(label) + ":" + str(label_values.value)
                    print_data.append(pr)
                return ''.join(print_data)

        def create_annotation(self, species, count, moving,
                              eating, standing, resting, interacting,
                              young_present):

            species_label = ClassLabel('species')
            species_label.setValue(species)

            count_label = CountLabel('count')
            count_label.setValue(count)

            moving_label = BinaryLabel('moving')
            moving_label.setValue(moving)

            eating_label = BinaryLabel('eating')
            eating_label.setValue(eating)

            standing_label = BinaryLabel('standing')
            standing_label.setValue(standing)

            resting_label = BinaryLabel('resting')
            resting_label.setValue(resting)

            interacting_label = BinaryLabel('interacting')
            interacting_label.setValue(interacting)

            young_present_label = BinaryLabel('young_present')
            young_present_label.setValue(young_present)

            self.labels = {'species': species_label,
                           'count': count_label,
                           'moving': moving_label,
                           'eating': eating_label,
                           'standing': standing_label,
                           'resting': resting_label,
                           'interacting': interacting_label,
                           'young_present': young_present_label}

        def create_annotation_with_conf(
                              self, species, count, moving,
                              eating, standing, resting, interacting,
                              young_present):

            species_label = ClassLabel('species', species[1])
            species_label.setValue(species[0])

            count_label = CountLabel('count', count[1])
            count_label.setValue(count[0])

            moving_label = BinaryLabel('moving', moving[1])
            moving_label.setValue(moving[0])

            eating_label = BinaryLabel('eating', eating[1])
            eating_label.setValue(eating[0])

            standing_label = BinaryLabel('standing', standing[1])
            standing_label.setValue(standing[0])

            resting_label = BinaryLabel('resting', resting[1])
            resting_label.setValue(resting[0])

            interacting_label = BinaryLabel('interacting', interacting[1])
            interacting_label.setValue(interacting[0])

            young_present_label = BinaryLabel('young_present', young_present[1])
            young_present_label.setValue(young_present[0])

            self.labels = {'species': species_label,
                           'count': count_label,
                           'moving': moving_label,
                           'eating': eating_label,
                           'standing': standing_label,
                           'resting': resting_label,
                           'interacting': interacting_label,
                           'young_present': young_present_label}

        def create_from_annotations(self, species, annotations):
            """ Aggregate several Annotations """

            labels = ['count', 'moving', 'eating', 'standing', 'resting',
                      'interacting', 'young_present']
            labels_lists = {k: list() for k in labels}
            for annotation in annotations:
                for label, label_list in labels_lists.items():
                    label_list.append(annotation.labels[label].value)

            self.create_annotation(
                species=species,
                count=labels_lists['count'],
                moving=labels_lists['moving'],
                eating=labels_lists['eating'],
                standing=labels_lists['standing'],
                resting=labels_lists['resting'],
                interacting=labels_lists['interacting'],
                young_present=labels_lists['young_present'])

        def _extract_annotation_counts(self, row, column_mapping):
            """ extract counts """

            # Identify all fields related to counts
            count_field_identifier = 'data.answers_howmany'
            count_fields = [k for k in list(column_mapping.keys())
                            if count_field_identifier in k]

            # Find the count field that was chosen by the volunteer
            for count_field in count_fields:
                if row[column_mapping[count_field]] == '1.0':
                    return count_field.split('.')[-1]
            return ""

        def _extract_annotation_young(self, row, column_mapping):
            """ Extract Young Present information """
            yes = row[column_mapping['data.answers_arethereanyyoungpresent.yes']]
            if yes == '1.0':
                return 1
            else:
                return 0

        def create_annotation_from_row(self, row, column_mapping):
            """ Extract a single row of a extraction.csv """

            # Mapping of labels to CSV column names
            col_names = {
                'species': 'species',
                'count': 'count',
                'moving': 'moving',
                'eating': 'eating',
                'standing': 'standing',
                'resting': 'resting',
                'interacting': 'interacting',
                'young_present': 'young_present'}

            self.create_annotation(
                species=row[column_to_row_mapping[col_names['species']]],
                count=row[column_to_row_mapping[col_names['count']]],
                moving=row[column_to_row_mapping[col_names['moving']]],
                eating=row[column_to_row_mapping[col_names['eating']]],
                standing=row[column_to_row_mapping[col_names['standing']]],
                resting=row[column_to_row_mapping[col_names['resting']]],
                interacting=row[column_to_row_mapping[col_names['interacting']]],
                young_present=row[column_to_row_mapping[col_names['young_present']]]
                )

        def create_annotation_from_ml(self, pred):
            """ Process a ML classification """

            labels_to_export = ['species', 'count', 'moving',
                                'eating',
                                'standing', 'resting',
                                'interacting', 'young_present']

            label_dict = {k: i for i, k in enumerate(labels_to_export)}
            default_values = ['NOTHINGHERE', '0', 0, 0, 0, 0, 0, 0]
            default_confs = [0 for x in range(0, len(default_values))]
            # if overall prediction is empty
            if pred['empty'] == 0:
                default_values[label_dict['species']] = 'NOTHINGHERE'
                default_confs[label_dict['species']] = pred['empty_conf']
            else:
                for label in labels_to_export:
                    default_values[label_dict[label]] = pred[label]
                    default_confs[label_dict[label]] = pred[label + '_conf']

            self.create_annotation_with_conf(
                species=(default_values[label_dict['species']],default_confs[label_dict['species']]),
                count=(default_values[label_dict['count']],default_confs[label_dict['count']]),
                moving=(default_values[label_dict['moving']],default_confs[label_dict['moving']]),
                eating=(default_values[label_dict['eating']],default_confs[label_dict['eating']]),
                standing=(default_values[label_dict['standing']],default_confs[label_dict['standing']]),
                resting=(default_values[label_dict['resting']],default_confs[label_dict['resting']]),
                interacting=(default_values[label_dict['interacting']],default_confs[label_dict['interacting']]),
                young_present=(default_values[label_dict['young_present']],default_confs[label_dict['young_present']])
                )

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

        def aggregateSpeciesLabelsML(self, ret=False, rules=[], max_annos=None):
            """ Aggregate Labels per Species Using Rules """

            species_pred = subject.ml_annotation[0].labels['species'].value
            species_conf = subject.ml_annotation[0].labels['species'].confidence
            rule_match = False
            self.n_annos_aggregated = 0

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
                            self.n_annos_aggregated = 1
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
    with open(output_file + "full.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabels(ret=True)
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)
        print("Used %s annotations" % tot_classifications)

    # Write to Disk
    with open(output_file + "only_2.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabels(2, ret=True)
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

        print("Used %s annotations" % tot_classifications)

    # Write to Disk
    with open(output_file + "only_5.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabels(2, ret=True)
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

        print("Used %s annotations" % tot_classifications)

    # Write to Disk
    with open(output_file + "empty_first2_95.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_two_95conf'])
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

        print("Used %s annotations" % tot_classifications)

    # Write to Disk
    with open(output_file + "empty_first1_95.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['empty_first_95conf'])
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

        print("Used %s annotations" % tot_classifications)

    # Write to Disk
    with open(output_file + "species_first2_95.csv", "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        tot_classifications = 0
        for j, subject in enumerate(subject_set.values()):
            aggs = subject.aggregateSpeciesLabelsML(ret=True, rules=['species_first_two_95conf'])
            tot_classifications += subject.n_annos_aggregated
            subject.aggregated_annotations = aggs
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)
            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

        print("Used %s annotations" % tot_classifications)


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
