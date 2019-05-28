""" Extract Zooniverse Classifications
    - Extract annotations from classifications
    - Export to csv file
        Output Example Header:
            user_name,user_id,created_at,subject_id,workflow_id,
            workflow_version,
            classification_id,retirement_reason,retired_at,question__count,
            question__eating,question__interacting,question__moving,
            question__resting,question__standing,question__young_present,
            question__species,question__horns_visible
        Output Example Record:
            not-logged-in-4ee662baaa306798b359,,2018-02-06 17:09:43 UTC,
            17530583,4979,275.13,88921948,consensus,2018-11-21T19:16:34.362Z,
            4,0,1,0,0,1,1,wildebeest,
"""
import csv
from collections import Counter, defaultdict
import traceback
import os
import argparse
import logging
import textwrap
import json

from utils.logger import set_logging
from zooniverse_exports import extractor
from utils.utils import print_nested_dict, set_file_permission
from config.cfg import cfg


flags = cfg['extractor_flags']
flags_global = cfg['global_processing_flags']
logger = logging.getLogger(__name__)

# # Cedar Creek
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/CC/CC_S1_classifications_extracted_v2.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
#
#
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted_v2.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
#
# args = dict()
# args['classification_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_classifications.csv'
# args['output_csv'] = '/home/packerc/shared/zooniverse/Exports/MTZ/MTZ_S1_annotations_test.csv'
# args['workflow_id'] = None
# args['workflow_version'] = None
# args['workflow_version_min'] = None


def extract_raw_classification(
        cls_dict,
        args,
        stats):
    """ Extract data from raw classifications
        cls_dict: dict of raw classification
        args: dict with configuration
        stats: Counter object to track stats
    """
    extracted_annotations = list()
    # extract classification-level info
    classification_info = {
        x: cls_dict[x] for x in flags['CLASSIFICATION_INFO_TO_ADD']}
    # map classification info header
    classification_info = extractor.rename_dict_keys(
        classification_info, flags['CLASSIFICATION_INFO_MAPPER'])
    # get all annotations (list of annotations)
    annotations_list = json.loads(cls_dict['annotations'])
    # get all tasks of an annotation
    classification_answers = list()
    for task in annotations_list:
        if not extractor.task_is_completed(task):
            stats.update({'n_incomplete_tasks'})
            continue
        task_type = extractor.identify_task_type(task)
        ids_or_answers = extractor.extract_task_info(
            task, task_type, flags)
        # get all identifications/answers of a task
        for _id_answer in ids_or_answers:
            _id_answer_mapped = extractor.map_task_questions(
                _id_answer, flags)
            classification_answers.append(_id_answer_mapped)
    # de-duplicate answers (example: two identical species
    # annotations from different tasks)
    classifications_deduplicated = extractor.deduplicate_answers(
            classification_answers, flags)
    for classification_answer in classifications_deduplicated:
        record = {**classification_info, 'annos': classification_answer}
        extracted_annotations.append(record)
    return extracted_annotations


