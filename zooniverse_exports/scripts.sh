
###################################
# Grumeti
####################################

SITE=GRU
SEASON=GRU_S1

python3 -m zooniverse_exports.extract_classifications \
        --classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
        --output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv


###################################
# Snapshot Serengeti - Legacy
####################################

# Extract Classifications
cd $HOME/snapshot_safari_misc

python3 -m zooniverse_exports.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process 'S3'

# Aggregate Classifications

###################################
# Snapshot Serengeti
####################################


cd $HOME/snapshot_safari_misc
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
        -output_csv /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications_extracted.csv \
        -workflow_id 4655 \
        -workflow_version 304

python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications_extracted.csv \
          -output_csv /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications_aggregated.csv

# Snapshot Serengeti
cd /home/packerc/shared/machine_learning/will5448/code/aggregation-for-caesar


# Most recent workflow version
python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/workflows.csv \
4655 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/extraction.csv

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/survey_extractor_extraction.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/reduction.csv

# Add Keywords
python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/workflows.csv \
4655 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/extraction_keywords.csv \
-k \'{\"T0\": {\"dot_freq\": \"line\"} }\'

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/survey_extractor_extraction.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/reduction.csv


# Different workflow version
python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/workflows.csv \
4655 \
-v 303 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/extraction_303.csv

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/survey_extractor_extraction_303.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/reduction_303.csv


# Different workflow version
python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/workflows.csv \
4655 \
-v 304 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/extraction_304.csv

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/survey_extractor_extraction_303.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/reduction_303.csv


python3 -m zooniverse_exports.extract_choices_from_workflow \
  -workflow_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/workflows.csv \
  -output /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/label_mapping.json

python3 -m zooniverse_exports.create_image_to_label \
-zooid_path /home/packerc/shared/zooniverse/ZOOIDs/SER/ \
-manifest_path /home/packerc/shared/zooniverse/Manifests/SER/ \
-zoo_exports_path /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/ \
-ml_info_path /home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/ \
-manifest_files SER_S11_1_manifest_v1 SER_S11_2_manifest_v1 \
-zooid_files SER_S11_1_ZOOID_v0.csv SER_S11_2_ZOOID_v0.csv \
-season_id SER_S11


# Generate Info Files from ZOOID files for prediction
python3 -m zooniverse_exports.generate_predict_file_from_zooids \
-root_path /home/packerc/shared/zooniverse/ZOOIDs/SER/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/SER_S11_all.csv \
-files SER_S11_1_ZOOID_v0.csv SER_S11_2_ZOOID_v0.csv \
-path_field path


# Generate Predictions to Subject Mapping
python3 -m zooniverse_exports.aggregate_preds_on_subject \
-manifest_root_path  /home/packerc/shared/zooniverse/Manifests/SER/ \
-manifest_files  SER_S11_1_manifest_v1 SER_S11_2_manifest_v1 \
-zooid_root_path  /home/packerc/shared/zooniverse/ZOOIDs/SER/ \
-zooid_files SER_S11_1_ZOOID_v0.csv SER_S11_2_ZOOID_v0.csv \
-predictions_empty_path /home/packerc/shared/machine_learning/data/predictions/empty_or_not/SER/SER_S11/predictions_run_20180619.json \
-predictions_species_path /home/packerc/shared/machine_learning/data/predictions/species/SER/SER_S11/predictions_run_20180619.json \
-output_file  /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/SER_S11_predictions_SER_old.json \
-label_mapping_path /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/label_mapping.json



# Simulate Different Aggregations
python3 -m zooniverse_exports.simulate_aggregations_ml \
-classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/classifications_extracted.csv \
-output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/classifications_aggregated_ml_SER_old.csv \
-aggregated_predictions /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/SER_S11_predictions_SER_old.json


# Simulate Different Aggregations after fine tuning
python3 -m zooniverse_exports.simulate_aggregations_ml \
-classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/classifications_extracted.csv \
-output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/classifications_aggregated_ml_after_fine_tune.csv \
-aggregated_predictions /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/SER_S11_predictions.json



-root_path /home/packerc/shared/zooniverse/ZOOIDs/SER/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/SER_S11_all.csv \
-files SER_S11_1_ZOOID_v0.csv SER_S11_2_ZOOID_v0.csv \
-path_field path


###################################
# Ruaha
####################################

# get Zooniverse exports
cd $HOME/snapshot_safari_misc
SITE=RUA
SEASON=RUA_S1

python3 -m zooniverse_exports.get_zooniverse_export \
        -password_file ~/keys/passwords.ini \
        -project_id 5155 \
        -output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
        -export_type classifications \
        -new_export 0


# Extract Zooniverse Classifications
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
        -workflow_id 4889 \
        -workflow_version 797

# Aggregate Zooniverse Classifications
python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_extracted.csv \
          -output_csv /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_aggregated.csv

