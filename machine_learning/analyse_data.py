""" Analyse Consensus Data wrt all possible answers over all projects """
import pandas as pd
from collections import Counter, OrderedDict
import os

from config.cfg import cfg
from utils import set_file_permission

plurality_aggregation_flags = cfg['plurality_aggregation_flags']


def find_dirs(path):
    """ Return full path of directories in path """
    all_files = os.listdir(path)
    return [x for x in all_files if os.path.isdir(os.path.join(path, x))]


def find_files(path):
    """ Return full paths of all files in path """
    all_files = os.listdir(path)
    return [x for x in all_files if os.path.isfile(os.path.join(path, x))]


def find_all_reports(root_path):
    """ Find all Reports """
    reports = OrderedDict()
    sites = find_dirs(root_path)
    for site in sites:
        site_files = find_files(os.path.join(root_path, site))
        report_files = [x for x in site_files if x.endswith('_report.csv')]
        for report in report_files:
            season_id, _ = report.split('_report.csv')
            if season_id in reports:
                print("Warning report {} with id {} already found".format(
                    report, season_id))
            reports[season_id] = os.path.join(root_path, site, report_files[0])
    return reports


def get_question_stats(df_report, non_binary_questions):
    question_cols = [x for x in df_report.columns if x.startswith('question__')]
    question_stats = dict()
    for question in question_cols:
        is_non_binary = any([x in question for x in non_binary_questions])
        if is_non_binary:
            question_stats[question] = Counter(df_report[question])
        else:
            rounded = [int(float(x) + 0.5) if x is not '' else '' for x in df_report[question]]
            question_stats[question] = Counter(rounded)
    return question_stats



output_csv = '/home/packerc/shared/machine_learning/data/meta_data/label_overview_all.csv'
root_path = '/home/packerc/shared/zooniverse/ConsensusReports/'

counts_questions = plurality_aggregation_flags['QUESTION_COUNTS']
non_binary_questions = counts_questions + [plurality_aggregation_flags['QUESTION_MAIN']]

reports = find_all_reports(root_path)

stats_list = []
for season_id, path_report in reports.items():
    location, season = season_id.split('_')
    path_cleaned = '/home/packerc/shared/season_captures/{}/cleaned/{}_cleaned.csv'.format(location, season_id)
    df_report = pd.read_csv(path_report, dtype='str', index_col=None)
    df_report.fillna('', inplace=True)
    question_stats = get_question_stats(df_report, non_binary_questions)
    for question, question_answers in question_stats.items():
        for question_answer in question_answers.keys():
            stats_list.append([location, season, question, question_answer])


df_stats = pd.DataFrame(stats_list)
df_stats.columns = ['location', 'season', 'question', 'answer']

# export df
df_stats.to_csv(output_csv, index=False)

set_file_permission(output_csv)
