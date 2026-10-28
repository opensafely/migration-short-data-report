# #############################################################################
# Number of migrants in OpenSAFELY-TPP from 2009-2025
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

# This is a script to explore the migration status of all individuals who:
#         1) was alive and registered (at the same time) within the study period (2009-2025) AND
#         2) do not have a disclosive sex AND
#         4) had a plausible age at the beginning of the study period  (i.e. not >110 years old in 2009)

from pathlib import Path

from ehrql import create_dataset, codelist_from_csv, show, case, when, days
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
import codelists
import migration_status_variables
from utilities import date_of_death

# Dates

study_start_date = "2009-01-01"
study_end_date = "2025-12-31" 

was_alive_and_registered_during_study = (
    practice_registrations.where(
        # Registration overlaps study period
        practice_registrations.start_date.is_on_or_before(study_end_date)
        & (
            practice_registrations.end_date.is_on_or_after(study_start_date)
            | practice_registrations.end_date.is_null()
        )

        # Registration overlaps patient's lifetime
        & (
            practice_registrations.end_date.is_on_or_after(
                patients.date_of_birth
            )
            | practice_registrations.end_date.is_null()
        )
        & (
            practice_registrations.start_date.is_on_or_before(date_of_death)
            | date_of_death.is_null()
        )

        # Patient born by study end
        & patients.date_of_birth.is_on_or_before(study_end_date)

        # Patient not deceased before study start
        & (
            date_of_death.is_on_or_after(study_start_date)
            | date_of_death.is_null()
        )
    ).exists_for_patient()
)


has_non_disclosive_sex = (
    (patients.sex == "male") | (patients.sex == "female")
)

was_not_over_110_at_study_start_or_less_than_0_at_end_date = (
    (patients.age_on(study_start_date) <= 110) & (patients.age_on(study_end_date) >= 0)
)

dataset = create_dataset()
dataset.define_population(was_alive_and_registered_during_study &
                          has_non_disclosive_sex & 
                          was_not_over_110_at_study_start_or_less_than_0_at_end_date)

# add variables 

## year of birth and date of birth
year_of_birth = (patients.date_of_birth).year
dataset.year_of_birth = year_of_birth

dataset.year_of_birth_band = case(
    when((year_of_birth >= 1898) & (year_of_birth <= 1925)).then("1898-1925"),
    when((year_of_birth > 1925) & (year_of_birth <= 1945)).then("1926-1945"),
    when((year_of_birth > 1945) & (year_of_birth <= 1965)).then("1946-1965"),
    when((year_of_birth > 1965) & (year_of_birth <= 1985)).then("1966-1985"),
    when((year_of_birth > 1985) & (year_of_birth <= 2005)).then("1986-2005"),
    when((year_of_birth > 2005) & (year_of_birth <= 2025)).then("2006-2025") 
)

dataset.date_of_birth = patients.date_of_birth

## sex

dataset.sex = patients.sex

## ethnicity

latest_ethnicity_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(codelists.ethnicity_16_level_codelist))
    .where(clinical_events.date.is_on_or_before(study_end_date)) 
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

dataset.region = (
    practice_registrations
    .where(
        practice_registrations.start_date.is_on_or_before(study_end_date)
        & (
            practice_registrations.end_date.is_on_or_after(study_start_date)
            | practice_registrations.end_date.is_null()
        )
    )
    .sort_by(practice_registrations.start_date)
    .last_for_patient()
    .practice_nuts1_region_name
)

## imd

address = (
    addresses
    .where(
        addresses.start_date.is_on_or_before(study_end_date)
        & (
            addresses.end_date.is_on_or_after(study_start_date)
            | addresses.end_date.is_null()
        )
    )
    .sort_by(addresses.start_date)
    .last_for_patient()
)

dataset.imd_decile = address.imd_decile
dataset.imd_quintile = address.imd_quintile

## date of first practice registration

date_of_first_practice_registration = (
    practice_registrations
    .sort_by(practice_registrations.start_date)
    .first_for_patient()
    .start_date
)

dataset.date_of_first_practice_registration = date_of_first_practice_registration

dataset.date_of_death = date_of_death

# migration status 

migrant_indicators = migration_status_variables.build_migrant_indicators(study_end_date, date_of_death)

for name, indicator in migrant_indicators.items():
    setattr(dataset, name, indicator)

dataset.mig_status_3_cat_withdoe = migration_status_variables.build_mig_status_3_cat_withdoe(
    migrant_indicators)

# first migration code with no date restrictions 

date_of_first_migration_code_no_restrictions = (
    clinical_events
            .where((clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)) | (clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))) 
            .sort_by(clinical_events.date)
            .first_for_patient().date

)

dataset.date_of_first_migration_code_no_restrictions = date_of_first_migration_code_no_restrictions

has_first_migration_code_no_restrictions = (
    clinical_events
                .where((clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)) | (clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))) 
                .sort_by(clinical_events.date)
                .exists_for_patient()
)

dataset.has_first_migration_code_no_restrictions = has_first_migration_code_no_restrictions

