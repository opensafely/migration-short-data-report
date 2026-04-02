# #############################################################################
# Number of migrants in OpenSAFELY-TPP from 2009-2025
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

# This is a script to create a cohort of individuals who had a migration code before their birth 
#         1) registered at anytime (2009-2025) AND
#         2) do not have a disclosive sex AND
#         4) did not die before or on 1st Jan 2009 (study start) AND 
#         5) had a plausible age at the beginning of the study period  (i.e. not >110 years old in 2009)
#         6) had a migration code before their birth

from pathlib import Path

from ehrql import create_dataset, codelist_from_csv, show, case, when, days
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
import codelists
import migration_status_variables

# Dates

study_start_date = "2009-01-01"
study_end_date = "2025-10-17" # based on what I think is the latest data available, using the latest report run date here: https://reports.opensafely.org/reports/opensafely-tpp-database-history/#CodedEvent

is_registered_at_any_time_during_study = practice_registrations.where(
  # starting during period
  practice_registrations.start_date.is_on_or_between(study_start_date, study_end_date) |
  
  # ending during period
  practice_registrations.end_date.is_on_or_between(study_start_date, study_end_date) | 
  
  # starting before and ending after
  (
    practice_registrations.start_date.is_on_or_before(study_start_date) &
    (practice_registrations.end_date.is_on_or_after(study_end_date + days(1)) | practice_registrations.end_date.is_null())
  )
)

has_non_disclosive_sex = (
    (patients.sex == "male") | (patients.sex == "female")
)

did_not_die_before_study_start = (
    ((patients.date_of_death > study_start_date) | (patients.date_of_death.is_null())) &
    ((ons_deaths.date > study_start_date) | (ons_deaths.date.is_null()))
)

was_not_over_110_at_study_start_or_less_than_0_at_end_date = (
    (patients.age_on(study_start_date) <= 110) | (patients.age_on(study_end_date) >= 0)
)

dataset = create_dataset()
dataset.define_population(is_registered_at_any_time_during_study.exists_for_patient() & 
                          has_non_disclosive_sex & 
                          did_not_die_before_study_start & 
                          was_not_over_110_at_study_start_or_less_than_0_at_end_date)

migrant_indicators = migration_status_variables.build_migrant_indicators(patients.date_of_birth)

for name, indicator in migrant_indicators.items():
    setattr(dataset, name, indicator)


