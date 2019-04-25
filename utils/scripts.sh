###################################
# Various commands
####################################

# Create paths
for LOC in MTZ KAR PLN NIA GON APN GRU SER RUA MAD KRU ENO; do
  mkdir -m 770 -p {SpeciesReports,Exports,Aggregations,Manifests,MachineLearning,LilaReports}/${LOC}/log_files
done

for LOC in SER; do
  mkdir -m 770 -p {LilaReports,SpeciesReports}/${LOC}/log_files
done



###################################
# MAD
####################################


set_params_MAD () {

cd $HOME/camera-trap-data-pipeline
SITE=MAD
SEASON=MAD_S1
PROJECT_ID=8776
WORKFLOW_ID=10337
WORKFLOW_VERSION_MIN=383

}


###################################
# Grumeti
####################################

set_params_GRU () {

cd $HOME/camera-trap-data-pipeline
SITE=GRU
SEASON=GRU_S1
PROJECT_ID=5115
WORKFLOW_ID=4979
WORKFLOW_VERSION_MIN=275
ATTRIBUTION='University of Minnesota Lion Center + Snapshot Safari + Singita Grumeti + Tanzania'
LICENSE='Snapshot Safari + Singita Grumeti'

}

###################################
# RUA
####################################


set_params_RUA () {

cd $HOME/camera-trap-data-pipeline
SITE=RUA
SEASON=RUA_S1
PROJECT_ID=5155
WORKFLOW_ID=4889
WORKFLOW_VERSION_MIN=797

}

###################################
# Mountain Zebra
####################################

set_params_MTZ () {

cd $HOME/camera-trap-data-pipeline
SITE=MTZ
SEASON=MTZ_S1
PROJECT_ID=5124
WORKFLOW_ID=8814
WORKFLOW_VERSION_MIN=247

}

###################################
# Karoo
####################################

set_params_KAR () {

cd $HOME/camera-trap-data-pipeline
SITE=KAR
SEASON=KAR_S1
PROJECT_ID=7679
WORKFLOW_ID=8789
WORKFLOW_VERSION_MIN=237.7

}

###################################
# Pilanesberg
####################################

set_params_PLN () {

cd $HOME/camera-trap-data-pipeline
SITE=PLN
SEASON=PLN_S1
PROJECT_ID=6190
WORKFLOW_ID=7764
WORKFLOW_VERSION_MIN=311.5

}

###################################
# Cedar Creek
####################################

set_params_CC () {

cd $HOME/camera-trap-data-pipeline
SITE=CC
SEASON=CC_S1
PROJECT_ID=5880
WORKFLOW_ID=5702
WORKFLOW_VERSION_MIN=289

}

###################################
# Snapshot Serengeti
####################################

set_params_SER () {

cd $HOME/camera-trap-data-pipeline
SITE=SER
SEASON=SER_S11
PROJECT_ID=4996
WORKFLOW_ID=4655
WORKFLOW_VERSION_MIN=304

}

###################################
# ENO
####################################

set_params_ENO () {

cd $HOME/camera-trap-data-pipeline
SITE=ENO
SEASON=ENO_S1
PROJECT_ID=8676
WORKFLOW_ID=10284
WORKFLOW_VERSION_MIN=227.4

}

# TEST
cd $HOME/camera-trap-data-pipeline
SITE=ENO
SEASON=ENO_S1_TEST_CANBEDELETED
PROJECT_ID=
WORKFLOW_ID=
WORKFLOW_VERSION_MIN=



###################################
# APN
####################################

set_params_APN () {

cd $HOME/camera-trap-data-pipeline
SITE=APN
SEASON=APN_S1
PROJECT_ID=5561
WORKFLOW_ID=5719
WORKFLOW_VERSION_MIN=159.9

}

cd $HOME/camera-trap-data-pipeline
SITE=APN
SEASON=APN_S2
PROJECT_ID=
WORKFLOW_ID=
WORKFLOW_VERSION_MIN=


###################################
# GON
####################################

set_params_GON () {

cd $HOME/camera-trap-data-pipeline
SITE=GON
SEASON=GON_S1
PROJECT_ID=3812
WORKFLOW_ID=3360
WORKFLOW_VERSION_MIN=497.11

}

###################################
# NIA (Mariri)
####################################

set_params_NIA () {

cd $HOME/camera-trap-data-pipeline
SITE=NIA
SEASON=NIA_S1
PROJECT_ID=5044
WORKFLOW_ID=4986
WORKFLOW_VERSION_MIN=531.12

}

###################################
# Python Prep
####################################

qsub -I -l walltime=6:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd $HOME/camera-trap-data-pipeline
git pull

###################################
# Bulk Processing
####################################

# done: KAR, MTZ, PLN, NIA, GON, APN, GRU, RUA

# Loop over all seasons
LOC=SER
for LOC in MTZ KAR PLN NIA GON APN GRU SER RUA; do
  set_params_${LOC}
  extract_zooniverse_data
  aggregate_annotations
  create_reports