# number of migration codes per person

number_of_migration_codes = (
    clinical_events
            .where(clinical_events.snomedct_code.is_in(codelists.all_migrant_codes))
            .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
            .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
            .count_for_patient()
)
dataset.number_of_migration_codes = number_of_migration_codes

number_of_migration_codes_withdoe = (
    clinical_events
            .where((clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)) | (clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))) 
            .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
            .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
            .count_for_patient()
)
dataset.number_of_migration_codes_withdoe = number_of_migration_codes_withdoe

# date of entry to the UK (SNOMED CT code: 860021000000109)

## has date of entry to the UK code 

has_date_of_uk_entry = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .exists_for_patient()
)
dataset.has_date_of_uk_entry = has_date_of_uk_entry

## number of uses of date of entry to the UK code 

dataset.number_of_date_of_uk_entry_codes = (
    clinical_events
    .where(clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .count_for_patient()
)

## date associated with earliest date of entry to the UK code (that was recorded post-birth )

date_of_earliest_date_of_uk_entry_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)
dataset.date_of_earliest_date_of_uk_entry_code = date_of_earliest_date_of_uk_entry_code

## temporality of earliest date of entry to the UK code in relation to first practice registration date

dataset.temporality_of_date_of_uk_entry_code = case(
    when((date_of_earliest_date_of_uk_entry_code.is_null())).then("No date of entry code"), 
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
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.date_of_first_migration_code = date_of_first_migration_code

date_of_first_migration_code_withdoe = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)) | (clinical_events.snomedct_code.is_in(codelists.date_of_uk_entry))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.date_of_first_migration_code_withdoe = date_of_first_migration_code_withdoe

time_from_1st_pracreg_first_migration_code_days_withdoe  = (date_of_first_migration_code_withdoe - date_of_first_practice_registration).days
time_from_1st_pracreg_first_migration_code_months_withdoe  = (date_of_first_migration_code_withdoe - date_of_first_practice_registration).months

dataset.time_from_1st_pracreg_first_migration_code_days_withdoe = time_from_1st_pracreg_first_migration_code_days_withdoe
dataset.time_from_1st_pracreg_first_migration_code_months_withdoe  = time_from_1st_pracreg_first_migration_code_months_withdoe 

# time from birth to first migration code 

time_from_birth_first_migration_code_days_withdoe  = (date_of_first_migration_code_withdoe - patients.date_of_birth).days
time_from_birth_first_migration_code_months_withdoe  = (date_of_first_migration_code_withdoe - patients.date_of_birth).months

dataset.time_from_birth_first_migration_code_days_withdoe = time_from_birth_first_migration_code_days_withdoe
dataset.time_from_birth_first_migration_code_months_withdoe  = time_from_birth_first_migration_code_months_withdoe 

# time from first practice registration to first specific migration code 

## country of birth 

date_of_first_cob_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.cob_migrant_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_cob_code_days  = (date_of_first_cob_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_cob_code_months  = (date_of_first_cob_code - date_of_first_practice_registration).months

## immigration status 

date_of_first_immig_status_excl_refugee_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.immigra_status_excl_ref_and_asylum_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_immig_status_excl_refugee_code_days  = (date_of_first_immig_status_excl_refugee_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_immig_status_excl_refugee_code_months = (date_of_first_immig_status_excl_refugee_code - date_of_first_practice_registration).months

## asylum and refugee codes

date_of_first_refugee_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.asylum_refugee_migrant_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_refugee_code_days  = (date_of_first_refugee_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_refugee_code_months = (date_of_first_refugee_code - date_of_first_practice_registration).months

## English not first/main language

date_of_first_language_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.english_not_main_language_excl_interpreter_migrant_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_language_code_days  = (date_of_first_language_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_language_code_months = (date_of_first_language_code - date_of_first_practice_registration).months

## Interpreter

date_of_first_interpreter_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.interpreter_migrant_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_interpreter_code_days  = (date_of_first_interpreter_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_interpreter_code_months = (date_of_first_interpreter_code - date_of_first_practice_registration).months

## trafficking

date_of_first_trafficking_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.trafficking_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_trafficking_code_days  = (date_of_first_trafficking_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_trafficking_code_months = (date_of_first_trafficking_code - date_of_first_practice_registration).months

## uk cob

date_of_first_uk_cob_code = (
    clinical_events.where((clinical_events.snomedct_code.is_in(codelists.uk_cob_codes))) 
    .where(clinical_events.date.is_on_or_between(patients.date_of_birth, study_end_date))
    .where((clinical_events.date.is_on_or_before(date_of_death)) | (date_of_death.is_null()))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.time_from_1st_pracreg_first_uk_cob_code_days  = (date_of_first_uk_cob_code - date_of_first_practice_registration).days
dataset.time_from_1st_pracreg_first_uk_cob_code_months  = (date_of_first_uk_cob_code - date_of_first_practice_registration).months

dataset.configure_dummy_data(population_size=1000)
show(dataset)