# Create Label Mapping from workflow file
python3 -m zooniverse_exports.extract_choices_from_workflow \
  -workflow_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/workflows.csv \
  -output /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/label_mapping.json


# write_first_nrows_of_csv_to_csv('/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications.csv', '/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_sampled.csv', 50000)

# Create Mapping Files: Image Path to Label (for training and evaluating models)
cd $HOME/snapshot_safari_misc

python3 -m zooniverse_exports.create_image_to_label \
-zooid_path /home/packerc/shared/zooniverse/ZOOIDs/RUA/ \
-manifest_path /home/packerc/shared/zooniverse/Manifests/RUA/ \
-zoo_exports_path /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/ \
-ml_info_path /home/packerc/shared/machine_learning/data/info_files/RUA/RUA_S1/ \
-manifest_files RUA_S1_A1_manifest_v1 \
-zooid_files RUA_S1_A1_ZOOID.csv \
-season_id RUA_S1


# Generate Info Files from ZOOID files for prediction
python3 -m zooniverse_exports.generate_predict_file_from_zooids \
-root_path /home/packerc/shared/zooniverse/ZOOIDs/RUA/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/RUA/RUA_S1/RUA_S1_all.csv \
-files RUA_S1_A1_ZOOID.csv \
-path_field path


python3 -m zooniverse_exports.aggregate_preds_on_subject \
-manifest_root_path  /home/packerc/shared/zooniverse/Manifests/RUA/ \
-manifest_files  RUA_S1_A1_manifest_v1 \
-zooid_root_path  /home/packerc/shared/zooniverse/ZOOIDs/RUA/ \
-zooid_files RUA_S1_A1_ZOOID.csv \
-predictions_empty_path /home/packerc/shared/machine_learning/data/predictions/empty_or_not/RUA/RUA_S1/predictions_run_SER_old_all_val_old_20180716.json \
-predictions_species_path /home/packerc/shared/machine_learning/data/predictions/species/RUA/RUA_S1/predictions_run_SER_old_all_val_old_20180716.json \
-output_file  /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/RUA_S1_predictions_SER_old_all_val_old.json \
-label_mapping_path /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/label_mapping.json


# Simulate Different Aggregations
python3 -m zooniverse_exports.simulate_aggregations_ml \
-classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_extracted.csv \
-output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_aggregated_ml_SER_old_20180716.csv \
-aggregated_predictions /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/RUA_S1_predictions_SER_old_all_val_old.json


# Generate TFRecord info base file
cd /home/packerc/shared/scripts/snapshot_safari_misc
module load python3
python3 -m zooniverse_exports.add_meta_data_to_aggregated_class \
-classifications_aggregated /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_classifications_aggregated.csv \
-season_cleaned /home/packerc/shared/season_captures/RUA/cleaned/RUA_S1_cleaned_A.csv \
-output_csv /home/packerc/shared/zooniverse/Exports/RUA/RUA_S1_export.csv \
-season RUA_S1 \
-site RUA \
-manifest_files_old /home/packerc/shared/zooniverse/Manifests/RUA/RUA_S1_A1_manifest_v1 \
-max_n_images 3


###################################
# Snapshot Serengeti
####################################
cd $HOME/snapshot_safari_misc
SITE=SER
SEASON=SER_S11
PROJECT_ID=4996
WORFKLOW_ID=4655
WORFKLOW_VERSION=363.25

python3 -m zooniverse_exports.get_zooniverse_export \
    -password_file ~/keys/passwords.ini \
    -project_id ${PROJECT_ID} \
    -output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
    -export_type classifications \
    -new_export 0


###################################
# Cedar Creek
####################################
cd $HOME/snapshot_safari_misc
SITE=CC
SEASON=CC_S1
PROJECT_ID=5880
WORFKLOW_ID=5702
WORFKLOW_VERSION=289.16


python3 -m zooniverse_exports.get_zooniverse_export \
    -password_file ~/keys/passwords.ini \
    -project_id ${PROJECT_ID} \
    -output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
    -export_type classifications \
    -new_export 0


###################################
# Grumeti
####################################


# get Zooniverse exports
cd $HOME/snapshot_safari_misc
SITE=GRU
SEASON=GRU_S1

python3 -m zooniverse_exports.get_zooniverse_export \
        -password_file ~/keys/passwords.ini \
        -project_id 5115 \
        -output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
        -export_type classifications \
        -new_export 0

# Extract Classifications
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
        -workflow_id 4979 \
        -workflow_version 275

# Aggregate Classifications
python3 -m zooniverse_exports.aggregate_extractions \
        -classifications_extracted /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_extracted.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated.csv


