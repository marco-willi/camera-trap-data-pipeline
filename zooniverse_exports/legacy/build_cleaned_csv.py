""" Build Cleaned CSV files -- Logic to:
    - create cleaned season inventories based on multiple data sources
        * LILA/Dryad data (S1-S6)
        * MSI SQL DB data
        * MSI SX_cleaned.csv files
    - specifically:
        * ensure valid/invalid flags are consistent
        * ensure timestamps are consistent and as correct as possible
        * generally, ensure consistency with LILA/Dryad
    - general procedure:
        1. Base files are SX_cleaned.csv for S9-S10, df_db for S1-S8
        2. Ensure everything S1-S6 in LILA dataset is contained
        (3. Add additional captures from S1-S6 if 'include'
            status but not in LILA)
        (4. verify with DB export valid flags)
        (5. verify timestamps LILA and DB export / SX_cleaned)
    - required files:
        1. LILA export (SnapshotSerengeti.json)
        2. DB export (timestamps_db.csv)
        3. SX_cleaned.csv files
"""
import os
import pandas as pd

from utils.utils import sort_df, sort_df_by_capture_id
from zooniverse_exports.legacy.legacy_utils import (
    read_lila, read_db, read_cleaned, print_stats, create_capture_id,
    create_date, create_time, _get_datetime_obj
)


#################################
# Parameters
#################################

root_data_path = '/home/packerc/shared/season_captures/SER/legacy_S1_S10_data/'

path_cleaned = root_data_path
lila_path = os.path.join(root_data_path, 'lila.json')
path_images_db = os.path.join(root_data_path, 'df_db_S1_S8.csv')
path_output = os.path.join(root_data_path, 'cleaned/')

col_mapper = {
    'ZoonID': 'subject_id',
    'idCaptureEvent': 'CaptureEventId',
    'Zooniverse_ID': 'subject_id',
    'ZooniverseIdentifier': 'subject_id',
    'Roll': 'roll_db_id',
    'Season': 'season',
    'Site': 'site_db_id',
    'Capture': 'capture_db_id',
    'GridCell': 'site',
    'RollNumber': 'roll',
    'CaptureEventNum': 'capture'
    }

#################################
# Read Data
#################################

# Read Base Data -- LILA / DB Exports / CLEANED CSV Files
df_lila = read_lila(lila_path)
df_db = read_db(path_images_db, col_mapper)
df_cleaned = read_cleaned(path_cleaned)


#################################
# Look at Stats
#################################

# investigate data
df_db.columns
print_stats(df_db['season'].value_counts())
print_stats(df_db['site'].value_counts())
print_stats(df_db['roll'].value_counts())
print_stats(df_db['SequenceNum'].value_counts())
print_stats(df_db['ZooniverseStatus'].value_counts())
print_stats(df_db['idTimestampStatuses'].value_counts())
print_stats(df_db['StatusDescription'].value_counts())
print_stats(df_db['Invalid'].value_counts())
df_db.groupby(['Invalid', 'season']).size()
df_cleaned.groupby(['include', 'season']).size()
df_cleaned.groupby(['include', 'invalid']).size()
df_db.groupby(['idTimestampStatuses', 'StatusDescription']).size()

# idTimestampStatuses  StatusDescription
# 0                    OK                                        5011159
# 1                    Not recoverable                             25836
# 2                    Fix is hard                                 36392
# 3                    Fix is hard but timestamp likely close      14555

# -> include only for invalid=0


#################################
# Select relevant columns
#################################

df_lila = df_lila[[
    'image_path', 'subject_id', 'season',
    'site', 'datetime', 'species']]

df_db = df_db[[
    'subject_id', 'image_path', 'season',
    'site', 'roll', 'capture', 'SequenceNum',
    'TimestampJPG', 'TimestampFile', 'TimestampAccepted',
    'Invalid', 'idTimestampStatuses', 'StatusDescription']]

df_cleaned = df_cleaned[[
    'newtime', 'oldtime', 'PathFilename', 'roll', 'season', 'site',
    'capture', 'image', 'include', 'invalid']]

# Export to Disk
df_lila.to_csv(os.path.join(root_data_path, 'df_lila.csv'), index=False)
df_db.to_csv(os.path.join(root_data_path, 'df_db.csv'), index=False)
df_cleaned.to_csv(os.path.join(root_data_path, 'df_cleaned.csv'), index=False)

# Read from disk
# df_lila = pd.read_csv(os.path.join(root_data_path, 'df_lila.csv'), index_col=False, dtype=str)
# df_db = pd.read_csv(os.path.join(root_data_path, 'df_db.csv'), index_col=False, dtype=str)
# df_cleaned = pd.read_csv(os.path.join(root_data_path, 'df_cleaned.csv'), index_col=False, dtype=str)
# df_lila.fillna('', inplace=True)
# df_db.fillna('', inplace=True)
# df_cleaned.fillna('', inplace=True)


