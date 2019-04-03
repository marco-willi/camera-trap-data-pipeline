""" Create Input File to Generate Predictions For"""
import os

import pandas as pd

from machine_learning.utils import find_all_reports

root_path = '/home/packerc/shared/machine_learning/data/info_files/'
output_path = '/home/packerc/shared/machine_learning/data/info_files/SNAPSHOT_SAFARI/'
output_type = 'blank_species_balanced'
#output_type = 'species'

reports = find_all_reports(root_path, report_postfix='_data_{}.csv'.format(output_type))

def _append_site_to_image_path(path, site):
    """ Appned site tag to image path """
    if path == '':
        return ''
    try:
        return os.path.join(site, path)
    except Exception as e:
        print(path)
        print(site)
        print(e)
        raise

test_dfs_all = list()
for season_id, path_report in reports.items():
    location, season = season_id.split('_')
    df_data = pd.read_csv(path_report, dtype='str', index_col=None)
    df_data.fillna('', inplace=True)
    df_test = df_data[df_data['split_name'] == 'test_{}_{}'.format(location, season)]
    # adjust image paths
    img_cols = [x for x in df_test.columns if 'image' in x]
    for img in img_cols:
        new_img_col = df_test[img].map(lambda x: _append_site_to_image_path(x, location))
        df_test[img] = new_img_col
    test_dfs_all.append(df_test)

df_all_test = pd.concat(test_dfs_all)
output_path_test_data = os.path.join(output_path, 'SNAPSHOT_SAFARI_data_{}_test.csv'.format(output_type))
df_all_test.to_csv(output_path_test_data, index=False)
