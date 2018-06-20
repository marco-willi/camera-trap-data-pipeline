python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_workflows.csv \
4255 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_extraction.csv

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/question_extractor_4715_extraction.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_reduction.csv


###################################
# Snapshot Serengeti
####################################

cd /home/packerc/shared/machine_learning/will5448/code/snapshot_safari_misc
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
-output_file  /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/SER_S11_predictions.json \
-label_mapping_path /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/label_mapping.json



# Simulate Different Aggregations
python3 -m zooniverse_exports.simulate_aggregations_ml \
-classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/classifications_extracted.csv \
-output_csv /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/SER_S11/classifications_aggregated_ml_ \
-aggregated_predictions /home/packerc/shared/machine_learning/data/zooniverse_exports/SER/SER_S11/SER_S11_predictions.json


-root_path /home/packerc/shared/zooniverse/ZOOIDs/SER/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/SER/SER_S11/SER_S11_all.csv \
-files SER_S11_1_ZOOID_v0.csv SER_S11_2_ZOOID_v0.csv \
-path_field path


###################################
# Ruaha
####################################

cd /home/packerc/shared/machine_learning/will5448/code/snapshot_safari_misc
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications.csv \
        -output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_extracted.csv \
        -workflow_id 4889 \
        -workflow_version 797

python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_extracted.csv \
          -output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_aggregated.csv


python3 -m zooniverse_exports.extract_choices_from_workflow \
  -workflow_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/workflows.csv \
  -output /home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/label_mapping.json


# write_first_nrows_of_csv_to_csv('/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications.csv', '/home/packerc/shared/machine_learning/data/zooniverse_exports/RUA/RUA_S1/classifications_sampled.csv', 50000)

cd /home/packerc/shared/machine_learning/will5448/code/snapshot_safari_misc

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
-files RUA_S1_A1_ZOOID.csv RUA_S1_A2_ZOOID.csv \
-path_field path



###################################
# Grumeti
####################################

cd /home/packerc/shared/machine_learning/will5448/code/snapshot_safari_misc
python3 -m zooniverse_exports.extract_classifications \
        -classification_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications.csv \
        -output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_extracted.csv \
        -workflow_id 4979 \
        -workflow_version 275

python3 -m zooniverse_exports.aggregate_extractions \
          -classifications_extracted /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_extracted.csv \
          -output_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_aggregated.csv


python3 -m zooniverse_exports.extract_choices_from_workflow \
  -workflow_csv /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/workflows.csv \
  -output /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/label_mapping.json


python3 -m zooniverse_exports.create_image_to_label \
-zooid_path /home/packerc/shared/zooniverse/ZOOIDs/GRU/ \
-manifest_path /home/packerc/shared/zooniverse/Manifests/GRU/ \
-zoo_exports_path /home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/ \
-ml_info_path /home/packerc/shared/machine_learning/data/info_files/GRU/GRU_S1/ \
-manifest_files GRU_S1_manifest_v1 \
-zooid_files GRU_S1_ZOOID.csv \
-season_id GRU_S1


# Generate Info Files from ZOOID files for prediction
python3 -m zooniverse_exports.generate_predict_file_from_zooids \
-root_path /home/packerc/shared/zooniverse/ZOOIDs/GRU/ \
-output_file /home/packerc/shared/machine_learning/data/info_files/GRU/GRU_S1/GRU_S1_all.csv \
-files GRU_S1_ZOOID.csv \
-path_field path



# write_first_nrows_of_csv_to_csv('/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications.csv', '/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_sampled.csv', 50000)