# create flags
df_cleaned['in_clean'] = '1'
df_db['in_db'] = '1'
df_lila['in_lila'] = '1'


# remove specific images that don't actually exist
def remove_non_existing(df):
    """ Remove images that dont exist """
    i_subset = ~df['image_path'].isin([
        'S1/L10/L10_R1/S1_L10_R1_PICT0004 (2).JPG',
        'S1/L10/L10_R1/S1_L10_R1_PICT0023 (2).JPG',
        'S1/L10/L10_R1/S1_L10_R1_PICT0024 (2).JPG',
        'S1/L10/L10_R1/S1_L10_R1_PICT0025 (2).JPG',
        'S7/G09/G09_R2/S7_G09_R2_P1060627.JPG'])
    return df.loc[i_subset]


df_lila = remove_non_existing(df_lila)
df_db = remove_non_existing(df_db)

#################################
# Merge Data
#################################

# build full data frame
df_merged = pd.merge(
    left=df_db, how='outer',
    right=df_cleaned,
    left_on=['image_path', 'season', 'site', 'roll'],
    right_on=['PathFilename', 'season', 'site', 'roll'],
    suffixes=('_db', '_cleaned'))
df_merged['image_path'] = df_merged['image_path'].fillna(df_merged['PathFilename'])

# create 'capture' column, take 'capture_db', substitute with 'capture_cleaned' if empty
df_merged['capture'] = df_merged['capture_db']
i_replace = (df_merged['capture_db'] == '') | (df_merged['capture_db'].isna())
df_merged['capture'].loc[i_replace] = df_merged['capture_cleaned'].loc[i_replace]

# merge lila data
df_merged2 = pd.merge(
    left=df_merged, how='outer',
    right=df_lila,
    left_on=['image_path', 'season', 'site'],
    right_on=['image_path', 'season', 'site'],
    suffixes=('', '_lila'))
df_merged2.fillna('', inplace=True)

#################################
# Clean Invalid Image Names
#################################

# remove images with either '(' or ')' in image name
i_special_char = df_merged2['image_path'].apply(lambda x: (')' in x) | ('(' in x))

bad_names = list(df_merged2['image_path'].loc[i_special_char])
good_names = [x.replace(' (2)', '') for x in bad_names]
df_merged2['image_path'].loc[i_special_char] = good_names

# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# RENAMING DONE!
# for old, new in zip(bad_names, good_names):
#     root_path = '/home/packerc/shared/albums/SER/'
#     old_path = os.path.join(root_path, old)
#     new_path = os.path.join(root_path, new)
#     try:
#         os.rename(old_path, new_path)
#         print("mv {} to {}".format(old_path, new_path))
#     except:
#         raise


#################################
# Some checks
#################################

df_db.groupby(['season', 'Invalid']).size().to_frame('count').reset_index()
df_merged2.groupby(['season', 'Invalid']).size().to_frame('count').reset_index()
df_merged2.groupby(['season', 'in_clean', 'in_db', 'in_lila']).size().to_frame('count').reset_index()
df_merged2.iloc[0]

# some random checks / comments

# # check investiage discrepancies
# img = 'S1/E02/E02_R5/S1_E02_R5_PICT0148.JPG'
# img = 'S4/B12/B12_R2/S4_B12_R2_IMAG0100.JPG'
# img = 'S5/G07/G07_R4/S5_G07_R4_IMAG0219.JPG'
# df_merged2[df_merged2['image_path'] == img]


# # complete roll missing
# # S4/B12/B12_R2/S4_B12_R2_
# # ASG000euyt, https://static.zooniverse.org/www.snapshotserengeti.org/subjects/standard/50dcd6e6a2fc8e37891057fa_0.jpg
# # SER_S4#B12#2#1,S4,B12,R2,1,
# # 4,B12,2,1
# # is in S4_cleaned.csv with correct time...
# # has invalid=3 flag, therefore, makes sense to be missing in LILA
#
#
# missing_in_cleaned.shape
# missing_in_cleaned.iloc[1]
#
# # 164 captures from S5 missing, S4/S6 are good
# # 464 images missing from S5
# missing_in_cleaned['season_y'].value_counts()
#
# # ASG000pf4u
# # S5/G07/G07_R4/S5_G07_R4_IMAG0219.JPG
# # entire roll S5/G07/G07_R4 missing in S5_cleaned.csv
# # however, is in LILA and DB


# df_merged2[df_merged2['image_rank_in_capture'] == '6']
# df_merged2[df_merged2['subject_id'] == 'ASG000twd2']

#################################
# Handle Different Seasons
#################################

# Build DFs for each season
col_mapper_final = {
    'SequenceNum': 'image_rank_in_capture',
    'image': 'image_rank_in_capture',
    'TimestampJPG': 'datetime_exif',
    'oldtime': 'datetime_exif',
    'TimestampFile': 'datetime_file_creation',
    'TimestampAccepted': 'datetime',
    'newtime': 'datetime',
    'Invalid': 'invalid',
    'image_path': 'image_path_rel',
    'datetime': 'datetime_lila'
    }

