""" Functions to Extract Zooniverse classifications from Oruboros
    - This is the system that contains Snapshot Serengeti S1-S10
      classifications
    - That system is deprecated and the classifications have been fully
      exported
    - This code provides function to process the exported classifications
"""
import csv
import os
from collections import OrderedDict
from collections import Counter
import traceback
import textwrap
import logging

from utils import correct_image_name

logger = logging.getLogger(__name__)


def split_raw_classification_csv(input_csv, output_path):
    """ split raw classification export into season files """
    file_writers = dict()
    file_objects = dict()

    # Split file according to 'season' column
    with open(input_csv, "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            season = line[row_name_to_id_mapper["season"]]
            if season not in file_writers:
                path = os.path.join(
                    output_path,
                    'SER_{}_classifications_raw.csv'.format(season))
                file_objects[season] = open(path, 'w')
                csv_writer = csv.writer(
                    file_objects[season], delimiter=',',
                    quotechar='"', quoting=csv.QUOTE_ALL)
                csv_writer.writerow(header)
                file_writers[season] = csv_writer
            writer = file_writers[season]
            writer.writerow(line)
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed %s annotations" % line_no)

    # close files
    for k, v in file_objects.items():
        v.close()

    return file_writers


def map_task_answers(answers, map):
    """ Map Task Answers
        Input: [{'species': 'NOTHING'}]
        Output: [{'species': 'nothinghere'}]
    """
    if isinstance(answers, str):
        if answers.lower() in map:
            return map[answers]
    elif isinstance(answers, list):
        lower_case = [x.lower() for x in answers]
        mapped = [x if x not in map else map[x] for x in lower_case]
        return mapped
    return answers


def extract_classification_info(line, map, flags):
    """ Extract info on classification level """
    res = {x: line[map[x]] for x in
           flags['CLASSIFICATION_INFO_TO_ADD']}
    return res


def extract_questions(line, map, flags):
    """ Extract info on classification level
    Input:
        - line (list) - CSV line
        - row_name_to_id_mapper (dict) - mapping column name to col id
    Output:
        - dict - questions and answers
    Example:
        - Input:
            ['56bb74735cabfc008e000956', 'matollik', 'ASG001gjr9',
            '59355', '2016-02-10 17:33:39 UTC', 'consensus', 'S1', 'G04',
            'R2', 'S1_G04_R2_PICT2534.JPG;...',
            '2010-09-26 22:57:02 UTC;;', 'zebra', '2', '', '', '', '', '', '']
         - Output:
            {'species': 'zebra', 'count': 2'', 'young_present': '',
             'standing': '', 'resting': '', 'moving': '',
             'eating': '', 'interacting': ''}
    """
    res = {x: line[map[x]] for x in
           flags['CSV_QUESTIIONS']}
    return res


def is_eligible(line, map):
    """ Check whether classification is eligible """
    if line[map['season']] == 'tutorial':
        return False
    return True


def map_answers(answers, map, flags):
    """ Map answers according to ANSWER_TYPE_MAPPER
    Example:
        - input:
            {'species': 'no animals present', ...}
        - output:
            {'species': 'blank', ...}
    """
    # map answers
    for question, answer_map in flags['ANSWER_TYPE_MAPPER'].items():
        if question in map:
            if question not in answers:
                logger.warning("Did not find question {} in answers {}".format(
                    question, answers))
            answer = answers[question]
            if answer in answer_map:
                mapped_answer = answer_map[answer]
                answers[question] = mapped_answer


# check if classification needs to be consolidate
# is the case if more than one annotation was made for the same species
def needs_consolidation(annotations):
    """ Check if a classification needs to be consolidated, which is the case
        if the same species was annotated multiple times
    Example Input:
    ----------------
    [{'species': 'lionFemale', 'count': '1',..},
     {'species': 'lionFemale', 'count': '2', ..},
     {'species': 'wildebeest', 'count': '11-50', ..}]
    """
    if len(annotations) == 1:
        return False
    else:
        species_annotations = {x['species'] for x in annotations}
        if len(species_annotations) == len(annotations):
            return False
        else:
            return True
    logger.warning("Unexpected case in needs_consolidation for annotations {}".format(
        annotations))


def consolidate_annotations(annotations, flags):
    """ Consolidate annotations with identical species annotations
        Example Input:
        ----------------
        [{'species': 'lionFemale', 'count': '1',..},
         {'species': 'lionFemale', 'count': '2', ..},
         {'species': 'wildebeest', 'count': '11-50', ..}]
        Example Output:
        -----------------
        [{'species': 'lionFemale', 'count': '3',..},
         {'species': 'wildebeest', 'count': '11-50', ..}]
    """
    species_counter = Counter([x['species'] for x in annotations])
    # identify the annotations to consolidate for each species
    consolidated_all = list()
    for species, num in species_counter.items():
        to_consolidate = list()
        for annotation in annotations:
            if annotation['species'] == species:
                to_consolidate.append(annotation)
        # no consolidation needed if only one annotation was made for a
        # specific species
        if len(to_consolidate) == 1:
            consolidated_all.append(to_consolidate[0])
            continue
        # do the consolidation
        consolidated = dict()
        for annotation in to_consolidate:
            for entry, value in annotation.items():
                # if field does not need to be consolidated
                # store it as-is
                if entry not in flags['CSV_QUESTIIONS']:
                    consolidated[entry] = value
                # if field needs to be consolidated but is the first
                # one of multiple to be consolidated, store as-is
                elif entry not in consolidated:
                    consolidated[entry] = value
                else:
                    current_value = consolidated[entry]
                    consol_value = consolidate_annotation_values(
                        entry, current_value, value)
                    consolidated[entry] = consol_value
        # add the consolidation of the urrent species
        consolidated_all.append(consolidated)
    return consolidated_all


def consolidate_annotation_values(type, current_value, new_value):
    """ Consolidate annotations for a specific type
    Example 1:
    -------
        -input:('count', '2', '2')
        -output: '3'
    Example 2:
    -------
        -input: (behavior, '1', '0')
        -output: '1'
    """
    # Count consolidation implemented as in previously published dataset
    # (note that 11-50 is given priority over 51+ -- unclear why)
    if type == 'count':
        if any([x == '11-50' for x in (current_value, new_value)]):
            return '11-50'
        if any([x == '51+' for x in (current_value, new_value)]):
            return '51+'
        # for empty images, if species is ''
        if any([x == '' for x in (current_value, new_value)]):
            return ''
        else:
            sum = int(current_value) + int(new_value)
            if sum > 10:
                return '11-50'
            else:
                return str(sum)
    # does not need consolidation
    elif type == 'species':
        return current_value
    # use max-consolidation as standard
    else:
        return max(current_value, new_value)


def fix_roll_id(roll):
    """ Fix Roll IDs - change to format 'R01' (example) """
    if roll.lower().startswith('r'):
        return roll.upper()
    else:
        return 'R{}'.format(roll).upper()


def build_img_path(season, site, roll, img):
    """ build path """
    roll_key = '_'.join([site, fix_roll_id(roll)])
    img_path = os.path.join(season, site, roll_key, img)
    return correct_image_name(img_path)


def build_season_id(season):
    """ Create a season identifier - 'SER_S10' (example) """
    if not season.startswith('SER_S'):
        if not season.startswith('S'):
            season = 'SER_S{}'.format(season)
        else:
            season = 'SER_{}'.format(season)
    return season


def build_capture_id(line, row_name_to_id_mapper):
    """ Build Capture ID - season#site#roll#capture """
    season = line[row_name_to_id_mapper['Season']]
    season = build_season_id(season)
    site = line[row_name_to_id_mapper[' Site']]
    roll = fix_roll_id(line[row_name_to_id_mapper[' Roll']])
    roll_without_R = roll[1:]
    capture = line[row_name_to_id_mapper[' Capture']]
    capture_id = '#'.join([season, site, roll_without_R, capture])
    return capture_id


def build_image_id(line, row_name_to_id_mapper):
    """ Build Image ID - season#site#roll#image_name """
    season = line[row_name_to_id_mapper['Season']]
    season = build_season_id(season)
    site = line[row_name_to_id_mapper[' Site']]
    roll = fix_roll_id(line[row_name_to_id_mapper[' Roll']])
    imgname = line[row_name_to_id_mapper[' PathFilename']]
    image_name = os.path.basename(imgname)
    return '#'.join([season, site, roll, image_name])


def build_img_to_capture_map(path, flags):
    img_to_capture = dict()
    with open(path, 'r') as f:
        csv_reader = csv.reader(f, delimiter=',', quotechar='"')
        header = next(csv_reader)
        # map header
        header = [flags['CSV_HEADER_MAPPER'][x] if x in
                  flags['CSV_HEADER_MAPPER'] else x for x in header]
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed %s annotations" % line_no)
            capture_id = build_capture_id(line, row_name_to_id_mapper)
            img_key = build_image_id(line, row_name_to_id_mapper)
            img_to_capture[img_key] = capture_id
    return img_to_capture


def process_season_classifications(path, img_to_capture, flags):
    """ Process season classifications """
    n_not_eligible = 0
    n_capture_id_not_found = 0
    n_annos_without_images = 0
    n_duplicate_subject_classifications = 0
    user_subject_class = dict()
    classifications = OrderedDict()
    with open(path, "r") as ins:
        csv_reader = csv.reader(ins, delimiter=',', quotechar='"')
        header = next(csv_reader)
        # map header
        header = [flags['CSV_HEADER_MAPPER'][x]
                  if x in flags['CSV_HEADER_MAPPER'] else x for x in header]
        header.append('capture_id')
        row_name_to_id_mapper = {x: i for i, x in enumerate(header)}
        for line_no, line in enumerate(csv_reader):
            # print status
            if ((line_no % 10000) == 0) and (line_no > 0):
                print("Processed %s annotations" % line_no)
            # check eligibility of classification
            if not is_eligible(line, row_name_to_id_mapper):
                n_not_eligible += 1
                continue
            try:
                # extract classification-level info
                classification_info = extract_classification_info(
                    line, row_name_to_id_mapper, flags)
                # build lookup key to get capture id
                season = build_season_id(classification_info['season'])
                image_name = classification_info['filenames'].split(';')[0]
                site = line[row_name_to_id_mapper['site']]
                roll = fix_roll_id(line[row_name_to_id_mapper['roll']])
                img_key = '#'.join([season, site, roll, image_name])
                try:
                    # add full capture_id and capture num
                    capture_id = img_to_capture[img_key]
                    capture = capture_id.split('#')[-1]
                except:
                    if n_capture_id_not_found < 10:
                        logger.info("Did not find img_key: {}".format(img_key))
                    elif n_capture_id_not_found == 10:
                        logger.info("Not printing more not found img_key msgs...")
                    n_capture_id_not_found += 1
                    continue
                    # capture_id = ''
                    # capture = ''
                if len(image_name) == 0:
                    n_annos_without_images += 1
                classification_info['capture_id'] = capture_id
                classification_info['capture'] = capture
                # get answers
                answers = extract_questions(line, row_name_to_id_mapper, flags)
                # map answers
                map_answers(answers, row_name_to_id_mapper, flags)
                # check if subject was already classified by the same user
                # during a different classification, if so skip
                user = classification_info['user_name']
                subject_id = classification_info['subject_id']
                classification_id = classification_info['classification_id']
                user_sub_key = '#'.join([user, subject_id])
                if user_sub_key not in user_subject_class:
                    user_subject_class[user_sub_key] = classification_id
                # check whether there is a previous classification from
                # the same user on the same subject
                if classification_id not in user_subject_class[user_sub_key]:
                    if n_duplicate_subject_classifications < 10:
                        msg = "Removed annnotation due \
                               to subject_id {} already classified by \
                               user {} in a prev classification_id: {} \
                               current classification id: {}".format(
                               subject_id,
                               user,
                               user_subject_class[user_sub_key],
                               classification_id)
                        logger.info(textwrap.shorten(msg, width=250))
                    elif n_duplicate_subject_classifications == 10:
                        logger.info(textwrap.shorten(
                            "not printing any more annotation removal due to \
                             identical user/subjec", width=99))
                    n_duplicate_subject_classifications += 1
                    continue
                record = {**classification_info, **answers}
                # store in classifiations dict
                c_id = classification_info['classification_id']
                if c_id not in classifications:
                    classifications[c_id] = list()
                classifications[c_id].append(record)
            except Exception:
                logger.warning("Error - Skipping Record %s" % line_no)
                logger.warning("Full line:\n %s" % line)
                logger.warning(traceback.format_exc())

    msg = "Removed {} non-eligible annotations".format(n_not_eligible)
    logger.info(textwrap.shorten(msg, width=150))
    msg = "Capture Ids not found - Removed: {} annotations".format(
        n_capture_id_not_found)
    logger.info(textwrap.shorten(msg, width=150))
    msg = "Images not found in season.csv: {}".format(
        n_annos_without_images)
    logger.info(textwrap.shorten(msg, width=150))
    msg = "Removed {} duplicate annotations - same user, subject, \
     but different classification id".format(
     n_duplicate_subject_classifications)
    logger.info(textwrap.shorten(msg, width=150))

    return classifications


def consolidate_all_classifications(classifications, flags):
    """ Consolidate classifications with multiple entries of the same
        species
    """
    consolidated_classifications = dict()
    n_consolidations = 0
    for c_id, annotations in classifications.items():
        if needs_consolidation(annotations):
            try:
                consolidated = consolidate_annotations(annotations, flags)
                consolidated_classifications[c_id] = consolidated
                n_consolidations += 1
            except:
                logger.warning("Failed to consolidate record: {}".format(
                    annotations))

    logger.info("Consolidated {} classifications with multiple entries for \
          the same species".format(n_consolidations))
    return consolidated_classifications


def export_cleaned_annotations(path, classifications, header, flags):
    """ Export Cleaned Annotation """

    # map questions if necessary
    header_to_print = list()
    for col in header:
        if col in flags['QUESTIONS']:
            header_to_print.append(
                flags['QUESTION_DELIMITER'].join(
                    [flags['QUESTION_PREFIX'], col]))
        else:
            header_to_print.append(col)

    with open(path, 'w') as f:
        csv_writer = csv.writer(f, delimiter=',')
        logger.info("Writing output to %s" % path)
        csv_writer.writerow(header_to_print)
        n_annos_written = 0
        for line_no, (_c_id, data) in enumerate(classifications.items()):
            for annotation in data:
                row = [annotation[x] for x in header]
                csv_writer.writerow(row)
                n_annos_written += 1
        logger.info("Wrote {} classifications and {} annotations".format(
            line_no, n_annos_written))
