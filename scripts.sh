###################################
# Grumeti
####################################

cd $HOME/snapshot_safari_misc
SITE=GRU
SEASON=GRU_S1
PROJECT_ID=5115
WORKFLOW_ID=4979
WORFKLOW_VERSION_MIN=275
ATTRIBUTION="'University of Minnesota Lion Center + Snapshot Safari + Singita Grumeti + Tanzania'"
LICENSE="'Snapshot Safari + Singita Grumeti'"

###################################
# Mountain Zebra
####################################

cd $HOME/snapshot_safari_misc
SITE=MTZ
SEASON=MTZ_S1
PROJECT_ID=5124
WORKFLOW_ID=8814
WORFKLOW_VERSION_MIN=247

###################################
# Karoo
####################################

cd $HOME/snapshot_safari_misc
SITE=KAR
SEASON=KAR_S1
PROJECT_ID=7679
WORKFLOW_ID=8789
WORFKLOW_VERSION_MIN=237.7


###################################
# Pilanesberg
####################################

cd $HOME/snapshot_safari_misc
SITE=PLN
SEASON=PLN_S1
PROJECT_ID=6190
WORKFLOW_ID=7764
WORFKLOW_VERSION_MIN=311.5

###################################
# Cedar Creek
####################################

cd $HOME/snapshot_safari_misc
SITE=CC
SEASON=CC_S1
PROJECT_ID=5880
WORKFLOW_ID=5702
WORFKLOW_VERSION_MIN=289


###################################
# Snapshot Serengeti
####################################

cd $HOME/snapshot_safari_misc
SITE=SER
SEASON=SER_S11
PROJECT_ID=4996
WORKFLOW_ID=4655
WORFKLOW_VERSION_MIN=304


###################################
# ENO
####################################

cd $HOME/snapshot_safari_misc
SITE=ENO
SEASON=ENO_S1
PROJECT_ID=
WORKFLOW_ID=
WORFKLOW_VERSION_MIN=

# TEST
cd $HOME/snapshot_safari_misc
SITE=ENO
SEASON=ENO_S1_TEST_CANBEDELETED
PROJECT_ID=
WORKFLOW_ID=
WORFKLOW_VERSION_MIN=



###################################
# APN
####################################


cd $HOME/snapshot_safari_misc
SITE=APN
SEASON=APN_S1
PROJECT_ID=5561
WORKFLOW_ID=5719
WORFKLOW_VERSION_MIN=159.9


cd $HOME/snapshot_safari_misc
SITE=APN
SEASON=APN_S2
PROJECT_ID=
WORKFLOW_ID=
WORFKLOW_VERSION_MIN=


###################################
# Python Prep
####################################

qsub -I -l walltime=6:00:00,nodes=1:ppn=4,mem=16gb
module load python3
cd $HOME/snapshot_safari_misc
git pull


###################################
# Pre-Processing
####################################

# Check Input Structure
python3 -m pre_processing.check_input_structure \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/

# Create Image Inventory
python3 -m pre_processing.create_image_inventory \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_inventory.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--n_processes 16

# Group Images into Captures
python3 -m pre_processing.group_inventory_into_captures \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_inventory.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--no_older_than_year 2017 \
--no_newer_than_year 2019

# rename all images
python3 -m pre_processing.rename_images \
--inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/

# generate action list
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/ \
--plot_timelines

# generate actions
python3 -m pre_processing.generate_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--action_list /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list.csv \
--actions_to_perform_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/

# apply actions
python3 -m pre_processing.apply_actions \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--actions_to_perform /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_actions_to_perform.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/

# Update Captures
python3 -m pre_processing.update_captures \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures.csv \
--captures_updated /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/

cp /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_captures_cleaned.csv

# generate action list - (OPTIONAL)
python3 -m pre_processing.create_action_list \
--captures /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_updated.csv \
--action_list_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_action_list2.csv \
--log_dir /home/packerc/shared/season_captures/${SITE}/log_files/


###################################
# Zooniverse Uploads
####################################

# generate manifest
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--log_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
--manifest_id ${SEASON} \
--attribution ${ATTRIBUTION} \
--license ${LICENSE}

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

# Get Zooniverse Classification Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--export_type classifications \
--new_export 0

# Get Zooniverse Subject Data
python3 -m zooniverse_exports.get_zooniverse_export \
--password_file ~/keys/passwords.ini \
--project_id $PROJECT_ID \
--output_file /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--export_type subjects \
--new_export 0

# Extract Annotations from Classifications
python3 -m zooniverse_exports.extract_annotations \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORFKLOW_VERSION_MIN