if __name__ == '__main__':

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--classification_csv", type=str, required=True)
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--log_dir", type=str, default=None)
    parser.add_argument(
        "--log_filename", type=str,
        default='extract_annotations')
    parser.add_argument("--filter_by_season", type=str, default='')
    parser.add_argument(
        "--workflow_id", type=str, default=None,
        help="Extract only classifications from the specified workflow_id")
    parser.add_argument(
        "--workflow_version_min", type=str, default=None,
        help="Extract only classifications with at least the specified \
        workflow version number \
        version. Only the major version number is compared, e.g., \
        version 45.12 is identical to 45.45")
    parser.add_argument(
        "--no_earlier_than_date", type=str, default=None,
        help="Extract only classifications that are no earlier than the \
              specified date -- must be in format YYYY-MM-DD")
    parser.add_argument(
        "--no_later_than_date", type=str, default=None,
        help="Extract only classifications that are no later than the \
              specified date -- must be in format YYYY-MM-DD")
    parser.add_argument(
        "--include_non_live_classifications",
        action='store_true',
        help="Wherther to include classifications that were made during \
              the non-live phase of a project")

    args = vars(parser.parse_args())

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

    ######################################
    # Check Input
    ######################################

    if not os.path.isfile(args['classification_csv']):
        raise FileNotFoundError("classification_csv: {} not found".format(
                                args['classification_csv']))

    if args['no_later_than_date'] is not None:
        date = args['no_later_than_date']
        try:
            no_later_than_date = \
              extractor.convert_date_str_to_datetime(date)
        except:
            raise ValueError(
                "'no_later_than_date' must be YYYY-MM-DD, is {}".format(
                    date))
        args['no_later_than_date'] = no_later_than_date

    if args['no_earlier_than_date'] is not None:
        date = args['no_earlier_than_date']
        try:
            no_earlier_than_date = \
              extractor.convert_date_str_to_datetime(date)
        except:
            raise ValueError(
                "'no_earlier_than_date ' must be YYYY-MM-DD, is {}".format(
                    date))
        args['no_earlier_than_date'] = no_earlier_than_date

    ######################################
    # Extract Classifications
    ######################################

    # store all extracted classifications
    all_extracted_classifications = list()

    # keep track of statistics
    stats = Counter()

    with open(args['classification_csv'], "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)

        # keep track of potential duplicates
        duplicate_tracker = set()

        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed {:,} classifications".format(line_no))

            # create dictionary from input line
            cls_dict = {header[i]: x for i, x in enumerate(line)}

            try:
                if not extractor.classification_is_valid(cls_dict):
                    logger.warning(
                        "Classification on line {} not valid, data: {}".format(
                            line_no, cls_dict
                        ))

                if not extractor.is_eligible_workflow(
                        cls_dict,
                        args['workflow_id'],
                        args['workflow_version_min']):
                    stats.update({'n_not_eligible_workflow'})
                    continue

                if not extractor.is_in_date_range(
                        cls_dict,
                        args['no_earlier_than_date'],
                        args['no_later_than_date']):
                    stats.update({'n_not_in_date_range'})
                    continue

                metadata = json.loads(cls_dict['metadata'])
                if not extractor.project_is_live(metadata):
                    if not args['include_non_live_classifications']:
                        stats.update({'project_is_not_live'})
                        continue

                if args['filter_by_season'] != '':
                    subject_data = json.loads(cls_dict['subject_data'])
                    season_id = extractor.get_season_from_subject_data(
                        subject_data, cls_dict['subject_ids'])
                    if season_id != args['filter_by_season']:
                        stats.update({'n_season_does_not_match'})
                        continue

                if extractor.subject_already_seen(cls_dict):
                    msg = "Removed classification_id: {} due to \
                           'seen_before' flag".format(
                         cls_dict['classification_id'])
                    logger.debug(textwrap.shorten(msg, width=99))
                    stats.update({'n_seen_before'})
                    continue

                if extractor.classification_is_duplicate(
                        cls_dict, duplicate_tracker):
                    # generate logging message
                    msg = "Removed classification_id: {} is duplicate".format(
                           cls_dict['classification_id'])
                    logger.debug(textwrap.shorten(msg, width=150))
                    stats.update({'n_duplicate_classifications_removed'})
                    continue

                extracted_classification = extract_raw_classification(
                    cls_dict, args, stats)

            except Exception:
                logger.warning(
                    "Failed to extract classification number {}".format(
                        line_no
                    ))
                logger.warning(
                    "Full data {}".format(
                        cls_dict
                    ))
                logger.warning(traceback.format_exc())
                stats.update({'n_exceptions'})

            all_extracted_classifications += extracted_classification

    # print statistics
    logger.info("Processed {:,} classifications".format(line_no))
    logger.info("Extracted {:,} identifications".format(
        len(all_extracted_classifications)))

    for stats_name, count in stats.items():
        logger.info('{}: {:,}'.format(stats_name, count))

    ######################################
    # Analyse Classifications
    ######################################

    question_stats = defaultdict(Counter)
    workflow_stats = defaultdict(Counter)
    general_stats = Counter()
    user_stats = Counter()

    for classification in all_extracted_classifications:
        # get annotation information
        for anno in classification['annos']:
            # get question/answer stats
            for question, answers in anno.items():
                if not isinstance(answers, list):
                    question_stats[question].update([answers])
                else:
                    question_stats[question].update(answers)
        try:
            workflow_stats[classification['workflow_id']].update(
                    {classification['workflow_version']}
            )
        except:
            pass
        try:
            not_log = classification['user_name'].startswith('not-logged-in-')
            if classification['user_id'] == '' and not_log:
                general_stats.update({'n_not_logged_in'})
            else:
                user_stats.update({classification['user_name']})
        except:
            pass

    # Print Stats
    logger.info("Found the following questions/tasks: {}".format(
        [x for x in question_stats.keys()]))

    # Stats not-logged-in users
    logger.info("Number of classifications by not logged in users: {}".format(
        general_stats['n_not_logged_in']))

    # print label stats
    for question, answer_data in question_stats.items():
        logger.info("Stats for question: %s" % question)
        total = sum([x for x in answer_data.values()])
        for answer, count in answer_data.most_common():
            logger.info(
                "Answer: {:20} -- counts: {:10} / {} ({:.2f} %)".format(
                 answer, count, total, 100*count/total))

    # workflow stats
    logger.info("Workflow stats:")
    for workflow_id, workflow_version_data in workflow_stats.items():
        for workflow_version, count in workflow_version_data.items():
            logger.info(
                "Workflow id: {:7} Workflow version: {:10} -- counts: {}".format(
                  workflow_id, workflow_version, count))

    logger.info("The top-10 most active users are:")
    for i, (user, count) in enumerate(user_stats.most_common(10)):
        logger.info("Rank {:3} - User: {:20} - Classifications: {}".format(
            i+1, user, count))

    # get all possible answers to the questions
    question_answer_pairs = extractor.find_question_answer_pairs(
        all_extracted_classifications)

    # analyze the question types
    question_types = extractor.analyze_question_types(
        all_extracted_classifications)

    # build question header for csv export
    question_header = extractor.build_question_header(
        question_answer_pairs, question_types)

    # order questions if possible
    try:
        question_header_first = [
            x for x in flags['QUESTIONS_OUTPUT_ORDER'] if x in question_header]
        question_header_last = [
            x for x in question_header if x not in question_header_first]
        question_header = question_header_first + question_header_last
    except:
        pass

    # modify question column names as specified
    question_header_print = list()
    for question in question_header:
        question_header_print.append(
            flags_global['QUESTION_DELIMITER'].join(
                [flags_global['QUESTION_PREFIX'], question]))

    logger.info("Automatically generated question header: {}".format(
        question_header))

    logger.info("Automatically generated cleaned question header: {}".format(
        question_header_print))

    ######################################
    # Export
    ######################################

    # build full csv header
    classification_header_cols = flags['CLASSIFICATION_INFO_TO_ADD']
    classification_header_cols = [
        flags['CLASSIFICATION_INFO_MAPPER'][x] if x
        in flags['CLASSIFICATION_INFO_MAPPER'] else x for
        x in classification_header_cols]

    header = classification_header_cols + question_header_print

    logger.info("Automatically generated output header: {}".format(
        header))

    with open(args['output_csv'], 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to {}".format(args['output_csv']))
        csv_writer.writerow(header)
        tot = len(all_extracted_classifications)
        for line_no, record in enumerate(all_extracted_classifications):
            # get classification info data
            class_data = [record[x] for x in classification_header_cols]
            # get annotation info data
            answers = extractor.flatten_annotations(
                record['annos'], question_types,  question_answer_pairs)
            answers_ordered = [
                answers[x] if x in answers else '' for x
                in question_header]
            csv_writer.writerow(
                class_data + answers_ordered)
        logger.info("Wrote {} annotations to {}".format(
            line_no+1, args['output_csv']))

    # change permmissions to read/write for group
    set_file_permission(args['output_csv'])