season_dfs = list()
for i in range(0, 10):
    season_num = i+1
    df_season = df_merged2[df_merged2['season'] == 'S{}'.format(season_num)].copy()
    # LILA and DB
    if season_num <= 6:
        df_season = df_season[[
            'image_path', 'season', 'site', 'roll', 'capture',
            'SequenceNum', 'TimestampJPG', 'TimestampFile',
            'TimestampAccepted', 'Invalid', 'datetime']]
    # DB
    elif season_num <= 8:
        df_season = df_season[[
            'image_path', 'season', 'site', 'roll', 'capture',
            'SequenceNum', 'TimestampJPG', 'TimestampFile',
            'TimestampAccepted', 'Invalid']]
    # SEASON
    else:
        df_season = df_season[[
            'image_path', 'season', 'site', 'roll', 'capture',
            'image', 'oldtime', 'newtime',
            'include', 'invalid']]
    df_season.rename(columns=col_mapper_final, inplace=True)
    season_dfs.append(df_season)

df_final = pd.concat(season_dfs)
df_final.fillna('', inplace=True)

# final checks
print_stats(df_final['season'].value_counts())
df_final.groupby(['season', 'include', 'invalid']).size().to_frame('count').reset_index()
df_final.groupby(['season', 'invalid']).size().to_frame('count').reset_index()

##########################
# check with LILA data
##########################

tt = df_final[(df_final['datetime_lila'] != df_final['datetime']) & (df_final['datetime_lila'] != '') & (df_final['datetime'] != '') & (df_final['image_rank_in_capture'] == '1')]
tt.shape
#(62, 12) are different

# check LILA invalid flags
tt = pd.merge(
    left=df_final,
    right=df_lila,
    left_on='image_path_rel',
    right_on='image_path',
    how='left',
    suffixes=('', '_lila'))
tt = tt.loc[(tt['season'].isin(['S1', 'S2', 'S3', 'S4', 'S5', 'S6']))]
tt.groupby(['season_lila', 'include', 'invalid']).size().to_frame('count').reset_index()
tt.groupby(['season', 'include', 'invalid']).size().to_frame('count').reset_index()
# -> LILA data had only 'invalid' == 0 records

# -> newtime is mostly 'TimestampAccepted' (small discrepancies for S4, S5 and S6)
print_stats(tt['season'].value_counts())


##################################
# Create Captures DF
##################################

# Problems
# 1) some captures have no time
# 2) some captures have timestampaccepted not on first image in sequence
# 3) some captures have correct timestamp only on first image

# Logic
# 1) take timestamp of first non-empty ordered by sequence num
# 2) leave blank if no timestamp found


# Create capture to timestamp df
# take lila datetime and substitute with 'datetime' if not available
print_stats(df_final['season'].value_counts())
df_capture = df_final.copy()
df_capture['datetime_clean'] = df_capture['datetime_lila']
i_no_lila = (df_capture['datetime_clean'] == '') | (df_capture['datetime_clean'].isna())
df_capture['datetime_clean'].loc[i_no_lila] = df_capture['datetime'].loc[i_no_lila]

# check
# tt = df_capture.drop_duplicates(subset=['season', 'site', 'roll', 'capture'])
# tt[tt['image_rank_in_capture'] != '1']
# df_merged2[(df_merged2['image_path'] == 'S4/B12/B12_R2/S4_B12_R2_IMAG0070.JPG') & (df_merged2['invalid'] == '0')]
#df_captures_first_image[df_captures_first_image['datetime_clean'] == ''][['image_path','SequenceNum']]

# move forward with only datetime_clean (mix of LILA and DB timestamp)
df_capture = df_capture[['season', 'site', 'roll', 'capture', 'datetime_clean']]

# get captures that have at least one non-empty datetime
df_capture_first_with_datetime = df_capture.loc[df_capture['datetime_clean'] != '']
df_capture_first_with_datetime.drop_duplicates(subset=['season', 'site', 'roll', 'capture'], inplace=True)

# get the rest of the captures
df_captures_first_image = df_capture.drop_duplicates(subset=['season', 'site', 'roll', 'capture'])

# df_captures_first_image.iloc[0]
# df_merged2[(df_merged2['season'] == 'S1') &
#  (df_merged2['site'] == 'O05') &
#  (df_merged2['roll'] == '1') &
#  (df_merged2['capture'] == '1171')]
# df_merged2[(df_merged2['season'] == 'S1') &
#  (df_merged2['site'] == 'C06') &
#  (df_merged2['roll'] == '1') &
#  (df_merged2['capture'] == '14')]


# merge both together to find captures without timestamps
df_captures_without_timestamps = pd.merge(
    left=df_captures_first_image,
    right=df_capture_first_with_datetime,
    on=['season', 'site', 'roll', 'capture'],
    how='left',
    suffixes=('', '_f'))