# Extract Subject Data
python3 -m zooniverse_exports.extract_subjects \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv


###################################
# Zooniverse Aggregations
####################################

# Aggregate Classifications
python3 -m zooniverse_aggregations.aggregate_annotations_plurality \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--log_dir /home/packerc/shared/zooniverse/Aggregations/${SITE}/ \
--export_consensus_only \
--export_sample_size 300

# Add subject data to Aggregations
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv

# OPTIONAL - Add subject data to Aggregations Samples
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples_subject_info.csv


###################################
# Reporting
####################################

# Reporting of Zooniverse exports
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_all.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON}

# Reporting of Zooniverse exports - only captures with annotations
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_with_aggregations \
--deduplicate_subjects

# Reporting of Zooniverse exports - only captures with annotations and samples
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_samples.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_with_aggregations \
--deduplicate_subjects

# Reporting of Zooniverse exports - only captures with species
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_species.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_species \
--deduplicate_subjects


# python3 -m reporting.add_aggregations_to_season_captures \
# --season_captures_csv '/home/isbell/shared/Snapshot Cedar Creek Images/CC_S01_cleaned_captures.csv' \
# --aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_subject_info.csv \
# --output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_zooniverse.csv \
# --default_season_id ${SEASON}


# Create Flattened ML Predictions
python3 -m reporting.flatten_ml_predictions \
--predictions_empty /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_empty_or_not.json \
--predictions_species /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_species.json \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_ml_preds_flat.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/

# Prepare Reporting of Machine-Learning Predictions
python3 -m reporting.manifest_predictions_to_csv \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}__complete__machine_learning.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/


# Reporting of Machine Learning Predictions
python3 -m reporting.add_predictions_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--predictions_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}__complete__machine_learning.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_machine_learning.csv


###################################
# Snapshot Serengeti - Legacy
####################################

qsub -I -l walltime=10:00:00,nodes=1:ppn=4,mem=16gb
module load python3

cd $HOME/snapshot_safari_misc
SITE=SER
SEASON=SER_S1
SEASON_STRING='1'

# Extract Annotations
python3 -m zooniverse_exports.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process ${SEASON_STRING}


# Aggregate Annotations
python3 -m zooniverse_aggregations.aggregate_annotations_plurality \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--log_dir /home/packerc/shared/zooniverse/Aggregations/${SITE}/ \
--export_consensus_only \
--export_sample_size 300


# Extract Subjects from Classifications
python3 -m zooniverse_exports.extract_subjects_legacy \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--log_dir /home/packerc/shared/zooniverse/Exports/${SITE}/

# Get Subject URLs from Zooniverse API (warning - takes a long time)
python3 -m zooniverse_exports.get_legacy_subject_urls \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--subjects_urls /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subject_urls.csv

python3 -m zooniverse_exports.get_legacy_ouroboros_data \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--subjects_ouroboros /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_ouroboros.json

# Re-Create Season Captures
python3 -m zooniverse_exports.recreate_legacy_season_captures \
--subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv

# Add subject data to Aggregations
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv

# Add subject data to Aggregations (samples)
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info_samples.csv


###################################
# Reporting
####################################

python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_species.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_species \
--deduplicate_subjects



###################################
# Bulk Processing
####################################

# Loop over all seasons
for season in 1 2 3 4 5 6 7 8 9; do
  SITE=SER
  SEASON=SER_S${season}
  python3 -m zooniverse_exports.extract_legacy_serengeti \
  --classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
  --output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
  --season_to_process S${season}
done

python3 -m zooniverse_exports.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process '10'

# Aggregate Annotations
python3 -m zooniverse_aggregations.aggregate_annotations_plurality \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
--log_dir /home/packerc/shared/zooniverse/Aggregations/${SITE}/ \
--export_consensus_only \
--export_sample_size 300

# Loop over all seasons
for season in 1 2 3 4 5 6 7 8 9 10; do
  SITE=SER
  SEASON=SER_S${season}

  # Extract Subjects from Classifications
  python3 -m zooniverse_exports.extract_subjects_legacy \
  --annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
  --output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
  --log_dir /home/packerc/shared/zooniverse/Exports/${SITE}

  # Re-Create Season Captures
  python3 -m zooniverse_exports.recreate_legacy_season_captures \
  --subjects_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
  --output_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv

  # Add subject data to Aggregations
  python3 -m zooniverse_exports.add_subject_info_to_csv \
  --subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
  --input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated.csv \
  --output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv

  # Add subject data to Aggregations (samples)
  python3 -m zooniverse_exports.add_subject_info_to_csv \
  --subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
  --input_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples.csv \
  --output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info_samples.csv
done
