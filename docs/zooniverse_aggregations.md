 # Aggregate Zooniverse Classifications

The following codes aggregate extracted annotations (essentially species identifications made by individual users).

The general aggregation logic (plurality algorithm) is as follows:

1. Group / collect all annotations of a specific subject (a capture event)
2. For each subject determine whether the majority of users identified a species or not (empty image).
3. If the majority identified no species, the consensus label is 'blank', otherwise proceed.
4. For each species calculate the following stats:
  - how many users identified it (and proportion)
  - calculate among the users who identified the species the proportions of users who identified a certain characteristic (e.g. 0.9 may identified a 'moving' behavior)
  - calculate among the users who identified the species the median number of counts/number of animals (round up)
  - characteristics that were not asked for or no user answered are indicated by an empty string: ''
3. Calculate the median over the number of different species identified by each user who identified at least one species (round up on ties).
4. Flag the top N species (median number of different species identified) with 'species_is_plurality_consensus'. Choose the first species identified by any users on ties.
5. Export the full dataset including species without consensus, blanks, and additional information.

## Output Fields

| Columns   | Description |
| --------- | ----------- |
|season, roll, site, capture  | internal identifiers of the capture
|subject_id | Zooniverse subject_id (per capture)
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

## Aggregate Annotations (plurality algorithm)

This is an example to aggregate annotations using the plurality algorithm.

```
python3 -m zooniverse_aggregations.aggregate_annotations_plurality \
--annotations /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_annotations.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_plurality.csv \
--log_dir /home/packerc/shared/zooniverse/Aggregations/${SITE}/
```

## Add subject data to Aggregations

This scripts adds subject data to the export.

```
python3 -m zooniverse_exports.merge_csvs \
--base_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_plurality.csv \
--to_add_csv /home/packerc/shared/zooniverse/Exports/${SITE}/${SEASON}_subjects_extracted.csv \
--output_csv /home/packerc/shared/zooniverse/Aggregations/${SITE}/${SEASON}_annotations_aggregated_plurality_info.csv \
--key subject_id
```