df_captures_without_timestamps = df_captures_without_timestamps[df_captures_without_timestamps['datetime_clean_f'].isna()]

df_captures_without_timestamps.shape[0]
# 10528 captures without timestamps

# combine
df_captures_all = df_capture_first_with_datetime.append(df_captures_without_timestamps[['season', 'site', 'roll', 'capture', 'datetime_clean']])
df_captures_all.shape
df_captures_all.columns

# check
tt = df_captures_all.drop_duplicates(subset=['season', 'site', 'roll', 'capture'])
assert tt.shape[0] == df_captures_all.shape[0]

df_captures_all['capture_id'] = df_captures_all[['season', 'site', 'roll', 'capture']].apply(
    lambda x: create_capture_id(*x), axis=1)

# sort by capture id
sort_df_by_capture_id(df_captures_all)

###########
# checks
###########

tt = pd.merge(left=df_captures_all, right=df_final[['season', 'site', 'roll', 'capture', 'datetime_lila']],
 on=['season', 'site', 'roll', 'capture'],
 how='outer')

# no diffs to LILA datetimes
tt_lila = tt[(~tt['datetime_lila'].isna()) & (tt['datetime_lila'] != '')]
tt_diff = tt_lila[tt_lila['datetime_lila'] != tt_lila['datetime_clean']]
assert tt_diff.shape[0] == 0

# no empty capture ids
assert df_captures_all[df_captures_all['capture_id'] == ''].shape[0] == 0
assert df_captures_all[df_captures_all['capture_id'].isna()].shape[0] == 0

# 10k captures without datetime_clean
no_datetime = df_captures_all[df_captures_all['datetime_clean'] == '']
no_datetime.shape

# Create capture date/time
# df_captures_all['capture_date_local'] = df_captures_all['datetime_clean'].apply(
#     lambda x: create_date(x))
#
# df_captures_all['capture_time_local'] = df_captures_all['datetime_clean'].apply(
#     lambda x: create_time(x))

df_captures_all.columns

df_captures_all.rename(columns={'datetime_clean': 'datetime'}, inplace=True)
df_captures_all = df_captures_all[[
    'capture_id', 'season', 'site', 'roll', 'capture', 'datetime']]

df_captures_all.to_csv(os.path.join(path_output, 'capture_events.csv'), index=False)

#df_captures_all = pd.read_csv(os.path.join(path_output, 'capture_events.csv'), index_col=False, dtype=str)

##################################
# Create Final DF
##################################

###########################
# Current / New Attributes
# capture_id,
# season,
# site,
# roll,
# capture,
# image_rank_in_capture,
# image_name,
# image_path,
# image_path_rel,
# datetime,
# image_rank_in_roll,
# seconds_to_next_image_taken,seconds_to_last_image_taken,
# days_to_last_image_taken,days_to_next_image_taken,
# image_name_original,image_path_original,image_path_original_rel,
# image_check__all_black,image_check__all_white,image_check__corrupt_file,image_check__corrupt_exif
# ,image_check__empty_exif,image_check__time_lapse,image_check__time_too_new,
# image_check__time_too_old,image_check__captures_with_too_many_images,
# datetime_file_creation,
# datetime_exif,
# exif__EXIF:Make,exif__EXIF:Model,exif__EXIF:Software,exif__EXIF:ModifyDate,exif__EXIF:Copyright,exif__EXIF:Orientation,exif__EXIF:XResolution,exif__EXIF:YResolution,exif__EXIF:ResolutionUnit,exif__EXIF:YCbCrPo
# sitioning,exif__EXIF:ExifVersion,exif__EXIF:DateTimeOriginal,exif__EXIF:CreateDate,exif__EXIF:ExposureTime,exif__EXIF:FNumber,exif__EXIF:MeteringMode,exif__EXIF:WhiteBalance,exif__EXIF:ColorSpace
# ,exif__EXIF:Flash,exif__EXIF:ExposureProgram,exif__EXIF:ISO,exif__EXIF:ExposureCompensation,exif__EXIF:ExifImageWidth,exif__EXIF:ExifImageHeight,exif__EXIF:UserComment,exif__Composite:Aperture,ex
# if__Composite:ImageSize,exif__Composite:Megapixels,
# exif__Composite:ShutterSpeed,exif__Composite:LightValue,
# exif__EXIF:Rating,exif__EXIF:RatingPercent,
# exif__EXIF:Padding,
# image_was_deleted,
# image_is_invalid,
# image_no_upload,
# image_uncertain_datetime,
# action_taken, action_taken_reason

# from captures_all
# 'capture_id', 'season', 'site', 'roll', 'capture', 'datetime'
# from df_final
# 'image_rank_in_capture', 'image_path_rel'
# datetime_file_creation
# datetime_exif
# image_was_deleted ? no
# image_is_invalid ? if 'invalid' = 0 then 1 else 0
# image_uncertain_datetime ? if 'invalid' 1,2,3 then 1 else 0

