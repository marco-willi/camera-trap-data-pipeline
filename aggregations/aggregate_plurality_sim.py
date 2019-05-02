""" Aggregate Zooniverse Classifications to obtain
    Labels for Subjects using the Plurality Algorithm
    Allows for restricting the use of the first N users only to
    Simulate the effect on final labels
"""
import csv
import os
import argparse
import math
from statistics import median_high, StatisticsError
from collections import defaultdict, OrderedDict
import logging

import pandas as pd

from utils.logger import set_logging
from config.cfg import cfg
from aggregations import aggregator
from utils.utils import (
    print_nested_dict, set_file_permission, OrderedCounter)


flags = cfg['plurality_aggregation_flags']
flags_global = cfg['global_processing_flags']

# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/ENO/ENO_S1_annotations.csv'
# args['output_csv'] = '/home/packerc/will5448/ENO_S1_plurality_raw_sim.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/ENO/ENO_S1_subjects_extracted.csv'
# args['export_consensus_only'] = False
# args['log_dir'] = None
# args['log_filename'] = ''
# args['n_users_to_use'] = [1, 2, 5, 10, 99]


def aggregate_species(
        species_names, species_stats,
        questions, question_type_map, n_users_total):
    """ Aggregate species stats """
    species_aggs = {x: OrderedDict() for x in species_names}
    for species, stats in species_stats.items():
        if species not in species_names:
            continue
        for question in questions:
            question_type = question_type_map[question]
            if question_type == 'count':
                # generate multiple count aggregations
                for agg_type in flags['COUNT_AGGREGATION_MODES']:
                    agg = aggregator.count_aggregator(
                        stats[question], flags, mode=agg_type)
                    agg_name = '{}_{}'.format(question, agg_type)
                    species_aggs[species][agg_name] = agg
            elif question_type == 'prop':
                agg = aggregator.proportion_affirmative(stats[question])
                species_aggs[species][question] = agg
            elif question_type == 'main':
                continue
        # add overall species stats
        species_aggs[species]['n_users_identified_this_species'] = \
            len(stats['classification_id'])
        n_user_id = species_aggs[species]['n_users_identified_this_species']
        p_user_id = '{:.2f}'.format(n_user_id / n_users_total)
        species_aggs[species]['p_users_identified_this_species'] = p_user_id
    return species_aggs


def calculate_pielou(votes_list):
    """ Calculate pielous evenness index
    votes_list: list with the number of votes for each species
    """
    if len(votes_list) < 2:
        return 0
    # denominator
    lnS = math.log(len(votes_list))
    # numerator
    sumlist = sum(votes_list)
    plist = [float(n)/sumlist for n in votes_list]
    plnplist = [n * math.log(n) for n in plist]
    sumplnp = -sum(plnplist)
    return sumplnp/lnS


