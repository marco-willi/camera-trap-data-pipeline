""" Aggregate Zooniverse Classifications to obtain
    Labels for Subjects using the Plurality Algorithm
"""
import csv
import os
import argparse
import math
from statistics import median_high, StatisticsError
from collections import Counter, defaultdict
import logging

from logger import setup_logger, create_log_file
from config.cfg import cfg
from zooniverse_aggregations import aggregator
from utils import (
    print_nested_dict, set_file_permission)


flags = cfg['plurality_aggregation_flags']

# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_subjects.csv'
#
# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_aggregated.csv'
# args['export_consensus_only'] = False
#
# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_subjects.csv'
#
# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_subjects.csv'
# args['export_consensus_only'] = False


# args = dict()
# args['annotations'] = '/home/packerc/shared/zooniverse/Exports/PLN/PLN_S1_annotations.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/PLN/PLN_S1_annotations_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/PLN/PLN_S1_subjects.csv'
# args['export_consensus_only'] = True
# args['export_sample_size'] = 300

def aggregate_species(
        species_names, species_stats,
        questions, question_type_map, n_users_total):
    """ Aggregate species stats """
    species_aggs = {x: dict() for x in species_names}
    for species, stats in species_stats.items():
        if species not in species_names:
            continue
        for question in questions:
            question_type = question_type_map[question]
            if question_type == 'count':
                agg = aggregator.count_aggregator_median(
                    stats[question], flags)
            elif question_type == 'prop':
                agg = aggregator.proportion_affirmative(stats[question])
            elif question_type == 'main':
                continue
            species_aggs[species][question] = agg
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
    if args['log_dir'] is not None:
        log_file_path = create_log_file(args['log_dir'], args['log_filename'])
        setup_logger(log_file_path)
    else:
        setup_logger()
    logger = logging.getLogger(__name__)

    for k, v in args.items():
        logger.info("Argument {}: {}".format(k, v))

    # logging flags
    print_nested_dict('', flags)

    question_main_id = flags['QUESTION_DELIMITER'].join(
        [flags['QUESTION_PREFIX'], flags['QUESTION_MAIN']])
    question_column_prefix = '{}{}'.format(
        flags['QUESTION_PREFIX'],
        flags['QUESTION_DELIMITER'])

    ######################################
    # Import Annotations
    ######################################

    # Read Annotations and associate with subject id
    subject_annotations = dict()
    with open(args['annotations'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        questions = [x for x in header if x.startswith(question_column_prefix)]
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Imported {:,} annotations".format(line_no))
            # store data into subject dict
            subject_id = line[row_name_to_id_mapper['subject_id']]
            if subject_id not in subject_annotations:
                subject_annotations[subject_id] = list()
            subject_annotations[subject_id].append(line)

    annotation_id_to_name_mapper = {
        v: k for k, v in row_name_to_id_mapper.items()}

    question_type_map = aggregator.create_question_type_map(
        questions, flags)

    ######################################
    # Aggregate Annotations
    ######################################

    subject_species_aggregations = dict()
    for num, (subject_id, subject_data) in enumerate(subject_annotations.items()):
        # print status
        if ((num % 10000) == 0) and (num > 0):
            print("Aggregated {:,} subjects".format(num))
        # initialize Counter objects
        stat_all = defaultdict(Counter)
        stat_species_only = defaultdict(Counter)
        # extract and add annotations to stats counters
        for annotation in subject_data:
            anno_dict = {annotation_id_to_name_mapper[i]: x for
                         i, x in enumerate(annotation)}
            for k, v in anno_dict.items():
                stat_all[k].update({v})
            # store species only answers
            main_answer = anno_dict[question_main_id]
            if main_answer != flags['QUESTION_MAIN_EMPTY']:
                for k, v in anno_dict.items():
                    stat_species_only[k].update({v})
        # median number of species identifications per user
        # if nobody ids a species, set this to 0
        try:
            n_species_ids_per_user_median = int(
                median_high(stat_species_only['user_name'].values()))
        except StatisticsError:
            n_species_ids_per_user_median = 0
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
                annotation_id_to_name_mapper,
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
            consensus_species = [flags['QUESTION_MAIN_EMPTY']]
            pielou = 0
        else:
            species_names_no_empty = [
                x for x in species_names_by_frequency
                if x != flags['QUESTION_MAIN_EMPTY']]
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
        subject_species_aggregations[subject_id] = record

    # Create one record per identification
    subject_identificatons = list()
    for subject_id, subject_agg_data in subject_species_aggregations.items():
        # export each species
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

    ######################################
    # Generate Stats
    ######################################

    question_stats = defaultdict(Counter)
    question_stats_plurality = defaultdict(Counter)
    subject_stats = dict()
    classifications_per_subject_stats = Counter()
    for _id in subject_identificatons:
        plurality = _id['species_is_plurality_consensus']
        user_classifications = _id['n_users_classified_this_subject']
        subject_id = _id['subject_id']
        for question in questions:
            try:
                if 'count' in question:
                    answer = _id[question]
                else:
                    answer = int(round(float(_id[question]), 0))
            except:
                answer = _id[question]
            if plurality == 1:
                question_stats_plurality[question].update({answer})
            question_stats[question].update({answer})
        subject_stats[subject_id] = user_classifications

    for n_class in subject_stats.values():
        classifications_per_subject_stats.update({n_class})

    # Print Stats per Question - Plurality Consensus Answers Only
    for question, answer_data in question_stats_plurality.items():
        logger.info("Stats for: {} - Plurality Consensus Only".format(question))
        total = sum([x for x in answer_data.values()])
        for answer, count in answer_data.most_common():
            logger.info("Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                answer, count, total, 100*count/total))

    # Print Stats per Question - All Answers
    for question, answer_data in question_stats.items():
        logger.info("Stats for: {} - All annotations per subject".format(question))
        total = sum([x for x in answer_data.values()])
        for answer, count in answer_data.most_common():
            logger.info("Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                answer, count, total, 100*count/total))

    total = sum([x for x in classifications_per_subject_stats.values()])
    for n_classifications, count in classifications_per_subject_stats.items():
        logger.info("Number of Classifications per Subject: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
            n_classifications, count, total, 100*count/total))

    output_header = list(record.keys())

    logger.info("Automatically generated output header: {}".format(
        output_header))

    # Output all Species
    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(output_header)
        tot = len(subject_identificatons)
        for line_no, record in enumerate(subject_identificatons):
            # skip record if no plurality consensus species
            if args['export_consensus_only']:
                if record['species_is_plurality_consensus'] == 0:
                    continue
            # get subject info data
            to_write = [record[x] for x in output_header]
            csv_writer.writerow(to_write)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} identifications".format(line_no))
        logger.info("Wrote {} aggregations to {}".format(
            line_no, args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