# Add Meta-Data to Aggregated Classifications
python3 -m zooniverse_exports.add_meta_data_to_aggregated_class \
  -classifications_aggregated /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated.csv \
  -season_cleaned /home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv \
  -output_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_export.csv \
  -season GRU_S1 \
  -site GRU \
  -manifest_files_old /home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1_manifest_v1 \
  -max_n_images 3




# python3 -m zooniverse_exports.extract_choices_from_workflow \
#   -workflow_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/workflows.csv \
#   -output /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/label_mapping.json


# python3 -m zooniverse_exports.create_image_to_label \
# -zooid_path /home/packerc/shared/zooniverse/ZOOIDs/GRU/ \
# -manifest_path /home/packerc/shared/zooniverse/Manifests/GRU/ \
# -zoo_exports_path /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/ \
# -ml_info_path /home/packerc/shared/machine_learning/data/info_files/GRU/GRU_S1/ \
# -manifest_files GRU_S1_manifest_v1 \
# -zooid_files GRU_S1_ZOOID.csv \
# -season_id GRU_S1


# Generate Info Files from ZOOID files for prediction
python3 -m zooniverse_exports.generate_predict_file_from_zooids \
-root_path /home/packerc/shared/zooniverse/ZOOIDs/GRU/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/GRU/GRU_S1/GRU_S1_all.csv \
-files GRU_S1_ZOOID.csv \
-path_field path



# write_first_nrows_of_csv_to_csv('/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications.csv', '/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_sampled.csv', 50000)

###################################
# Gondwana
####################################


# Get classifications
cd $HOME/snapshot_safari_misc
module load python3
python3 -m zooniverse_exports.get_zooniverse_export -password_file ~/keys/passwords.ini \
        -project_id 3812 \
        -output_file /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications.csv \
        -export_type classifications \
        -new_export 0


# Extract classifications
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications_extracted.csv \
        -workflow_id 3360 \
        -workflow_version 497

# aggregate classifications
python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications_extracted.csv \
          -output_csv /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications_aggregated.csv

# Create Label-Mapping Plus Meta-Data (for TFRecord)
python3 -m zooniverse_exports.add_meta_data_to_aggregated_class \
  -classifications_aggregated /home/packerc/shared/zooniverse/Exports/GON/GON_S1_classifications_aggregated.csv \
  -season GON_S1 \
  -site GON \
  -manifest_files_old /home/packerc/shared/zooniverse/Manifests/GON/GON_S1_manifest_v1 \
  -season_cleaned /home/packerc/shared/season_captures/GON/cleaned/GON_S1_cleaned.csv \
  -output_csv /home/packerc/shared/zooniverse/Exports/GON/GON_S1_export.csv


###################################
# Niassa / Mariri (NIA)
####################################

# Get classifications
cd $HOME/snapshot_safari_misc
module load python3
python3 -m zooniverse_exports.get_zooniverse_export -password_file ~/keys/passwords.ini \
        -project_id 5044 \
        -output_file /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications.csv \
        -export_type classifications \
        -new_export 0

# Extract classifications
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications_extracted.csv \
        -workflow_id 4986 \
        -workflow_version 531

# aggregate classifications
python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications_extracted.csv \
          -output_csv /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications_aggregated.csv


# Create Label-Mapping Plus Meta-Data (for TFRecord)
python3 -m zooniverse_exports.add_meta_data_to_aggregated_class \
  -classifications_aggregated /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_classifications_aggregated.csv \
  -season NIA_S1 \
  -site NIA \
  -manifest_files_old /home/packerc/shared/zooniverse/Manifests/NIA/NIA_S1_manifest_v1 \
  -season_cleaned /home/packerc/shared/season_captures/NIA/cleaned/NIA_S1_cleaned_corrected.csv \
  -output_csv /home/packerc/shared/zooniverse/Exports/NIA/NIA_S1_export.csv

###################################
# Gorongosa - Incomplete (different format)
####################################


# Get classifications
cd $HOME/snapshot_safari_misc
module load python3
python3 -m zooniverse_exports.get_zooniverse_export -password_file ~/keys/passwords.ini \
        -project_id 593 \
        -output_file /home/packerc/shared/zooniverse/Exports/GOR/GOR_S1_classifications.csv \
        -export_type classifications \
        -new_export 0


# Extract classifications
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/zooniverse/Exports/GOR/GOR_S1_classifications.csv \
        -output_csv /home/packerc/shared/zooniverse/Exports/GOR/GOR_S1_classifications_extracted.csv \
        -workflow_id 338 \
        -workflow_version 1899


###################################
# Misc
####################################


# python3 extract_panoptes_csv.py \
# /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_classifications.csv \
# /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_workflows.csv \
# 4255 \
# -o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_extraction.csv
#
# python3  reduce_panoptes_csv.py \
# /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/question_extractor_4715_extraction.csv \
# -o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_reduction.csv
