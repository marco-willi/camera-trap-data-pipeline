""" Analyse Consensus Data wrt all possible answers over all projects """
import pandas as pd

from config.cfg import cfg
from utils import set_file_permission
from machine_learning.utils import find_all_reports, get_question_stats

plurality_aggregation_flags = cfg['plurality_aggregation_flags']


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