# final record
# 'capture_id', 'season', 'site', 'roll', 'capture', 'image_rank_in_capture',
# 'image_path_rel',
# 'datetime', 'datetime_file_creation', 'datetime_exif',
# 'invalid', 'include', 'image_is_invalid', 'image_uncertain_datetime'


df_final_cols = df_final[['image_path_rel', 'season', 'site', 'roll',
 'capture', 'image_rank_in_capture', 'datetime_exif',
 'datetime_file_creation', 'invalid', 'include']].copy()

df_final_cols.fillna('', inplace=True)
print_stats(df_final_cols['include'].value_counts())
df_final_cols.groupby(['invalid', 'include']).size().to_frame('count').reset_index()
df_final_cols.groupby(['season']).size().to_frame('count').reset_index()

# re-create 'include' flag
i_to_include = df_final_cols['invalid'].isin(['0'])
i_to_exclude = df_final_cols['invalid'].isin(['1', '2', '3'])
i_to_unknown = df_final_cols['invalid'].isin([''])
df_final_cols['include'].loc[i_to_include] = '1'
df_final_cols['include'].loc[i_to_exclude] = '0'
df_final_cols['include'].loc[i_to_unknown] = ''

# re-create 'image_is_valid' / 'image_uncertain_datetime' flags
df_final_cols['image_is_invalid'] = ''
df_final_cols['image_datetime_uncertain'] = ''
df_final_cols['image_is_invalid'].loc[i_to_exclude] = '1'
df_final_cols['image_datetime_uncertain'].loc[i_to_exclude] = '1'
df_final_cols['image_is_invalid'].loc[i_to_include] = '0'
df_final_cols['image_datetime_uncertain'].loc[i_to_include] = '0'


df_final_cols = pd.merge(
    left=df_final_cols, right=df_captures_all,
    how='left', on=['season', 'site', 'roll', 'capture'])

# checks
assert sum(df_final_cols['capture_id'].isna()) == 0
assert sum(df_final_cols['capture_id'] == '') == 0
assert sum(df_final_cols['capture'] == '') == 0
assert sum(df_final_cols['image_path_rel'] == '') == 0

# some missing values expected
sum(df_final_cols['datetime'].isna())
sum(df_final_cols['datetime'] == '')
sum(df_final_cols['datetime_file_creation'] == '')
sum(df_final_cols['datetime_file_creation'] != '')
sum(df_final_cols['datetime_exif'] == '')

df_final_cols.groupby(['invalid', 'image_is_invalid']).size().to_frame('count').reset_index()
df_final_cols.groupby(['invalid', 'image_datetime_uncertain']).size().to_frame('count').reset_index()


# final record
# 'capture_id', 'season', 'site', 'roll', 'capture', 'image_rank_in_capture',
# 'image_path_rel',
# 'datetime', 'datetime_exif',
# 'invalid', 'include', 'image_is_invalid', 'image_uncertain_datetime'

order_cols = ['capture_id', 'season', 'site',
 'roll', 'capture', 'image_rank_in_capture',
 'image_path_rel', 'datetime', 'datetime_exif', 'datetime_file_creation',
 'invalid', 'include', 'image_is_invalid', 'image_datetime_uncertain']

df_final_cols = df_final_cols[order_cols]

df_final_cols.to_csv(os.path.join(path_output, 'captures_cleaned.csv'), index=False)

##################################
# Create Filtered / Valid DF
##################################

df_final_include = df_final_cols.loc[df_final_cols['include'].isin(['1'])]

df_final_include.to_csv(os.path.join(path_output, 'captures_include.csv'), index=False)


##################################
# Create Season Cleaned
##################################

all_seasons = df_final_cols['season'].value_counts()

# sum(df_final_cols['image_rank_in_capture'] == '')
# tt = df_final_cols[df_final_cols['image_rank_in_capture'] == '']
# tt.groupby(['invalid', 'include']).size().to_frame('count').reset_index()

for season in all_seasons.index:
    output_path_season = os.path.join(path_output, 'SER_{}_cleaned.csv'.format(season))
    i_season = df_final_cols['season'].isin([season])
    df_season = df_final_cols.copy()
    df_season = df_season.loc[i_season]
    sort_df(df_season)
    df_season.to_csv(output_path_season, index=False)
    print("Wrote Season {}".format(season))


##################################
# Checks
##################################

# check for duplicates
tt = df_final_include.groupby('image_path_rel').size()
assert tt[tt>1].shape[0] == 0

# check datetime available
assert sum(df_final_include['datetime'].isna()) == 0
assert sum(df_final_include['datetime'] == '') == 0
assert sum(df_final_include['datetime_exif'] == '') == 0

# some missing values expected
sum(df_final_include['datetime_file_creation'] == '')

# check lila overlap
lila_check = pd.merge(left=df_lila, right=df_final_include, how='left',
 left_on='image_path', right_on='image_path_rel')

