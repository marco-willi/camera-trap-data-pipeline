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

    Output CSV (example):
    -------------------
    subject_id,label_num,species,count,moving,eating,standing,...
    17512921,1,WILDEBEEST,10,1,0,1,0,0,1
    17520346,1,NOTHINGHERE,0,0,0,0,0,0,0
    17521219,1,NOTHINGHERE,0,0,0,0,0,0,0
    17523475,1,WILDEBEEST,1,1,0,0,0,0,0
    17529581,1,WILDEBEEST,1,0,0,1,0,0,0
"""
import csv
import argparse

from collections import Counter

from utils import print_progress
from zooniverse_exports.utils import (
    SnapshotSafariAnnotation, Subject, order_dict_by_values)

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

    n_subjects = len(subject_set.keys())
    print("N Subjects: %s" % n_subjects)
    Counter(species_counts)
    species_distribution = order_dict_by_values(species_distribution)

    for k, v in species_distribution.items():
        print("Class %s - # %s (%s %%)" % (k, v, round(100 * v/n_subjects, 2)))

    # subject = subject_set['19237945']
    print("Example Subject")
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
