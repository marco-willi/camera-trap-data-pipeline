# Reporting

The following codes can be used to:

1. Merge season captures with Zooniverse aggregations
2. Merge season captures with Machine Learning predictions


## Merge Season Captures with Zooniverse Aggregations

```
python3 -m reporting.add_aggregations_to_season_captures \
        --season_captures_csv /home/packerc/shared/season_captures/GRU/cleaned/GRU_S1_cleaned.csv \
        --aggregated_csv /home/packerc/shared/zooniverse/Exports/GRU/GRU_S1_classifications_aggregated_subject_info.csv \
        --output_csv /home/packerc/shared/zooniverse/Reports/GRU/GRU_S1_report_zooniverse.csv
```

## Output Fields

The following file contains one record per capture event and species detection. Primary-key is 'subject_id' and 'question__species'.

| Columns   | Description |
| --------- | ----------- |
|capture_id, season, roll, site, capture | internal identifiers of the capture
|capture_date_local | local date (YYYY-MM-DD) of the capture
|capture_time_local | local time (HH:MM:SS) of the capture
|subject_id | Zooniverse subject_id (per capture)
|retirement_reason | Zooniverse retirement reason
|retired_at | Zooniverse date when retired
|zooniverse_url_*| Zooniverse image links of the capture (if uploaded)
|question__* | Aggregated question answers
|n_users_identified_this_species | Number of users that identified 'question__species'
|p_users_identified_this_species | Proportion of users that identified 'question__species'
|n_species_ids_per_user_median | Median number of different species identified among users for this capture
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
