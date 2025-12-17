# #############################################################################
# Number of migrants in OpenSAFELY-TPP from 2009-2025
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

# This is a script to create the following migrant cohort with basic demographics:
# - Select anyone with 
#         1) a migration-related code at any time point from 2009-2025 AND 
#         2) who was registered at anytime (2009-2025) AND
#         3) who does not have a disclosive sex AND
#         4) had not died before 2009 AND 
#         4) has a plausible age (i.e. not >110 years old in 2009)

from pathlib import Path

from ehrql import create_dataset, codelist_from_csv, show, case, when
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths

from analysis.codelists import all_migrant_codes, cob_migrant_codes, asylum_refugee_migrant_codes, interpreter_migrant_codes, ethnicity_codelist

# Dates

study_start_date = "2009-01-01"
study_end_date = "2024-12-31"

# Select all individuals who:
#          1) had a migrant code during the entire study period AND 
#          2) were registered at some point during the period AND 
#          3) has a non-disclosive sex AND
#          4) had not died before the start of the study period 
#          5) was not over 100 years old at the beginning of the study period
# Add a variable indicating the date of the first code 
# Add a variable indicating how many migration-related codes they have

has_any_migrant_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .exists_for_patient())

is_registered_during_study = (
    practice_registrations
    .where((practice_registrations.end_date.is_null()) | ((practice_registrations.end_date.is_on_or_before(study_end_date)) & (practice_registrations.end_date.is_after(study_start_date))))
    .exists_for_patient()
)           

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

show(was_not_over_100_at_study_start)

dataset = create_dataset()
dataset.define_population(has_any_migrant_code & 
                          is_registered_during_study & 
                          has_non_disclosive_sex & 
                          is_alive_at_study_start & 
                          was_not_over_100_at_study_start)

show(dataset)

date_of_first_migration_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .sort_by(clinical_events.date)
    .first_for_patient().date)

dataset.date_of_first_migration_code = date_of_first_migration_code

dataset.number_of_migration_codes = (
    clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
    .count_for_patient()
)

dataset.sex = patients.sex

# Add variables to indicate the type of migration code

dataset.has_cob_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(cob_migrant_codes)).exists_for_patient()
dataset.has_asylum_or_refugee_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(asylum_refugee_migrant_codes)).exists_for_patient()
dataset.has_interpreter_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(interpreter_migrant_codes)).exists_for_patient()

# Add first practice registration date

date_of_first_practice_registration = (
    practice_registrations.sort_by(practice_registrations.start_date)
    .first_for_patient().start_date
)

dataset.date_of_first_practice_registration = date_of_first_practice_registration

# Calculate time from first registration to first migration code 

time_to_first_migration_code  = (date_of_first_migration_code - date_of_first_practice_registration).days

dataset.time_to_first_migration_code = time_to_first_migration_code

# Add ethnicity variable

dataset.latest_ethnicity_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .snomedct_code
)
dataset.latest_ethnicity_group = dataset.latest_ethnicity_code.to_category(
    ethnicity_codelist
)

# Add year of birth variable and categorise into bands 

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

# Add MSOA 

address = addresses.for_patient_on(study_start_date) 

dataset.msoa_code = address.msoa_code

# Add IMD based on patient's address 

dataset.imd_decile = address.imd_decile
dataset.imd_quintile = address.imd_quintile

# Add practice region (at study start)

dataset.region = practice_registrations.for_patient_on(study_start_date).practice_nuts1_region_name

# Add date of death (if died)

dataset.TPP_death_date = patients.date_of_death
dataset.ons_death_date = ons_deaths.date

show(dataset)

dataset.configure_dummy_data(population_size=1000)



