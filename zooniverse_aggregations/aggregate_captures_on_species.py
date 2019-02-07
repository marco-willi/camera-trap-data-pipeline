""" Aggregate Zooniverse Classifications to obtain
    Labels for Subjects using the Plurality Algorithm
"""
import csv
import os
import argparse
from statistics import median_high
from collections import Counter, defaultdict
import logging

from logger import setup_logger, create_logfile_name
from zooniverse_exports import extractor
from global_vars import aggregation_flags as flags
from utils import print_nested_dict

# args = dict()
# args['classifications_extracted'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_subjects.csv'
#
# args = dict()
# args['classifications_extracted'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/SER/SER_S1_classifications_aggregated_v2.csv'
# args['subject_csv'] = None
#
# args = dict()
# args['classifications_extracted'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_subjects.csv'
#
# args = dict()
# args['classifications_extracted'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications_extracted.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications_aggregated.csv'
# args['subject_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_subjects.csv'

if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--classifications_extracted", type=str, required=True,
        help="Path to extracted classifications")
    parser.add_argument(
        "--output_csv", type=str, required=True,
        help="Path to file to store aggregated classifications.")
    parser.add_argument(
        "--subject_csv", type=str, default=None,
        help="Path to Zooniverse subject csv export.")
    parser.add_argument(
        "--export_consensus_only", action="store_true",
        help="Export only species with plurality consensus")

    args = vars(parser.parse_args())

    ######################################
    # Configuration
    ######################################

    # logging
    log_file_name = create_logfile_name('aggregate_classifications')
    log_file_path = os.path.join(
        os.path.dirname(args['output_csv']), log_file_name)
    setup_logger(log_file_path)
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

    # Read Annotations and associate with subject id
    subject_annotations = dict()
    with open(args['classifications_extracted'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        questions = [x for x in header if x.startswith(question_column_prefix)]
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} annotations".format(line_no))
            # store data into subject dict
            subject_id = line[row_name_to_id_mapper['subject_id']]
            if subject_id not in subject_annotations:
                subject_annotations[subject_id] = list()
            subject_annotations[subject_id].append(line)

    annotation_id_to_name_mapper = {
        v: k for k, v in row_name_to_id_mapper.items()}

    # get subject-level information
    subject_info = dict()
    for subject_id, annotations in subject_annotations.items():
        # get subject-level information
        subject_data_list = annotations[0]
        subject_info[subject_id] = dict()
        for sub_info in flags['SUBJECT_INFO_TO_ADD']:
            try:
                subject_info[subject_id][sub_info] = \
                    subject_data_list[row_name_to_id_mapper[sub_info]]
            except:
                subject_info[subject_id][sub_info] = ''

    # Add subject information
    # Read Annotations and associate with subject id
    if args['subject_csv'] is not None:
        n_images_per_subject = list()
        with open(args['subject_csv'], "r") as ins:
            csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
            header = next(csv_reader)
            row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
            for line_no, line in enumerate(csv_reader):
                subject_id = line[row_name_to_id_mapper['subject_id']]
                locations_dict = extractor.extract_key_from_json(
                    line, 'locations', row_name_to_id_mapper)
                if subject_id in subject_info:
                    for i, (img_name, url) in enumerate(locations_dict.items()):
                            subject_info[subject_id]['url{}'.format(i+1)] = url
                else:
                    logger.debug("Subject {} has no classifications".format(
                        subject_id))
                n_images_per_subject.append(i+1)
        max_images_per_subject = max(n_images_per_subject)
        url_keys = ['url{}'.format(i+1) for i in range(max_images_per_subject)]
        for subject_id, subject_data in subject_info.items():
            for url_key in url_keys:
                if url_key not in subject_data:
                    subject_data[url_key] = ''

    # question type mapper
    def create_question_type_map(questions, flags):
        """ Map Question Types """
        question_type_map = dict()
        for question in questions:
            if any([x in question for x in flags['QUESTION_COUNTS']]):
                question_type_map[question] = 'count'
            elif flags['QUESTION_MAIN'] in question:
                question_type_map[question] = 'main'
            else:
                question_type_map[question] = 'prop'
        return question_type_map

    def count_aggregator_median(count_stats, flags):
        """ Special count aggregator
        Input:
            - count_stats: {'10-50': 3, '1': 5, '2': 3}
            - counts_mapper: {'10-50': 11, '51+': 12}
        Output:
            - '2'
        """
        counts_mapper = flags['COUNTS_TO_ORDINAL_MAPPER']
        count_values = []
        for count, n_votes in count_stats.items():
            if count in counts_mapper:
                count_values += [int(counts_mapper[count])] * n_votes
            elif count is not '':
                count_values += [int(count)] * n_votes
            else:
                pass
        if len(count_values) == 0:
            return ''
        med = median_high(count_values)
        # unmap value if it was mapped in the first place
        if med in counts_mapper.values():
            counts_unmapping = {v: k for k, v in counts_mapper.items()}
            return counts_unmapping[med]
        else:
            return str(med)

    def proportion_affirmative(question_stats):
        """ Calculate proportion of true/affirmative answers """
        true = question_stats['1']
        no_answer = question_stats['']
        tot = sum(question_stats.values())
        # if nobody answered this question return an empty string to indicate
        # this question was not asked
        if no_answer == tot:
            return ''
        try:
            return '{:.2f}'.format(true / tot)
        except ZeroDivisionError:
            return '0'
        except:
            raise ValueError("Error trying to divide {} by {}".format(
                true, tot))

    def stats_for_species(
            species_list, subject_data,
            row_id_to_name_mapper,
            species_field='question__species'
            ):
        stat_species = dict()
        for annotation in subject_data:
            anno_dict = {row_id_to_name_mapper[i]: x for i, x in enumerate(annotation)}
            species = anno_dict[species_field]
            if species in species_list:
                if species not in stat_species:
                    stat_species[species] = defaultdict(Counter)
                for k, v in anno_dict.items():
                    stat_species[species][k].update({v})
        return stat_species

    question_type_map = create_question_type_map(
        questions, flags)

    # Aggregate subjects
    subject_species_aggregations = dict()
    for num, (subject_id, subject_data) in enumerate(subject_annotations.items()):
        # print status
        if ((num % 10000) == 0) and (num > 0):
            print("Aggregated {:,} subjects".format(num))
        # initialize Counter objects
        stat_all = defaultdict(Counter)
        # extract and add annotations to stats counters
        for annotation in subject_data:
            anno_dict = {annotation_id_to_name_mapper[i]: x for
                         i, x in enumerate(annotation)}
            for k, v in anno_dict.items():
                stat_all[k].update({v})
        # extract some stats
        n_species_ids_per_user_median = int(median_high(stat_all['user_name'].values()))
        n_subject_classifications = len(stat_all['classification_id'])
        n_subject_users = len(stat_all['user_name'])
        # order species by frequency of annotation
        species_by_frequency = stat_all['question__species'].most_common()
        species_names = [x[0] for x in species_by_frequency]
        # calc stats for the top-species only
        species_stats = stats_for_species(
                species_names, subject_data,
                annotation_id_to_name_mapper,
                species_field=question_main_id
                )
        # Aggregate stats for each species
        species_aggs = {x: dict() for x in species_names}
        for species, stats in species_stats.items():
            for question in questions:
                question_type = question_type_map[question]
                if question_type == 'count':
                    agg = count_aggregator_median(stats[question], flags)
                elif question_type == 'prop':
                    agg = proportion_affirmative(stats[question])
                elif question_type == 'main':
                    continue
                species_aggs[species][question] = agg
            # add overall species stats
            species_aggs[species]['n_users_identified_this_species'] = \
                len(stats['classification_id'])
            n_user_id = species_aggs[species]['n_users_identified_this_species']
            p_user_id = '{:.2f}'.format(n_user_id / n_subject_classifications)
            species_aggs[species]['p_users_identified_this_species'] = p_user_id
        # Determine top / consensus species
        top_species = [
            species_names[i] for i in
            range(n_species_ids_per_user_median)]
        # add info to dict
        agg_info = {'n_species_ids_per_user_median': n_species_ids_per_user_median,
                    'n_users_classified_this_subject': n_subject_users}
        record = {'species_aggregations': species_aggs,
                  'aggregation_info': agg_info,
                  'top_species': top_species}
        subject_species_aggregations[subject_id] = record

    # Create a record per identification
    subject_identificatons = list()
    for subject_id, subject_agg_data in subject_species_aggregations.items():
        # export each species
        for sp, species_dat in subject_agg_data['species_aggregations'].items():
            species_is_plurality_consensus = \
                int(sp in subject_agg_data['top_species'])
            record = {
                **subject_info[subject_id],
                question_main_id: sp,
                **species_dat,
                **subject_agg_data['aggregation_info'],
                'species_is_plurality_consensus': species_is_plurality_consensus}
            subject_identificatons.append(record)

    # Generate Stats
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
    for question, answer_data in question_stats_plurality.items():
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
                if record['species_is_plurality_consensus'] == '0':
                    continue
            # get subject info data
            to_write = [record[x] for x in output_header]
            csv_writer.writerow(to_write)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} identifications".format(line_no))
        logger.info("Wrote {} records to {}".format(
            line_no, args['output_csv']))

    output_csv_path, output_csv_name = os.path.split(args['output_csv'])
    output_csv_basename = output_csv_name.split('.csv')
    output_csv_sample = os.path.join(
        output_csv_path, output_csv_basename[0] + '_samples.csv')

    with open(output_csv_sample, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(output_csv_sample))
        csv_writer.writerow(output_header)
        tot = len(subject_identificatons)
        for line_no, record in enumerate(subject_identificatons):
            # skip record if no plurality consensus species
            if args['export_consensus_only']:
                if record['species_is_plurality_consensus'] == '0':
                    continue
            # get subject info data
            to_write = [record[x] for x in output_header]
            if (line_no % 100) == 0:
                csv_writer.writerow(to_write)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Wrote {:,} identifications".format(line_no))
        logger.info("Wrote {} records to {}".format(
            line_no, output_csv_sample))