done

# Loop over all seasons (Legacy)
for season in 1 2 3 4 5 6 7 8 9 10; do
  SITE=SER
  SEASON=SER_S${season}
  if [ $season -eq 10 ]
  then
    SEASON_STRING=${season}
  else
    SEASON_STRING=S${season}
  fi
  echo "season string: ${SEASON_STRING}"
  extract_zooniverse_data_legacy
  aggregate_annotations
  create_reports
  create_lila_reports
done


###################################
# Pre-Processing
####################################

# Check Input Structure
python3 -m pre_processing.check_input_structure \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_check_input_structure

# Check for duplicate images
python3 -m pre_processing.check_for_duplicates \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_check_for_duplicates

# Create Image Inventory
python3 -m pre_processing.create_image_inventory \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory_basic.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_create_image_inventory

# Create Basic Inventory Checks
python3 -m pre_processing.basic_inventory_checks \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory_basic.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
--n_processes 16 \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_basic_inventory_checks

# Extract Exif Data
python3 -m pre_processing.extract_exif_data \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
--update_inventory \
--output_csv /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_exif_data.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_exif_data

# Group Images into Captures
python3 -m pre_processing.group_inventory_into_captures \
--inventory /home/packerc/shared/season_captures/${SITE}/inventory/${SEASON}_inventory.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--no_older_than_year 2017 \
--no_newer_than_year 2019 \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_group_inventory_into_captures

# rename all images
python3 -m pre_processing.rename_images \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_rename_images

# generate action list
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--plot_timelines \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_create_action_list

# generate actions
python3 -m pre_processing.generate_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--actions_to_perform_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_generate_actions

# apply actions
python3 -m pre_processing.apply_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--actions_to_perform /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_apply_actions

# Update Captures
python3 -m pre_processing.update_captures \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--captures_updated /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_update_captures

cp /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_captures_cleaned.csv

# generate action list - (OPTIONAL)
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list2.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--log_filename ${SEASON}_create_action_list


###################################
# Machine Learning
####################################

python3 -m machine_learning.create_machine_learning_file \
--cleaned_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_csv /home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_machine_learning_input.csv \
--log_dir /home/packerc/shared/zooniverse/MachineLearning/${SITE}/log_files/ \
--log_filename ${SEASON}_create_machine_learning_file


INPUT_FILE=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_machine_learning_input.csv
OUTPUT_FILE_EMPTY=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_empty_or_not.json
OUTPUT_FILE_SPECIES=/home/packerc/shared/zooniverse/MachineLearning/${SITE}/${SEASON}_predictions_species.json
IMAGES_ROOT=/home/packerc/shared/albums/${SITE}/

qsub -v INPUT_FILE=${INPUT_FILE},OUTPUT_FILE=${OUTPUT_FILE_EMPTY},IMAGES_ROOT=${IMAGES_ROOT} ctc_predict_empty_file.pbs
qsub -v INPUT_FILE=${INPUT_FILE},OUTPUT_FILE=${OUTPUT_FILE_SPECIES},IMAGES_ROOT=${IMAGES_ROOT} ctc_predict_species_file.pbs

###################################
# Zooniverse Uploads
####################################

# generate manifest
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--manifest_id ${SEASON} \
--attribution "${ATTRIBUTION}" \
--license "${LICENSE}"

# Create machine learning file
python3 -m zooniverse_uploads.create_machine_learning_file \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json

# add machine scores to batch
python3 -m zooniverse_uploads.add_predictions_to_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json

# Split into batches
python3 -m zooniverse_uploads.split_manifest_into_batches \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--max_batch_size 20000

# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_2__manifest.json \
--project_id ${PROJECT_ID} \
--image_root_path /home/packerc/shared/albums/${SITE}/ \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--password_file ~/keys/passwords.ini

# Retry Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_2__manifest.json \
--project_id ${PROJECT_ID} \
--subject_set_id 73582 \
--image_root_path /home/packerc/shared/albums/${SITE}/ \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--password_file ~/keys/passwords.ini

###################################
# Zooniverse Downloads
####################################

extract_zooniverse_data () {
# Get Zooniverse Classification Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--export_type classifications \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/

# Get Zooniverse Subject Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--export_type subjects \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/

# Extract Annotations from Classifications
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORKFLOW_VERSION_MIN \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_annotations

# Extract Subject Data
python3 -m zooniverse_exports.extract_subjects \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects
}

###################################
# Zooniverse Aggregations
####################################

aggregate_annotations () {

python3 -m aggregations.aggregate_annotations_plurality \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality_raw.csv \
--log_dir /home/packerc/shared/zooniverse/Aggregations/${SITE}/log_files/ \
--log_filename ${SEASON}_aggregate_annotations_plurality

python3 -m zooniverse_exports.merge_csvs \
--base_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality_raw.csv \
--to_add_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality.csv \
--key subject_id

}

