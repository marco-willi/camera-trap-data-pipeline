python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_workflows.csv \
4255 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_extraction.csv

python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/question_extractor_4715_extraction.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/4715_reduction.csv



# Snapshot Serengeti
cd /home/packerc/shared/machine_learning/will5448/code/aggregation-for-caesar
python3 extract_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/classifications.csv \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/workflows.csv \
4655 \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/extraction.csv


python3  reduce_panoptes_csv.py \
/home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/survey_extractor_extraction.csv \
-o /home/packerc/shared/machine_learning/will5448/data/zooniverse_exports/SER/reduction.csv