# # Output Consensus Only
# with open(args['output_consensus_csv'], 'w') as f:
#     csv_writer = csv.writer(f, delimiter=',')
#     logger.info("Writing output to {}".format(args['output_consensus_csv']))
#     csv_writer.writerow(output_header)
#     tot = len(subject_identificatons)
#     for line_no, record in enumerate(subject_identificatons):
#         # skip record if no plurality consensus species
#         if record['species_is_plurality_consensus'] == '0':
#             continue
#         # get subject info data
#         to_write = [record[x] for x in output_header]
#         csv_writer.writerow(to_write)
#         # print status
#         if ((line_no % 10000) == 0) and (line_no > 0):
#             print("Wrote {:,} identifications".format(line_no))
#     logger.info("Wrote {} records to {}".format(
#         line_no, args['output_consensus_csv']))

# To assess the accuracy of aggregated classifications, we calculated an evenness#
# index, using all non-blank classifications for each image set.
# When all classifications were in agreement, we assigned the value zero,
# indicating high accuracy. Otherwise, we used Pielou’s evenness index (Pielou 1966), calculated as:
# - ΣS i¼1pi ln pi =ln S, where S is the number of different species chosen among all volunteers,
# and pi is the proportion of ‘votes’ that species i received. The Pielou evenness index ranges from 0 to 1, with 0 indicating low evenness and high accuracy and 1 indicating high evenness and low accuracy. Note that
# ??
# the Pielou evenness index is expected to be high for image sets with multiple species and therefore is not a useful
#


# count number of blanks and species
# count number of species (ignoring blanks)
# take median number of species
# count vote talles for each species
# calc pielou
# choose top N species
# output row for each top N species
# ignore blanks in that setting

# choose a random species on ties
# choose median counts round up (gotta choose one or the other)
# medind = int(math.ceil((len(sorted_list)+1)/2)-1)
# calculate proportion of binary

# Calculate the Pielou Evenness Index
# Input: a list giving the distribution of votes
# Output: the Pielou Evenness Index or 0 for unanimous vote
# def calculate_pielou(nlist):
#     if len(nlist)<2:
#         return 0
#     # denominator
#     lnS = math.log(len(nlist))
#     # numerator
#     sumlist = sum(nlist)
#     plist = [float(n)/sumlist for n in nlist]
#     plnplist = [n * math.log(n) for n in plist]
#     sumplnp = -sum(plnplist)
#     return sumplnp/lnS
