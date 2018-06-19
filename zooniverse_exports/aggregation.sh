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



# write_first_nrows_of_csv_to_csv('/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications.csv', '/home/packerc/shared/machine_learning/data/zooniverse_exports/GRU/GRU_S1/classifications_sampled.csv', 50000)
