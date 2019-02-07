""" Functions to help aggregate Zooniverse classifications """
from statistics import median_high
from collections import Counter, defaultdict


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
        species_field):
    """ Calculate stats for specific species accross all classifications of a
        Subject
    """
    stat_species = dict()
    for annotation in subject_data:
        anno_dict = {
            row_id_to_name_mapper[i]: x
            for i, x in enumerate(annotation)}
        species = anno_dict[species_field]
        if species in species_list:
            if species not in stat_species:
                stat_species[species] = defaultdict(Counter)
            for k, v in anno_dict.items():
                stat_species[species][k].update({v})
    return stat_species
