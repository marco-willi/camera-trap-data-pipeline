""" Define global variables for use in other codes """


label_mappings = {
    # Old Snapshot Serengeti (S1-6) label mapping
    'old_ser_label_mapping': {
         'AARDVARK': 0, 'AARDWOLF': 1, 'BABOON': 2,
         'BATEAREDFOX': 3, 'BUFFALO': 4, 'BUSHBUCK': 5, 'CARACAL': 6,
         'CHEETAH': 7,
         'CIVET': 8, 'DIKDIK': 9, 'ELAND': 10, 'ELEPHANT': 11,
         'GAZELLEGRANTS': 12, 'GAZELLETHOMSONS': 13, 'GENET': 14,
         'GIRAFFE': 15,
         'GUINEAFOWL': 16, 'HARE': 17, 'HARTEBEEST': 18,
         'HIPPOPOTAMUS': 19,
         'HONEYBADGER': 20, 'HUMAN': 21, 'HYENASPOTTED': 22,
         'HYENASTRIPED': 23,
         'IMPALA': 24, 'JACKAL': 25, 'KORIBUSTARD': 26, 'LEOPARD': 27,
         'LIONFEMALE': 28, 'LIONMALE': 29, 'MONGOOSE': 30, 'OSTRICH': 31,
         'BIRDOTHER': 32, 'PORCUPINE': 33, 'REEDBUCK': 34, 'REPTILES': 35,
         'RHINOCEROS': 36, 'RODENTS': 37, 'SECRETARYBIRD': 38, 'SERVAL': 39,
         'TOPI': 40, 'MONKEYVERVET': 41, 'WARTHOG': 42, 'WATERBUCK': 43,
         'WILDCAT': 44, 'WILDEBEEST': 45, 'ZEBRA': 46, 'ZORILLA': 47},
    'counts_to_numeric': {"1": 0, "2": 1, "3": 2, "4": 3,
                          "5": 4, "6": 5, "7": 6, "8": 7, "9": 8,
                          "10": 9, "1150": 10, "51": 11},
    'counts_db_to_ml': {"0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
                        "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
                        "10": "10", "11": "11-50", "1150": "11-50", "51": "51+"}
}


###################################################
# Pre-Processing Flags
###################################################

pre_processing_flags = dict()
pre_processing_flags['general'] = {
    'capture_delta_seconds': 5}
pre_processing_flags['image_checks_basic'] = [
    'all_black',
    'all_white',
    'corrupt_file',
    'corrupt_exif',
    'empty_exif']

pre_processing_flags['image_checks_time'] = [
    'time_lapse',
    'time_too_new',
    'time_too_old',
    'captures_with_too_many_images']

pre_processing_flags['image_checks'] = \
    pre_processing_flags['image_checks_basic'] + \
    pre_processing_flags['image_checks_time']

pre_processing_flags['image_check_parameters'] = {
    'all_black': {'thresh': 30, 'percent': 0.8},
    'all_white': {'thresh': 200, 'percent': 0.8},
    'time_lapse_days': {'max_days': 30},
    'time_too_new': {'max_year': 2018},
    'time_too_old': {'min_year': 2012},
    'captures_with_too_many_images': {'max_images': 3}
}
pre_processing_flags['exif_data_timestamps'] = \
        ['DateTime', 'DateTimeOriginal']
pre_processing_flags['time_formats'] = {
        'output_datetime_format': '%Y-%m-%d %H:%M:%S',
        'output_date_format': '%Y-%m-%d',
        'output_time_format': '%H:%M:%S',
        'exif_input_datetime_format': '%Y:%m:%d %H:%M:%S'
}

flags = pre_processing_flags


###################################################
# GLobal Processing Flags
###################################################

global_processing_flags = dict()
global_processing_flags['QUESTION_PREFIX'] = 'question'
global_processing_flags['QUESTION_DELIMITER'] = '__'
global_processing_flags['EMPTY_ANNOTATION'] = 'blank'

###################################################
# Flags to define the bheavior of the Extractor
###################################################

extractor_flags = dict()

# Prefix each question in the output with the following prefix and delim
# Example: 'question__young_present' instead of 'young_present'
extractor_flags['QUESTION_PREFIX'] = global_processing_flags['QUESTION_PREFIX']
extractor_flags['QUESTION_DELIMITER'] = \
    global_processing_flags['QUESTION_DELIMITER']

# map the following question names
extractor_flags['QUESTION_NAME_MAPPER'] = {
    'howmany': 'count',
    'question': 'species',
    'arethereanyyoungpresent': 'young_present',
    'doyouseeanyhorns': 'horns_visible',
    'choice': 'species',
    'doyouseeanyantlers': 'antlers_visible',
    'howmanyanimalscanyouseethathavehorns': 'horns_count'
    }

# Map specific answers of specific questions
extractor_flags['ANSWER_TYPE_MAPPER'] = {
    'species': {
        'no animals present': global_processing_flags['EMPTY_ANNOTATION'],
        'nothing': global_processing_flags['EMPTY_ANNOTATION'],
        'nothinghere': global_processing_flags['EMPTY_ANNOTATION'],
        'nothingthere': global_processing_flags['EMPTY_ANNOTATION'],
        'noanimalspresent': global_processing_flags['EMPTY_ANNOTATION']
        }
    }