def aggregate_subject_annotations(
        subject_data,
        questions,
        question_type_map,
        question_main_id):
    """ Aggregate subject annotations """
    # initialize Counter objects
    stat_all = defaultdict(OrderedCounter)
    stat_species_only = defaultdict(OrderedCounter)
    # extract and add annotations to stats counters
    for anno_dict in subject_data:
        for k, v in anno_dict.items():
            stat_all[k].update({v})
        # store species only answers
        main_answer = anno_dict[question_main_id]
        if main_answer != flags_global['QUESTION_MAIN_EMPTY']:
            for k, v in anno_dict.items():
                stat_species_only[k].update({v})
    # median number of species identifications per user
    # if nobody ids a species, set this to 0
    try:
        n_species_ids_per_user_median = int(
            median_high(stat_species_only['user_name'].values()))
    except StatisticsError:
        n_species_ids_per_user_median = 0
    # get the max number of species identified by any user
    try:
        n_species_ids_per_user_max = int(
            max(stat_species_only['user_name'].values()))
    except ValueError:
        n_species_ids_per_user_max = 0
    # Calculate some statistics
    n_subject_classifications = len(stat_all['classification_id'])
    n_subject_users = len(stat_all['user_name'])
    n_users_id_species = len(stat_species_only['user_name'])
    n_users_id_empty = n_subject_users - n_users_id_species
    p_users_id_species = n_users_id_species / n_subject_users
    # order species by frequency of identifications
    # ties are ordered arbitrarily
    # (according to which species was detected first)
    species_by_frequency = stat_all[question_main_id].most_common()
    species_names_by_frequency = [x[0] for x in species_by_frequency]
    # calc stats for all species
    species_stats = aggregator.stats_for_species(
            species_names_by_frequency, subject_data,
            species_field=question_main_id
            )
    # define empty capture if more volunteers saw nothing
    # than saw something
    is_empty = n_users_id_empty > n_users_id_species
    if is_empty:
        species_aggs = aggregate_species(
                species_names_by_frequency, species_stats,
                questions, question_type_map,
                n_subject_classifications)
        consensus_species = [flags_global['QUESTION_MAIN_EMPTY']]
        pielou = 0
    else:
        species_names_no_empty = [
            x for x in species_names_by_frequency
            if x != flags_global['QUESTION_MAIN_EMPTY']]
        species_aggs = aggregate_species(
                species_names_no_empty, species_stats,
                questions, question_type_map,
                n_users_id_species)
        # calculate pielou
        pielou = calculate_pielou(
            [x['n_users_identified_this_species']
             for x in species_aggs.values()])
        # Determine top / consensus species based on the median number of
        # different species identified by the volunteers
        consensus_species = [species_names_no_empty[i] for i in
                             range(n_species_ids_per_user_median)]
    # collect information to be added to the export
    agg_info = {
        'n_species_ids_per_user_median': n_species_ids_per_user_median,
        'n_species_ids_per_user_max': n_species_ids_per_user_max,
        'n_users_classified_this_subject': n_subject_users,
        'n_users_saw_a_species': n_users_id_species,
        'n_users_saw_no_species': n_users_id_empty,
        'p_users_saw_a_species': '{:.2f}'.format(p_users_id_species),
        'pielous_evenness_index': '{:.2f}'.format(pielou)
         }
    record = {
        'species_aggregations': species_aggs,
        'aggregation_info': agg_info,
        'consensus_species': consensus_species}
    return record


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annotations", type=str, required=True,
        help="Path to extracted annotations")
    parser.add_argument(
        "--output_csv", type=str, required=True,
        help="Path to file to store aggregated annotations.")
    parser.add_argument(
        "--export_consensus_only", action="store_true",
        help="Export only species with plurality consensus")
    parser.add_argument(
        "--n_users_to_use", nargs='+', type=int, default=[1, 2, 5, 10, 99],
        help="Export only species with plurality consensus")

    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='aggregate_annotations_plurality')

    args = vars(parser.parse_args())

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['annotations']):
        raise FileNotFoundError(
            "annotations: {} not found".format(
             args['annotations']))

    ######################################
    # Configuration
    ######################################

    # logging
    set_logging(args['log_dir'], args['log_filename'])

    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # logging flags
    print_nested_dict('', flags)

    question_main_id = flags_global['QUESTION_DELIMITER'].join(
        [flags_global['QUESTION_PREFIX'], flags_global['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags_global['QUESTION_PREFIX'],
        flags_global['QUESTION_DELIMITER'])

    ######################################
    # Import Annotations
    ######################################

    # Read Annotations and associate with subject id
    subject_annotations = dict()
    with open(args['annotations'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        questions = [x for x in header if x.startswith(question_column_prefix)]
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Imported {:,} annotations".format(line_no))
            # convert to dict
            line_dict = {header[i]: x for i, x in enumerate(line)}
            if line_dict['subject_id'] not in subject_annotations:
                subject_annotations[line_dict['subject_id']] = list()
            subject_annotations[line_dict['subject_id']].append(line_dict)

    question_type_map = aggregator.create_question_type_map(
        questions, flags, flags_global)

    ######################################
    # Aggregate Annotations
    ######################################

    def extract_first_n_users_annotations(subject_data, n_users=2):
        """ Extract annotations of first n users for a subject """
        users = OrderedDict([(x['user_name'], 0) for x in subject_data])
        n_users_real = len(users)
        users_to_extract = set(list(users)[0:min(n_users, n_users_real)])
        subject_data_selected = list()
        for annotation in subject_data:
            if annotation['user_name'] in users_to_extract:
                subject_data_selected.append(annotation)
        return subject_data_selected

    subject_species_aggregations = dict()
    for num, (subject_id, subject_data) in enumerate(subject_annotations.items()):
        # print status
        if ((num % 10000) == 0) and (num > 0):
            print("Aggregated {:,} subjects".format(num))
        # gradually select more users
        records = list()
        for n_users_to_extract in args['n_users_to_use']:
            subject_data_select = extract_first_n_users_annotations(
                subject_data, n_users=n_users_to_extract)
            record = aggregate_subject_annotations(
                        subject_data_select,
                        questions,
                        question_type_map,
                        question_main_id)
            record['aggregation_info']['max_users_used'] = n_users_to_extract
            records.append(record)
        subject_species_aggregations[subject_id] = records

    # Create one record per identification
    subject_identificatons = list()
    for subject_id, subject_agg_data_list in subject_species_aggregations.items():
        # export each species
        for subject_agg_data in subject_agg_data_list:
            for sp, species_dat in subject_agg_data['species_aggregations'].items():
                species_is_plurality_consensus = \
                    int(sp in subject_agg_data['consensus_species'])
                record = {
                    'subject_id': subject_id,
                    question_main_id: sp,
                    **species_dat,
                    **subject_agg_data['aggregation_info'],
                    'species_is_plurality_consensus': species_is_plurality_consensus}
                subject_identificatons.append(record)

    # extract all questions and order them by the original ordering
    questions_original = questions
    questions_found = set()
    for row in subject_identificatons:
        row_questions = list(row.keys())
        questions_found = questions_found.union(
            {x for x in row_questions
             if x.startswith(question_column_prefix)})
    questions = list(questions_found)
    questions = sorted(
        questions,
        key=lambda x: '{}_{}'.format(
            questions_original.index(
                [q for q in questions_original if x.startswith(q)][0]), x))

    ######################################
    # Export to CSV
    ######################################

    df_out = pd.DataFrame(subject_identificatons)

    # order columns: subject_id, questions, rest
    cols = df_out.columns.tolist()
    first_cols = ['subject_id'] + questions
    first_cols = [x for x in first_cols if x in cols]
    cols_rearranged = first_cols + [x for x in cols if x not in first_cols]
    df_out = df_out[cols_rearranged]

    # sort output by subject_id
    df_out.sort_values(by=first_cols, inplace=True)

    if args['export_consensus_only']:
        df_out = df_out[df_out['species_is_plurality_consensus'] == 1]

    df_out.to_csv(args['output_csv'], index=False)

    logger.info("Wrote {} aggregations to {}".format(
        df_out.shape[0], args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
