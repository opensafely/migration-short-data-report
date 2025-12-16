## Script to generate a migration event-level dataset for migrants
## that has a row per individual per migration-related code 
## Author: Yamina Boukari
####

from ehrql import Dataset, days, years, when, case

from ehrql.tables.tpp import (
  clinical_events
)

from analysis.codelists import *

from analysis.scrapyard.dataset_definition_full_study_cohort import dataset

# all migration-related codes 
migration_related_codes = (
  clinical_events
  .where(clinical_events.snomedct_code.is_in(all_migrant_codes))
  .sort_by(clinical_events.date)
)

dataset.add_event_table(
  "migration_related_codes",
  date=migration_related_codes.date,
  snomedct_code=migration_related_codes.snomedct_code,
  migration_category=case(
    when(migration_related_codes.snomedct_code.is_in(language_migrant_codes)).then("Main/first language is not English"),
    when(migration_related_codes.snomedct_code.is_in(interpreter_migrant_codes)).then("Interpreter required"),
    when(migration_related_codes.snomedct_code.is_in(asylum_refugee_migrant_codes)).then("Asylum or refugee status"),
    when(migration_related_codes.snomedct_code.is_in(cob_migrant_codes)).then("Country of birth")))

dataset.migration_related_codes.migration_category = (
    dataset.migration_related_codes.migration_category.fill_null("Other")
)
