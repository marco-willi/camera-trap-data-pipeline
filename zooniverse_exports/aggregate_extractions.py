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

from collections import OrderedDict, Counter
from statistics import median

from utils import print_progress


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-classifications_extracted", type=str, required=True)
    parser.add_argument("-output_csv", type=str, required=True)

    args = vars(parser.parse_args())

    #############################
    # Parameters
    #############################

    labels_to_export = ['species', 'count', 'moving', 'eating',
                        'standing', 'resting',
                        'interacting', 'young_present']

    output_header = ['subject_id', 'label_num'] + labels_to_export

    input_file = args['classifications_extracted']
    output_file = args['output_csv']

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
        def __init__(self, name):
            self.name = name

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
        def __init__(self, name="binary"):
            self.name = name
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
        def __init__(self, name="count"):
            self.name = name
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
        def __init__(self, name="species"):
            self.name = name

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

    class Subject(object):
        """ a subject """
        def __init__(self, id):
            self.id = id
            self.annotations = list()
            self.aggregated_annotations = list()

        def add_annotation(self, annotation):
            self.annotations.append(annotation)

        def _get_species(self):
            species = list()
            n_species = self._calc_number_of_annotations()

            for annotation in self.annotations:
                species.append(annotation.labels['species'].value)

            species_counts = Counter(species)
            ordered_species = order_dict_by_values(species_counts)
            self.ordered_species = ordered_species
            self.species = list(self.ordered_species.keys())[0: n_species]

        def _calc_number_of_annotations(self):
            """ Calculate median number of annotations """
            user_ids = list()
            for annotation in self.annotations:
                user_ids.append(annotation.user_id)
            user_counts = Counter(user_ids)
            median_annotations = int(median(list(user_counts.values())))
            return median_annotations

        def aggregateSpeciesLabels(self):
            """ Aggregate Labels per Species """

            # extract species labels
            self._get_species()

            # Collect all aggregations for the species
            species_annotations = {s: list() for s in self.species}
            for annotation in self.annotations:
                species_label = annotation.labels['species'].value
                if species_label in species_annotations.keys():
                    species_annotations[species_label].append(annotation)

            # create new aggregated annotations for each species
            for species in self.species:
                aggregated_annotation = SnapshotSafariAnnotation(
                    user_id="aggregated",
                    time="aggregated")

                aggregated_annotation.create_from_annotations(
                    species,
                    species_annotations[species])

                self.aggregated_annotations.append(aggregated_annotation)

    # Read Annotations
    with open(input_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        subject_set = dict()
        for row_id, row in enumerate(reader):
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

    # Create Aggregations
    for subject in subject_set.values():
        subject.aggregateSpeciesLabels()

    species_distribution = dict()
    species_counts = list()
    for subject in subject_set.values():
        species_counts.append(len(subject.species))
        for species in subject.species:
            if species not in species_distribution:
                species_distribution[species] = 0
            species_distribution[species] += 1

    print("N Subjects: %s" % len(subject_set.keys()))
    Counter(species_counts)
    species_distribution = order_dict_by_values(species_distribution)

    for k, v in species_distribution.items():
        print("Class %s - # %s" % (k, v))

    # subject = subject_set['19237945']
    for annot in subject.aggregated_annotations:
        for k, v in annot.labels.items():
            print("Label %s: %s" % (k, v.value))

    # Write to Disk
    with open(output_file, "w", newline='') as outs:
        csv_writer = csv.writer(outs, delimiter=',')
        print("Writing file to %s" % output_file)
        csv_writer.writerow(output_header)
        tot = len(subject_set)
        for j, subject in enumerate(subject_set.values()):
            n_labels = len(subject.aggregated_annotations)
            print_progress(j, tot)

            # Create a seprate record for each label
            for i in range(0, n_labels):
                anno = subject.aggregated_annotations[i].labels
                row = [subject.id, i+1]
                for label in labels_to_export:
                    row.append(anno[label].value)
                csv_writer.writerow(row)

    #for annotation in subject.annotations:


    # Examples:
    # 18877949, counting