# Mapping answers to any question according to the following
extractor_flags['ANSWER_MAPPER'] = {
    'yes': '1', 'y': '1', 'no': '0', 'n': '0',
    0: '0', 1: '1'}

# questions to ignore in the export
extractor_flags['QUESTIONS_TO_IGNORE'] = ('dontcare')

# classification level fields to add to the export
extractor_flags['CLASSIFICATION_INFO_TO_ADD'] = [
    'user_name', 'user_id', 'created_at', 'subject_ids',
    'workflow_id', 'workflow_version', 'classification_id']

# map classification level info
extractor_flags['CLASSIFICATION_INFO_MAPPER'] = {
    'subject_ids': 'subject_id'
}

# add retirement information if available
extractor_flags['RETIREMENT_INFO_TO_ADD'] = [
    "retirement_reason",
    "retired_at"
    ]

###################################################
# Flags to define the bheavior of the
# Legacy Extractor
###################################################

legacy_extractor_flags = dict()

legacy_extractor_flags['QUESTION_PREFIX'] = global_processing_flags['QUESTION_PREFIX']
legacy_extractor_flags['QUESTION_DELIMITER'] = global_processing_flags['QUESTION_DELIMITER']

legacy_extractor_flags['QUESTIONS'] = (
    'species', 'count', 'standing',
    'resting', 'moving', 'eating', 'interacting', 'young_present')

# map column names of the input csv for clarity and consistency
legacy_extractor_flags['CSV_HEADER_MAPPER'] = {
    'id': 'classification_id',
    'subject_zooniverse_id': 'subject_id',
    "species_count": 'count',
    "babies": 'young_present',
    "retire_reason": 'retirement_reason'
    }

# map different answers to the question columns
legacy_extractor_flags['ANSWER_TYPE_MAPPER'] = {
    'species': {
        'no animals present': global_processing_flags['EMPTY_ANNOTATION'],
        'nothing': global_processing_flags['EMPTY_ANNOTATION'],
        '': global_processing_flags['EMPTY_ANNOTATION']
        },
    'young_present': {
        'false': 0,
        'true': 1
        },
    'standing': {
        'false': 0,
        'true': 1
        },
    'resting': {
        'false': 0,
        'true': 1
        },
    'moving': {
        'false': 0,
        'true': 1
        },
    'eating': {
        'false': 0,
        'true': 1
        },
    'interacting': {
        'false': 0,
        'true': 1
        }
    }

# Define the question columns
legacy_extractor_flags['CSV_QUESTIIONS'] = [
    'species', 'count', 'young_present',
    "standing", "resting", "moving", "eating", "interacting"]

# Columns to export
legacy_extractor_flags['CLASSIFICATION_INFO_TO_ADD'] = [
    'user_name', 'created_at', 'subject_id', 'capture_event_id',
    "retirement_reason", "season", "site", "roll",
    "filenames", "timestamps",
    'classification_id']

# Subject info to add from the legacy classifications export
add_subject_info_flags_legacy = [
    'season', 'roll', 'site', 'capture',
    'retirement_reason', 'retired_at', 'created_at', 'filenames',
    'timestamps', 'capture_id']

###################################################
# Flags to define the bheavior of the
# Plurality Aggregator
###################################################

plurality_aggregation_flags = dict()

# Prefix each question in the output with the following prefix and delim
# Example: 'question__young_present' instead of 'young_present'
plurality_aggregation_flags['QUESTION_PREFIX'] = global_processing_flags['QUESTION_PREFIX']
plurality_aggregation_flags['QUESTION_DELIMITER'] = global_processing_flags['QUESTION_DELIMITER']
plurality_aggregation_flags['QUESTION_MAIN'] = 'species'
plurality_aggregation_flags['QUESTION_MAIN_EMPTY'] = global_processing_flags['EMPTY_ANNOTATION']
plurality_aggregation_flags['QUESTION_COUNTS'] = ['count', 'horns_count']
plurality_aggregation_flags['COUNTS_TO_ORDINAL_MAPPER'] = {
    '11-50': 11, '51+': 12, '': 0}

###################################################
# Flags to define the bheavior of adding
# Subject Info
###################################################

add_subject_info_flags = dict()

add_subject_info_flags['SUBJECT_METADATA_TO_ADD'] = [
    'season', 'roll', 'site', 'capture']

add_subject_info_flags['SUBJECT_DATA_TO_ADD'] = [
    'retirement_reason', 'retired_at', 'created_at']

add_subject_info_flags['SUBJECT_INFO_MAPPER'] = {
    '#season': 'season', '#site': 'site',
    '#roll': 'roll', '#capture': 'capture'}

###################################################
# Subject Extractor
###################################################

subject_extractor_flags = dict()

subject_extractor_flags['SUBJECT_ADD_LOCATION_DATA'] = True

subject_extractor_flags['SUBJECT_METADATA_TO_ADD'] = [
    '#season', '#roll', '#site', '#capture']

subject_extractor_flags['SUBJECT_DATA_TO_ADD'] = [
    'retirement_reason', 'retired_at', 'created_at']

subject_extractor_flags['SUBJECT_METADATA_NAME_MAPPER'] = {
    '#season': 'season', '#site': 'site',
    '#roll': 'roll', '#capture': 'capture'}
