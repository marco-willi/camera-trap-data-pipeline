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
# Reporting of Zooniverse exports - only captures with species
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_species.csv \
--default_season_id ${SEASON} \
--export_only_species

# Reporting of Zooniverse exports - all captures from the season file
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_all.csv \
--default_season_id ${SEASON}

# Reporting of Zooniverse exports - only captures with annotations
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations_aggregated_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report.csv \
--default_season_id ${SEASON} \
--export_only_with_aggregations

# Reporting of Zooniverse exports - only captures with annotations and samples
python3 -m reporting.add_aggregations_to_season_captures \
--season_captures_csv /home/packerc/shared/season_captures/${SITE}/cleaned/${SEASON}_cleaned.csv \
--aggregated_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations_aggregated_samples_subject_info.csv \
--output_csv /home/packerc/shared/zooniverse/Reports/${SITE}/${SEASON}_report_samples.csv \
--default_season_id ${SEASON} \
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

Generate a csv with all machine learning predictions.

```
python3 -m reporting.manifest_predictions_to_csv \
--manifest /home/packerc/shared/zooniverse/Manifests/GRU/GRU_S1__complete__manifest.json \
--output_csv /home/packerc/shared/zooniverse/Reports/GRU/GRU_S1__complete__machine_learning.csv
```

Merge the machine learning predictions with the season captures.
```
python3 -m reporting.add_predictions_to_season_captures \
        --season_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_subjects_extracted.csv \
        --predictions_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated_samples.csv \
        --output_csv /home/packerc/shared/zooniverse/Reporting/GRU/GRU_S1_report_zooniverse.csv
```

The following file contains one record per capture event. Primary key is 'capture_id'.

| Columns   | Description |
| --------- | ----------- |
|capture_id, season, roll, site, capture | internal identifiers of the capture
|capture_date_local | local date (YYYY-MM-DD) of the capture
|capture_time_local | local time (HH:MM:SS) of the capture
|machine_prediction_empty | 'empty' if machine predicts empty image, or 'species' if machine thinks species is present
|machine_confidence_empty | Confidene of 'empty'/'species' prediction
|machine_prediction_species| Species with the highest probability of being present.
|machine_confidence_species| Confidence for the species with the highest probability of being present.
|machine_prediction_(behavior) | Prediction of a behavior being present (1 for yes, 0 for no)
|machine_confidence_(behavior) | Confidence of predicted behavior (1 for yes, 0 for no)
|machine_prediction_count | Prediction of a behavior being present (1 for yes, 0 for no)
|machine_confidence_(behavior) | Confidence of predicted behavior (1 for yes, 0 for no)
|machine_prediction_(species)| Confidence of (species) being present in the image
