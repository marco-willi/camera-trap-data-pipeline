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
# Pilanesberg
####################################

cd $HOME/snapshot_safari_misc
SITE=PLN
SEASON=PLN_S1
PROJECT_ID=6190
WORKFLOW_ID=
WORFKLOW_VERSION_MIN=

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


###################################
# SCRIPTS
####################################

# Data processing
python3 -m pre_processing.check_input_structure \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--log_dir /home/packerc/shared/season_captures/${SITE}/captures/

# Create Image Inventory
python3 -m pre_processing.create_input_inventory_parallel \
--root_dir /home/packerc/shared/albums/${SITE}/${SEASON}/ \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_raw.csv \
--n_processes 16

# Group Images into Captures
python3 -m pre_processing.group_inventory_into_captures \
--input_inventory /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_raw.csv \
--output_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_grouped.csv


# Find potential issues
python3 -m pre_processing.export_checks_for_inspection \
--inventory_grouped /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_captures_grouped.csv \
--issues_csv /home/packerc/shared/season_captures/${SITE}/captures/${SEASON}_potential_issues.csv \
--no_older_than_year 2017 \
--no_newer_than_year 2019 \
--plot_timelines


# generate manifest
python3 -m zooniverse_uploads.generate_manifest \
--captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--compressed_image_dir /home/packerc/shared/zooniverse/ToUpload/${SITE}/${SEASON}_Compressed/ \
--output_manifest_dir /home/packerc/shared/zooniverse/Manifests/${SITE}/ \
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
--max_batch_size 20000

# Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id 5115 \
--password_file ~/keys/passwords.ini

# Retry Upload manifest
python3 -m zooniverse_uploads.upload_manifest \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__batch_1__manifest.json \
--project_id ${PROJECT_ID} \
--subject_set_id $SUBJECT_SET_ID \
--password_file ~/keys/passwords.ini

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

# Extract Classification Data
python3 -m zooniverse_exports.extract_classifications \
--classification_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
--workflow_id $WORKFLOW_ID \
--workflow_version_min $WORFKLOW_VERSION_MIN

# Extract Subject Data
python3 -m zooniverse_exports.extract_subjects \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv

# Aggregate Classifications
python3 -m zooniverse_aggregations.aggregate_classifications_plurality \
--classifications_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated.csv \
--export_consensus_only \
--export_sample_size 300

# Add subject data to Aggregations
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_subject_info.csv

# OPTIONAL - Add subject data to Aggregations Samples
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_samples.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_samples_subject_info.csv

# Reporting of Zooniverse exports
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_zooniverse.csv \
--default_season_id ${SEASON}


# python3 -m reporting.add_aggregations_to_season_captures \
# --season_captures_csv '/home/isbell/shared/Snapshot Cedar Creek Images/CC_S01_cleaned_captures.csv' \
# --aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_subject_info.csv \
# --output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_zooniverse.csv \
# --default_season_id ${SEASON}

# Prepare Reporting of Machine-Learning Predictions
python3 -m reporting.manifest_predictions_to_csv \
--manifest /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}__complete__manifest.json \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}__complete__machine_learning.csv

# Reporting of Machine Learning Predictions
python3 -m reporting.add_predictions_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--predictions_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}__complete__machine_learning.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_machine_learning.csv


###################################
# Snapshot Serengeti - Legacy
####################################

qsub -I -l walltime=10:00:00,nodes=1:ppn=4,mem=16gb
module load python3

cd $HOME/snapshot_safari_misc
SITE=SER
SEASON=SER_S1
SEASON_STRING='S1'

# Extract Classifications
python3 -m zooniverse_exports.extract_legacy_serengeti \
--classification_csv '/home/packerc/shared/zooniverse/Exports/SER/2019-01-27_serengeti_classifications.csv' \
--output_path '/home/packerc/shared/zooniverse/Exports/SER/' \
--season_to_process ${SEASON_STRING}


# Aggregate Classifications
python3 -m zooniverse_aggregations.aggregate_classifications_plurality \
--classifications_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated.csv \
--export_consensus_only \
--export_sample_size 300


# Extract Subjects from Classifications
python3 -m zooniverse_exports.extract_subjects_legacy \
--classifications_extracted /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv


# Add subject data to Aggregations
python3 -m zooniverse_exports.add_subject_info_to_csv \
--subject_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--input_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated.csv \
--output_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_classifications_aggregated_subject_info.csv