###################################
# Reporting
####################################

create_reports () {

# Create Complete Report
python3 -m reporting.create_zooniverse_report \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_complete.csv \
--default_season_id ${SEASON} \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_zooniverse_report

# Create statistics file
python3 -m reporting.create_report_stats \
--report_path /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_complete.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_complete_overview.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_report_stats

# Create Consensus Report
python3 -m reporting.create_zooniverse_report \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_consensus.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_zooniverse_report \
--default_season_id ${SEASON} \
--exclude_blanks \
--exclude_humans \
--exclude_non_consensus \
--exclude_captures_without_data \
--exclude_zooniverse_cols \
--exclude_additional_plurality_infos

# Create statistics file
python3 -m reporting.create_report_stats \
--report_path /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_consensus.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_consensus_overview.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_report_stats

# Create a small sample report
python3 -m reporting.sample_report \
--report_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_consensus.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_consensus_samples.csv \
--sample_size 300 \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/log_files/ \
--log_filename ${SEASON}_sample_report
}

create_lila_reports () {
python3 -m reporting.create_zooniverse_report \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_aggregated_plurality.csv \
--output_csv /home/packerc/shared/zooniverse/LilaReports/${SITE}/${SEASON}_report_lila.csv \
--log_dir /home/packerc/shared/zooniverse/LilaReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_zooniverse_report \
--default_season_id ${SEASON} \
--exclude_non_consensus \
--exclude_captures_without_data \
--exclude_zooniverse_cols \
--exclude_additional_plurality_infos \
--exclude_zooniverse_urls

python3 -m reporting.create_report_stats \
--report_path /home/packerc/shared/zooniverse/LilaReports/${SITE}/${SEASON}_report_lila.csv \
--output_csv /home/packerc/shared/zooniverse/LilaReports/${SITE}/${SEASON}_report_lila_overview.csv \
--log_dir /home/packerc/shared/zooniverse/LilaReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_report_stats

python3 -m reporting.create_image_inventory \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--report_path /home/packerc/shared/zooniverse/LilaReports/${SITE}/${SEASON}_report_lila.csv \
--output_csv /home/packerc/shared/zooniverse/LilaReports/${SITE}/${SEASON}_report_lila_image_inventory.csv \
--log_dir /home/packerc/shared/zooniverse/LilaReports/${SITE}/log_files/ \
--log_filename ${SEASON}_create_image_inventory
}


###################################
# Reporting - Machine Learning
####################################

# Create Flattened ML Predictions
python3 -m machine_learning.flatten_ml_predictions \
--predictions_empty /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__predictions_empty_or_not.json \
--predictions_species /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__predictions_species.json \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_ml_preds_flat.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/

# Reporting of Machine Learning Predictions
python3 -m reporting.add_predictions_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--predictions_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_ml_preds_flat.csv \
--output_csv /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/${SEASON}_report_ml.csv \
--log_dir /home/packerc/shared/zooniverse/SpeciesReports/${SITE}/ \
--export_only_with_predictions


###################################
# Snapshot Serengeti - Legacy
####################################

qsub -I -l walltime=10:00:00,nodes=1:ppn=4,mem=16gb
module load python3

cd $HOME/camera-trap-data-pipeline
SITE=SER
SEASON=SER_S1
SEASON_STRING=S1

extract_zooniverse_data_legacy () {

# Extract Annotations
python3 -m zooniverse_exports.legacy.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path /home/packerc/shared/zooniverse/Exports/SER/ \
--season_to_process ${SEASON_STRING} \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_legacy_serengeti


# Extract Subjects from Classifications
python3 -m zooniverse_exports.legacy.extract_subjects_legacy \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_prelim.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects_legacy_prelim


# # Get Subject URLs from Zooniverse API (warning - takes a long time)
# python3 -m zooniverse_exports.get_legacy_ouroboros_data \
# --subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_prelim.csv \
# --subjects_ouroboros /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json

# # Extract Zooniverse URLs from Oruboros Exports
# python3 -m zooniverse_exports.extract_legacy_subject_urls \
# --oruboros_export /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json \
# --output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv

# DO NOT RUN - SEASON CAPTURES ARE CREATED DIFFERENTLY
# # Re-Create Season Captures
# python3 -m zooniverse_exports.recreate_legacy_season_captures \
# --subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted_prelim.csv \
# --output_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
# --log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
# --log_filename ${SEASON}_recreate_legacy_season_captures

# Extract Subjects from Classifications without timestamps
python3 -m zooniverse_exports.legacy.extract_subjects_legacy \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/log_files/ \
--log_filename ${SEASON}_extract_subjects_legacy \
--exclude_colums timestamps filenames

# Add subject urls to subject extracts
python3 -m zooniverse_exports.merge_csvs \
--base_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--to_add_cs /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--key subject_id \
--add_new_cols_to_right
}
