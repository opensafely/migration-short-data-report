# This is a script to create a cohort with basic demographics in order to carry out a survival analysis looking at time from first practice registration to first migration code:
# - Select anyone with 
#         2) who was registered at any time during the study period (2009-2024) AND
#         3) who does not have a disclosive sex AND
#         4) had not died before the start of the study period AND 
#         5) was not over 100 years old at the start of the study period

from ehrql import create_dataset, codelist_from_csv, show, case, when, days, minimum_of
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
from datetime import date, datetime

all_migrant_codes = codelist_from_csv(
    "codelists/user-YaminaB-migration-status.csv", column="code"
)

# Dates

study_start_date = "2009-01-01"
study_end_date = "2024-12-31"

# Dataset definitions

is_registered_during_study = (practice_registrations.where((practice_registrations.start_date.is_on_or_before(study_start_date) | 
                                    practice_registrations.start_date.is_between_but_not_on(study_start_date, study_end_date)) &
                                    ((practice_registrations.end_date.is_null()) | 
                                     (practice_registrations.end_date.is_between_but_not_on(study_start_date, study_end_date)) |
                                     (practice_registrations.end_date.is_on_or_after(study_end_date)))
).exists_for_patient())           

has_non_disclosive_sex = (
    (patients.sex == "male") | (patients.sex == "female")
)

is_alive_at_study_start = (
    ((patients.date_of_death >= study_start_date) | (patients.date_of_death.is_null())) &
    ((ons_deaths.date >= study_start_date) | (ons_deaths.date.is_null()))
)

was_not_over_100_at_study_start = (
    patients.age_on(study_start_date) <= 100
)

dataset = create_dataset()
dataset.define_population(is_registered_during_study & 
                          has_non_disclosive_sex & 
                          is_alive_at_study_start & 
                          was_not_over_100_at_study_start)

# Add required variables

## Date of first GP registration 

date_of_first_practice_registration = (
    practice_registrations.sort_by(practice_registrations.start_date)
    .first_for_patient().start_date
)

dataset.date_of_first_practice_registration = date_of_first_practice_registration

# Baseline date is date_of_first_practice_registration minus 1 day
# because we assume that any migration code recorded on date of practice registration
# occured after registration.

dataset.baseline_date = date_of_first_practice_registration - days(1)

## De-registration date 

def date_deregistered_from_all_supported_practices():
    max_dereg_date = practice_registrations.end_date.maximum_for_patient()
    # In TPP currently active registrations are recorded as having an end date of
    # 9999-12-31. We convert these, and any other far-future dates, to NULL.
    return case(
        when(max_dereg_date.is_before("3000-01-01")).then(max_dereg_date),
        otherwise=None,
    )

dataset.date_of_deregistration = date_deregistered_from_all_supported_practices()

show(dataset)

# Add date of death (if died)

dataset.TPP_death_date = patients.date_of_death
dataset.ons_death_date = ons_deaths.date

# Censor date 

study_end_date = datetime.strptime(study_end_date, "%Y-%m-%d").date()

censor_date = minimum_of(dataset.TPP_death_date, 
                         dataset.ons_death_date, 
                         dataset.date_of_deregistration,
                         study_end_date
                         )

dataset.censor_date = censor_date

show(dataset)

## Migration status

dataset.has_a_migration_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .exists_for_patient())

## Date of first migration code

date_of_first_migration_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.date_of_first_migration_code = date_of_first_migration_code

migration_code_before_practice_reg = date_of_first_migration_code < date_of_first_practice_registration

processed_first_migration_code_date = case(
    when(migration_code_before_practice_reg == False).then(date_of_first_migration_code),
    when(migration_code_before_practice_reg == True).then(date_of_first_practice_registration)
)

dataset.processed_first_migration_code_date = processed_first_migration_code_date

show(dataset)

## Number of migration codes (maybe don't need)

dataset.number_of_migration_codes = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .count_for_patient()
)

# Sex

dataset.sex = patients.sex

# Year of birth

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


dataset.configure_dummy_data(population_size=1000)

