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
# Flags to define the bheavior of the Extractor
###################################################

extractor_flags = dict()

# Prefix each question in the output with the following prefix and delim
# Example: 'question__young_present' instead of 'young_present'
extractor_flags['QUESTION_PREFIX'] = 'question'
extractor_flags['QUESTION_DELIMITER'] = '__'

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
        'no animals present': 'blank',
        'nothing': 'blank',
        'nothinghere': 'blank',
        'nothingthere': 'blank',
        'noanimalspresent': 'blank'
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

# add subject level information and map if specified
# -if not available it will add an empty string in the output
extractor_flags['SUBJECT_INFO_TO_ADD'] = [
    '#season', '#site', '#roll', '#capture']

extractor_flags['SUBJECT_INFO_MAPPER'] = {
    '#season': 'season', '#site': 'site',
    '#roll': 'roll', '#capture': 'capture'}

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

legacy_extractor_flags['QUESTION_PREFIX'] = 'question'
legacy_extractor_flags['QUESTION_DELIMITER'] = '__'

legacy_extractor_flags['QUESTIONS'] = (
    'species', 'young_present', 'standing',
    'resting', 'moving', 'eating', 'interacting')

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
        'no animals present': 'blank',
        'nothing': 'blank',
        '': 'blank'
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




aggregation_flags = dict()

# Prefix each question in the output with the following prefix and delim
# Example: 'question__young_present' instead of 'young_present'
aggregation_flags['QUESTION_PREFIX'] = 'question'
aggregation_flags['QUESTION_DELIMITER'] = '__'
aggregation_flags['QUESTION_MAIN'] = 'species'
aggregation_flags['QUESTION_MAIN_EMPTY'] = 'blank'
aggregation_flags['QUESTION_COUNTS'] = ['count', 'horns_count']
aggregation_flags['COUNTS_TO_ORDINAL_MAPPER'] = {'10-50': 11, '51+': 12, '': 0}
aggregation_flags['SUBJECT_INFO_TO_ADD'] = [
    'season', 'roll', 'site', 'capture', 'subject_id',
    'retirement_reason', 'retired_at']


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

subject_extractor_flags['SUBJECT_METADATA_TO_ADD'] = [
    '#season', '#roll', '#site', '#capture']

subject_extractor_flags['SUBJECT_DATA_TO_ADD'] = [
    'retirement_reason', 'retired_at', 'created_at']

subject_extractor_flags['SUBJECT_INFO_MAPPER'] = {
    '#season': 'season', '#site': 'site',
    '#roll': 'roll', '#capture': 'capture'}