assert sum(lila_check['capture_id'].isna()) == 0
assert sum(lila_check['capture_id'] == '') == 0
assert sum((lila_check['datetime_x'] != lila_check['datetime_y']) & (lila_check['datetime_x'] != '')) == 0

print_stats(df_final_include['season'].value_counts())
print_stats(df_lila['season'].value_counts())

# check / investigate captures previously not in LILA but now are
tt = pd.merge(
    left=df_final_include,
    right=df_lila,
    left_on='image_path_rel',
    right_on='image_path',
    how='left',
    suffixes=('', '_lila'))

tt = tt.loc[(tt['season'].isin(['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])) & (tt['season_lila'].isna())]
tt.shape[0]
print_stats(tt['season'].value_counts())
print_stats(tt['invalid'].value_counts())
tt.iloc[0]
tt
# 12 new images (4 captures)

# check status of lila data
tt = pd.merge(
    left=df_final_include,
    right=df_lila,
    left_on='image_path_rel',
    right_on='image_path',
    how='left',
    suffixes=('', '_lila'))
tt = tt.loc[(tt['season'].isin(['S1', 'S2', 'S3', 'S4', 'S5', 'S6'])) & (tt['season_lila'].isna())]

# not in LILA but look ok
# 1908680  S5/B03/B03_R2/S5_B03_R2_IMAG0015.JPG  2012-08-05 07:37:08
# 1908681  S5/B03/B03_R2/S5_B03_R2_IMAG0016.JPG  2012-08-05 07:37:08
# 1908682  S5/B03/B03_R2/S5_B03_R2_IMAG0017.JPG  2012-08-05 07:37:08
# 2040775  S5/D06/D06_R1/S5_D06_R1_IMAG1601.JPG  2012-06-10 11:15:55
# 2040776  S5/D06/D06_R1/S5_D06_R1_IMAG1602.JPG  2012-06-10 11:15:55
# 2040777  S5/D06/D06_R1/S5_D06_R1_IMAG1603.JPG  2012-06-10 11:15:55
# 3157969  S6/S13/S13_R1/S6_S13_R1_IMAG5890.JPG  2013-01-17 08:08:47
# 3157970  S6/S13/S13_R1/S6_S13_R1_IMAG5891.JPG  2013-01-17 08:08:47
# 3157971  S6/S13/S13_R1/S6_S13_R1_IMAG5892.JPG  2013-01-17 08:08:47
# 3182402  S6/U10/U10_R2/S6_U10_R2_IMAG0448.JPG  2013-03-08 17:31:15
# 3182403  S6/U10/U10_R2/S6_U10_R2_IMAG0449.JPG  2013-03-08 17:31:15
# 3182404  S6/U10/U10_R2/S6_U10_R2_IMAG0450.JPG  2013-03-08 17:31:15

# check file existence
# no files missing
# all_files = set()
# for dirpath, dirnames, filenames in os.walk('/home/packerc/shared/albums/SER/'):
#     for filename in [f for f in filenames if f.endswith(".JPG")]:
#         all_files.add(os.path.join(dirpath, filename))
#
# root_path = '/home/packerc/shared/albums/SER/'
# missing = list()
# for _i, row in df_final_include.iterrows():
#     if (_i % 100000) == 0:
#         print("Processed {}".format(_i))
#     img_path = os.path.join(root_path, row.image_path_rel)
#     if not img_path in all_files:
#         missing.append(row.image_path_rel)
#         print("Did not find: {}".format(row.image_path_rel))


##################################
# Observations
##################################

"""
Rational:

To ensure consistency between how we have selected Serengeti S1-S6 for public release on LILA and
the upcoming release of newly created exports for S1-S11 I have investigated in detail how
previous seasons were selected. Main questions were to figure out which images were selected and how
the timestamps were defined. Along the way I have found some smaller inconsistencies. I think I have now found
a good way to create a consistent LILA delivery for public release. To ensure whatever I did makes sense to you,
I'd like you to validate the following points/observations/decisions:


1. Most images have an include and/or an invalid flag (some have neither)
2. The invalid flag indicates images with correct/confirmed timestamps.
3. All images released on LILA were flagged with invalid = '0'. You only want to release images with invalid = '0'.
4. 12 images with invalid = '0' were not released on LILA (unclear why -- the images look fine)
    -> I will include these images.
4. Some (~40) images from S7 have a faulty image name: * (2).JPG
    -> I will correct these image names.
5. Some (~6) images with faulty names in the db don't exist on MSI
    -> I will remove these non-existing images from the cleaned files.
9. 'newtime' corresponds to 'TimestampAccepted', 'oldtime' corresponds to 'TimestampJPG', this column name
    was changed over time.
6. 'TimestampAccepted' is the 'correct' time but is only available on 'capture' level. The LILA dateset, therefore,
   has the same time for each image of the same capture.
7. TimestampAccepted is usually defined for the first image of a capture but not always.
8. Some captures don't have a 1st, 2nd and 3rd image but a 2nd, 4th, 6th as defined by their 'SequenceNum'
    -> I will NOT correct these.
9. Empty/blanks released on LILA do not have a timestamp.
    -> I will add timestamps for blanks.

I can guarantee:

1. All images released on LILA (S1-S6) will be in the newly created reports
2. All timestamps released on LILA (S1-S6) will match with the newly created reports
3. The labels for S1-S6 may have changed because:
    1) they can not be reproduced b/c of random effects,
    2) we have gathered more annotations,
    3) small changes in how 'blanks' are defined
4. All images in the reports / cleaned.csv files actually exist on MSI

Does the following distribution per season make sense (number of images):
S9  -- counts:     983081 / 6679922 (14.72 %)
S8  -- counts:     980256 / 6679922 (14.67 %)
S7  -- counts:     832154 / 6679922 (12.46 %)
S5  -- counts:     827224 / 6679922 (12.38 %)
S10 -- counts:     685686 / 6679922 (10.26 %)
S2  -- counts:     573200 / 6679922 (8.58 %)
S4  -- counts:     531554 / 6679922 (7.96 %)
S6  -- counts:     462846 / 6679922 (6.93 %)
S1  -- counts:     411414 / 6679922 (6.16 %)
S3  -- counts:     392507 / 6679922 (5.88 %)
"""



#df_merged2.groupby(['season', 'Invalid', 'include']).size().to_frame('count').reset_index()
#   invalid include    count
# 0                    27072
# 1       0       1  6679922
# 2       1       0    32572
# 3       2       0    36773
# 4       3       0    14555


##################################
# OLD CHECKS
##################################

# # check for duplicates
# tt = df_final_include.groupby('image_path_rel').size()
# tt[tt>1]
#
# # check lila content
# lila_check = pd.merge(left=df_lila, right=df_final_include, how='left',
#  left_on='image_path', right_on='image_path_rel')
#
# tt = lila_check[lila_check['capture_id'].isna()]
#
# df_lila[df_lila['image_path'] == 'S1/L10/L10_R1/S1_L10_R1_PICT0001.JPG']
# df_export[df_export['image_path'] == 'S1/L10/L10_R1/S1_L10_R1_PICT0001.JPG']
# # 'SequenceNum' wrong, capture starts with 2, 4 6
#
#
# lila_check.shape
# df_lila.shape
#
#
# # duplicates
# # df_export[df_export['image_path']== 'S1/I07/I07_R1/S1_I07_R1_PICT0007.JPG']
# # df_merged2[df_merged2['image_path'] == 'S1/I07/I07_R1/S1_I07_R1_PICT0007.JPG']
# # df_merged2[df_merged2['image_path'] == 'S10/H06/H06_R2/S10_H06_R2_IMAG0062.JPG']
# # df_merged2[(df_merged2['season'] == 'S10') & (df_merged2['site'] == 'H06') & (df_merged2['roll'] == '2') & (df_merged2['capture_clean'] == '23')]
#
# # test timestamps
# tt = df_merged2[(df_merged2['oldtime'] != df_merged2['TimestampJPG']) & (df_merged2['oldtime'] != '') & (df_merged2['TimestampJPG'] != '')]
# tt.shape
# # -> oldtime is TimestampJPG
#
# tt = df_merged2[(df_merged2['newtime'] != df_merged2['TimestampAccepted']) & (df_merged2['newtime'] != '') & (df_merged2['TimestampAccepted'] != '')]
# tt.shape
# # -> newtime is mostly 'TimestampAccepted' (small discrepancies for S4, S5 and S6)
# print_stats(tt['season'].value_counts())
#
# tt = df_merged2[(df_merged2['oldtime'] != df_merged2['newtime']) & (df_merged2['oldtime'] != '') & (df_merged2['newtime'] != '')]
# tt.shape
# # -> oldtime is not newtime
#
# # compare lila
# tt = df_merged2[(df_merged2['datetime'] != df_merged2['TimestampAccepted']) & (df_merged2['datetime'] != '') & (df_merged2['TimestampAccepted'] != '')]
# tt.shape
# print_stats(tt['SequenceNum'].value_counts())
# tt.iloc[10]
# # wrong in db (but only for sequecenum2)
# df_merged2[df_merged2['image_path'] == 'S1/D09/D09_R2/S1_D09_R2_PICT0014.JPG']
#
# tt = df_merged2[(df_merged2['datetime'] != df_merged2['TimestampAccepted']) &
#     (df_merged2['datetime'] != '') &
#     (df_merged2['TimestampAccepted'] != '') &
#     (df_merged2['SequenceNum'] == '1')]
# tt.shape
# # 65 first images with different timestamp
# for _i, row in tt.iterrows():
#     print("cleaned: {} lila: {}".format(row.TimestampAccepted, row.datetime))
# # some significant differences - db is wrong
# tt.iloc[4]
# df_merged2[df_merged2['image_path'] == 'S1/E02/E02_R5/S1_E02_R5_PICT0274.JPG']
# # -> generally accept LILA timestamp
#
#
# df_merged2.groupby(['season', 'invalid', 'include']).size().to_frame('count').reset_index()
#
#
# # TESTS
# df_merged[(df_merged['season'] == 'S4') &
# (df_merged['site'] == 'C07') &
#  (df_merged['roll'] == '2') &
#   (df_merged['capture'] == '1234')]
#
#
# #df_capture = df_capture[df_capture['datetime_clean'] != '']
# df_capture3 = df_capture.groupby(['season', 'site', 'roll', 'capture']).first()
#
#
# # try to get datetime
# def create_datetime(date_str):
#     try:
#         tm = _get_datetime_obj(date_str)
#     except:
#         tm = None
#     return tm
# df_capture['datetime_obj'] = df_capture['datetime_clean'].apply(
#     lambda x: create_datetime(x))
# df_capture2 = df_capture.groupby(['season', 'site', 'roll', 'capture']).datetime_obj.agg(['min', 'max'])
#
# df_capture2[df_capture2['min'] !=  df_capture2['max']]
# # TESTS
# df_final[(df_final['season'] == 'S1') &
# (df_final['site'] == 'C07') &
#  (df_final['roll'] == '2') &
#   (df_final['capture'] == '1042')]
#
# df_capture.drop_duplicates(subset=['season', 'site', 'roll', 'capture'], inplace=True)
# df_capture.shape
# # (2513837, 6) without excluding 'datetime_clean' != ''
# # (2503309, 5) with excluding 'datetime_clean' != ''
#
# # TESTS
# no_datetime = df_capture[df_capture['datetime_clean'] == '']
# df_final[(df_final['season'] == 'S2') &
# (df_final['site'] == 'H07') &
#  (df_final['roll'] == '2') &
#   (df_final['capture'] == '242')]['datetime']
# df_capture[(df_capture['season'] == 'S2') &
# (df_capture['site'] == 'H07') &
#  (df_capture['roll'] == '2') &
#   (df_capture['capture'] == '242')]['datetime']
#
# tt = df_capture[(df_capture['season'] == 'S2') &
# (df_capture['site'] == 'H07') &
#  (df_capture['roll'] == '2') &
#   (df_capture['capture'] == '242')]
# tt['datetime_obj'] = tt['datetime_clean'].apply(
#     lambda x: create_datetime(x))
# tt2 = tt.groupby(['season', 'site', 'roll', 'capture']).datetime_obj.agg(['min', 'max'])
#
# # SER_S8#L11#3#1224
# # has no datetime
# df_final[(df_final['season'] == 'S8') &
# (df_final['site'] == 'L11') &
#  (df_final['roll'] == '3') &
#   (df_final['capture'] == '1224')]['datetime']
#
#
#
# def create_capture_id(season, site, roll, capture):
#     return 'SER_{}#{}#{}#{}'.format(season, site, roll, capture)
#
# df_capture['capture_id'] = df_capture[['season', 'site', 'roll', 'capture']].apply(
#     lambda x: create_capture_id(*x), axis=1)
#
# # investigate
# df_capture.shape
#
#
# # SER_S1#L10#1#9
# df_merged2[(df_merged2['season'] == 'S1') & (df_merged2['site'] == 'L10') & (df_merged2['roll'] == '1') & (df_merged2['capture_export'] == '9')]
# # remove:
# # S1/L10/L10_R1/S1_L10_R1_PICT0023 (2).JPG
# # S1/L10/L10_R1/S1_L10_R1_PICT0024 (2).JPG
# # S1/L10/L10_R1/S1_L10_R1_PICT0025 (2).JPG
#
# # SER_S1#O05#1#1171
# df_merged2[(df_merged2['season'] == 'S1') &
#     (df_merged2['site'] == 'O05') &
#     (df_merged2['roll'] == '1') &
#     (df_merged2['capture_export'] == '1171')]
# # if no lila timestamp and if no timestamp accepted, take timestamp jpg
#
# # SER_S8#L11#3#
# df_merged2[(df_merged2['season'] == 'S8') &
#  (df_merged2['site'] == 'L11') &
#   (df_merged2['roll'] == '3') &
#   (df_merged2['capture_export'] == '1225')]
# # substitute capture export with capture clean if capture export is empty
# # some captures not in db but in cleaned?
#
#
#
# S1/O05/O05_R1/S1_O05_R1_PICT3650.JPG
# S1/O05/O05_R1/S1_O05_R1_PICT3711.JPG
# df_merged2[df_merged2['image_path'] == 'S1/O05/O05_R1/S1_O05_R1_PICT3650.JPG']
# df_merged2[df_merged2['image_path'] == 'S1/O05/O05_R1/S1_O05_R1_PICT3711.JPG']
