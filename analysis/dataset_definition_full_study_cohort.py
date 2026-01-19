# #############################################################################
# Number of migrants in OpenSAFELY-TPP from 2009-2025
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

# This is a script to explore the migration status of all individuals who were:
#         1) registered at anytime (2009-2025) AND
#         2) do not have a disclosive sex AND
#         4) alive on 1st Jan 2009 AND 
#         4) had a plausible age at the beginning of the study period  (i.e. not >110 years old in 2009)

from pathlib import Path

from ehrql import create_dataset, codelist_from_csv, show, case, when
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
import codelists
import migration_status_variables

# Dates

study_start_date = "2009-01-01"
study_end_date = "2025-10-17" # based on what I think is the latest data available, using the latest report run date here: https://reports.opensafely.org/reports/opensafely-tpp-database-history/#CodedEvent

is_registered_during_study = (
    practice_registrations
    .where((practice_registrations.end_date.is_null()) | ((practice_registrations.end_date.is_on_or_before(study_end_date)) & (practice_registrations.end_date.is_after(study_start_date))))
    .exists_for_patient()
)           

has_non_disclosive_sex = (
    (patients.sex == "male") | (patients.sex == "female")
)

is_alive_at_study_start = (
    ((patients.date_of_death > study_start_date) | (patients.date_of_death.is_null())) &
    ((ons_deaths.date > study_start_date) | (ons_deaths.date.is_null()))
)

was_not_over_110_at_study_start = (
    patients.age_on(study_start_date) <= 110
)

dataset = create_dataset()
dataset.define_population(is_registered_during_study & 
                          has_non_disclosive_sex & 
                          is_alive_at_study_start & 
                          was_not_over_110_at_study_start)

# add variables 

## year of birth
year_of_birth = (patients.date_of_birth).year
dataset.year_of_birth = year_of_birth

dataset.year_of_birth_band = case(
    when((year_of_birth >= 1900) & (year_of_birth <= 1925)).then("1900-1925"),
    when((year_of_birth > 1925) & (year_of_birth <= 1945)).then("1926-1945"),
    when((year_of_birth > 1945) & (year_of_birth <= 1965)).then("1946-1965"),
    when((year_of_birth > 1965) & (year_of_birth <= 1985)).then("1966-1985"),
    when((year_of_birth > 1985) & (year_of_birth <= 2005)).then("1986-2005"),
    when((year_of_birth > 2005) & (year_of_birth <= 2025)).then("2006-2025") 
)

## sex

dataset.sex = patients.sex

## ethnicity

latest_ethnicity_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(codelists.ethnicity_16_level_codelist))
    .where(clinical_events.date.is_on_or_before(study_end_date)) # maybe this is redundant?
    .sort_by(clinical_events.date)
    .last_for_patient()
    .snomedct_code)
dataset.latest_ethnicity_code = latest_ethnicity_code

latest_ethnicity_16_level_group = latest_ethnicity_code.to_category(
    codelists.ethnicity_16_level_codelist)
dataset.latest_ethnicity_16_level_group = latest_ethnicity_16_level_group

latest_ethnicity_6_level_group = latest_ethnicity_code.to_category(
    codelists.ethnicity_6_level_codelist)
dataset.latest_ethnicity_6_level_group = latest_ethnicity_6_level_group

## practice region (latest during the study period)

dataset.region = practice_registrations.for_patient_on(study_end_date).practice_nuts1_region_name

## imd

address = addresses.for_patient_on(study_end_date) 

dataset.imd_decile = address.imd_decile
dataset.imd_quintile = address.imd_quintile

## date of first practice registration

date_of_first_practice_registration = (
    practice_registrations.sort_by(practice_registrations.start_date)
    .first_for_patient().start_date
)
dataset.date_of_first_practice_registration = date_of_first_practice_registration

# migration status 

migrant_indicators = migration_status_variables.build_migrant_indicators(study_end_date)

for name, indicator in migrant_indicators.items():
    setattr(dataset, name, indicator)

## consolidate migration indiciators into 2-cat, 3-cat and 6-cat variables

dataset.mig_status_2_cat = migration_status_variables.build_mig_status_2_cat(migrant_indicators)

dataset.mig_status_3_cat = migration_status_variables.build_mig_status_3_cat(
    migrant_indicators,
    dataset.latest_ethnicity_16_level_group
)

dataset.mig_status_6_cat = migration_status_variables.build_mig_status_6_cat(
    migrant_indicators,
    dataset.latest_ethnicity_16_level_group
)

# number of migration codes per person

number_of_migration_codes = (
    clinical_events
            .where(clinical_events.snomedct_code.is_in(codelists.all_migrant_codes))
            .where(clinical_events.date.is_on_or_before(study_end_date))
            .count_for_patient()
)
dataset.number_of_migration_codes = number_of_migration_codes

number_of_migration_codes_at_any_time = (
    clinical_events
            .where(clinical_events.snomedct_code.is_in(codelists.all_migrant_codes))
            .count_for_patient()
)
dataset.number_of_migration_codes_at_any_time = number_of_migration_codes

# date of entry to the UK (SNOMED CT code: 860021000000109)

## has date of entry to the UK code 

date_of_entry_code = ["860021000000109"]

has_date_of_uk_entry_at_any_time = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(date_of_entry_code))
    .exists_for_patient()
)
dataset.has_date_of_uk_entry_at_any_time = has_date_of_uk_entry_at_any_time

has_date_of_uk_entry = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(date_of_entry_code))
    .where(clinical_events.date.is_on_or_before(study_end_date))
    .exists_for_patient()
)
dataset.has_date_of_uk_entry = has_date_of_uk_entry

## number of uses of date of entry to the UK code 

dataset.number_of_date_of_uk_entry_codes = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(date_of_entry_code))
    .where(clinical_events.date.is_on_or_before(study_end_date))
    .count_for_patient()
)

dataset.number_of_date_of_uk_entry_codes_at_any_time = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(date_of_entry_code))
    .count_for_patient()
)

## date associated with earliest date of entry to the UK code 

date_of_earliest_date_of_uk_entry_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(date_of_entry_code))
    .sort_by(clinical_events.date)
    .first_for_patient().date)
dataset.date_of_earliest_date_of_uk_entry_code = date_of_earliest_date_of_uk_entry_code

## temporality of earliest date of entry to the UK code in relation to first practice registration date

dataset.temporality_of_date_of_uk_entry_code = case(
    when((date_of_earliest_date_of_uk_entry_code.is_null())).then("Missing"), 
    when((date_of_earliest_date_of_uk_entry_code < date_of_first_practice_registration)).then("Before first practice registration"),
    when((date_of_earliest_date_of_uk_entry_code >= date_of_first_practice_registration)).then("On or after first practice registration")
)

## number of individuals with a date of entry code and any other migration-related code 

dataset.date_of_entry_and_other_migration_code = case(
    when((has_date_of_uk_entry == True) & (number_of_migration_codes > 0)).then("True"),
    otherwise="False"
)

# time from first practice registration to first migration code 

date_of_first_migration_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(codelists.all_migrant_codes))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.date_of_first_migration_code = date_of_first_migration_code

time_to_first_migration_code  = (date_of_first_migration_code - date_of_first_practice_registration).days

dataset.time_to_first_migration_code = time_to_first_migration_code

dataset.configure_dummy_data(population_size=1000)
show(dataset)


