import os
from collections import OrderedDict, Counter


def find_dirs(path):
    """ Return full path of directories in path """
    all_files = os.listdir(path)
    return [x for x in all_files if os.path.isdir(os.path.join(path, x))]


def find_files(path):
    """ Return full paths of all files in path """
    all_files = os.listdir(path)
    return [x for x in all_files if os.path.isfile(os.path.join(path, x))]


def find_all_reports(root_path, report_postfix='_report.csv'):
    """ Find all Reports """
    reports = OrderedDict()
    sites = find_dirs(root_path)
    for site in sites:
        site_files = find_files(os.path.join(root_path, site))
        report_files = [x for x in site_files if x.endswith(report_postfix)]
        for report in report_files:
            season_id, _ = report.split(report_postfix)
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
