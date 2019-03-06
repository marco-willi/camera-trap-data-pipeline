# Reporting

The following codes can be used to:

1. Merge season captures with Zooniverse aggregations
2. Merge season captures with Machine Learning predictions

The following codes show an example for Grumeti:

```
cd $HOME/snapshot_safari_misc
SITE=GRU
SEASON=GRU_S1
```

## Merge Season Captures with Aggregated Annotations

The following reports can be generated:
```
# Reporting of Zooniverse exports
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_all.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON}

# Reporting of Zooniverse exports - only captures with annotations
# deduplicate captures with more than one subject id
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_with_aggregations \
--deduplicate_subjects

# Reporting of Zooniverse exports - only captures with annotations and samples
# deduplicate captures with more than one subject id
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_samples_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_samples.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_with_aggregations \
--deduplicate_subjects

# Reporting of Zooniverse exports - only captures with species
# deduplicate captures with more than one subject id
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_species.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--default_season_id ${SEASON} \
--export_only_species \
--deduplicate_subjects
```

To de-duplicate capture ids with more than one subject (if accidentally uploaded more than once to Zooniverse) -- deleting some subject ids:
```
--deduplicate_subjects
```

To export only species detections (no blanks):
```
--export_only_species
```

To export only with Zooniverse aggregations (otherwise also include captures without Zooniverse data):
```
--export_only_with_aggregations
```

## Output Fields

The following file contains one record per capture event and species detection. Primary-key is 'subject_id' and 'question__species'.

| Columns   | Description |
| --------- | ----------- |
|capture_id, season, roll, site, capture | internal identifiers of the capture
|capture_date_local | local date (YYYY-MM-DD) of the capture
|capture_time_local | local time (HH:MM:SS) of the capture
|subject_id | Zooniverse subject_id (unique per capture)
|retirement_reason | Zooniverse retirement reason
|created_at | Zooniverse date when the capture was uploaded
|retired_at | Zooniverse date when the capture was retired
|zooniverse_url_*| Zooniverse image links of the capture (if uploaded)
|question__* | Aggregated question answers, fractions, labels or counts
|n_users_identified_this_species | Number of users that identified 'question__species'
|p_users_identified_this_species | Proportion of users that identified 'question__species'
|n_species_ids_per_user_median | Median number of different species identified among users who identified at least one species for this capture
|n_users_saw_a_species| Number of users who saw/id'd at least one species.
|n_users_saw_no_species| Number of users who saw/id'd no species.
|p_users_saw_a_species| Proportion of users who saw/id'd a species.
|pielous_evenness_index| The Pielou Evenness Index or 0 for unanimous vote
|n_users_classified_this_subject | Number of users that classified this subject
|species_is_plurality_consensus | Flag indicating a plurality consensus for this species (normally only species with a 1 are relevant)

## Merge Season Captures with Machine Predictions

Generate a csv with all machine learning predictions, one record per capture-id.

```
# Create Flattened ML Predictions
python3 -m reporting.flatten_ml_predictions \
--predictions_empty /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_empty_or_not.json \
--predictions_species /home/packerc/shared/zooniverse/Manifests/${SITE}/${SEASON}_predictions_species.json \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_ml_preds_flat.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/
```

Merge the machine learning predictions with the season captures.
```
# Reporting of Machine Learning Predictions
python3 -m reporting.add_predictions_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--predictions_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_ml_preds_flat.csv \
--output_csv /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/${SEASON}_report_ml.csv \
--log_dir /home/packerc/shared/zooniverse/ConsensusReports/${SITE}/ \
--export_only_with_predictions
```

The following file contains one record per capture event. Primary key is 'capture_id'.

| Columns   | Description |
| --------- | ----------- |
|capture_id, season, roll, site, capture | internal identifiers of the capture
|capture_date_local | local date (YYYY-MM-DD) of the capture
|capture_time_local | local time (HH:MM:SS) of the capture
|machine_confidence_empty| confidence of the image being empty / blank
|machine_confidence_species| confidence of the image containing a species
|machine_topprediction_(label)| the models top prediction for (label), e.g., '5' for the 'count' label
|machine_confidence_count_(num) | Confidence of the model of (num) species being present in the image.
|machine_confidence_(behavior) | Confidence of predicted behavior (0-1)
|machine_confidence_species_(species)| Confidence of (species) being present in the image (0-1)
