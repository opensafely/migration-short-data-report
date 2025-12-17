# This is a script to create the following migrant cohort with basic demographics:
# - Select anyone with 
#         1) who was registered with a TPP practice on the Census date AND
#         2) was alive on the census date
#         3) who does not have a disclosive sex AND 
#         4) has a plausible age (i.e. not >110 years old at the date of the census)

from ehrql import create_dataset, show, case, when
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events
import codelists
import migration_status_variables
from argparse import ArgumentParser

# Below code from https://github.com/opensafely/disease_incidence/blob/main/analysis/dataset_definition_demographics.py
# Arguments (from project.yaml)

parser = ArgumentParser()
parser.add_argument("--census-date", type=str)
args = parser.parse_args()

#######
# census_date = args.census_date
census_date = "2021-03-21"

# define population

was_registered_on_census_date = (
    practice_registrations.exists_for_patient_on(census_date)
)           

has_non_disclosive_sex = (
    (patients.sex == "male") | (patients.sex == "female")
)

was_alive_on_census_date = (
    (patients.is_alive_on(census_date))
)

has_possible_age= ((patients.age_on(census_date) < 110) & (patients.age_on(census_date) > 0))

dataset = create_dataset()
dataset.define_population(was_registered_on_census_date & 
                          has_non_disclosive_sex &
                          has_possible_age & 
                          was_alive_on_census_date)

# add variables 

# age

age_on_census_date = patients.age_on(census_date)
dataset.age_band = case(
        when(age_on_census_date < 16).then("0-15"),
        when((age_on_census_date >= 16) & (age_on_census_date < 25)).then("16-24"),
        when((age_on_census_date >= 25) & (age_on_census_date < 35)).then("25-34"),
        when((age_on_census_date >= 35) & (age_on_census_date < 50)).then("35-49"),
        when((age_on_census_date >= 50) & (age_on_census_date < 65)).then("50-64"),
        when((age_on_census_date >= 65) & (age_on_census_date < 75)).then("65-74"),
        when((age_on_census_date >= 75) & (age_on_census_date < 85)).then("75-84"),
        when(age_on_census_date >= 85).then("85 plus"),
        otherwise="missing",
)

# sex 

dataset.sex = patients.sex

# Practice region

dataset.region = practice_registrations.for_patient_on(census_date).practice_nuts1_region_name

# IMD

address = addresses.for_patient_on(census_date) 

dataset.imd_decile = address.imd_decile
dataset.imd_quintile = address.imd_quintile

# ethnicity 

latest_ethnicity_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(codelists.ethnicity_16_level_codelist))
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


# migration status 

migrant_indicators = migration_status_variables.build_migrant_indicators(census_date)

for name, indicator in migrant_indicators.items():
    setattr(dataset, name, indicator)

# consolidate migration indiciators into 2-cat, 3-cat and 6-cat variables

dataset.mig_status_2_cat = migration_status_variables.build_mig_status_2_cat(migrant_indicators)

dataset.mig_status_3_cat = migration_status_variables.build_mig_status_3_cat(
    migrant_indicators,
    dataset.latest_ethnicity_16_level_group
)

dataset.mig_status_6_cat = migration_status_variables.build_mig_status_6_cat(
    migrant_indicators,
    dataset.latest_ethnicity_16_level_group
)

# # migration status - 2 categories (migrant, non-migrant)

# dataset.mig_status_2_cat = case(
#     when(migrant_indicators["migrant"] == True).then("Migrant"),
#     otherwise="Non-migrant"
# )

# # migrant status - 3 catogories (migrant, non-migrant, unknown)

# dataset.mig_status_3_cat = case(
#     when(migrant_indicators["migrant"] == True).then("Migrant"),
#     when((migrant_indicators["born_in_uk"] == True) | (latest_ethnicity_16_level_group == "White - British")).then("Non-migrant"),
#     otherwise="Unknown"
# )

# # migrant status - 6 categories (definite migrant, highly likely migrant, likely migrant, definite non-migrant, likely non-migrant, unknown)

# dataset.mig_status_6_cat = case(
#     when(migrant_indicators["not_born_in_uk"] == True).then("Definite migrant"), 
#     when((migrant_indicators["immig_status_excl_refugee_asylum"] == True) | (migrant_indicators["refugee_asylum_status"] == True)).then("Highly likely migrant"),
#     when((migrant_indicators["english_not_main_language"] == True) | (migrant_indicators["interpreter_required"] == True)).then("Likely migrant"),
#     when(migrant_indicators["born_in_uk"] == True).then("Definite non-migrant"),
#     when(latest_ethnicity_16_level_group == "White - British").then("Likely non-migrant"),
#     otherwise="Unknown"
# )


# migrant = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)).exists_for_patient()
# dataset.migrant = migrant

# born_in_uk = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.uk_cob_codes)).exists_for_patient()
# dataset.born_in_uk = born_in_uk

# not_born_in_uk = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.cob_migrant_codes)).exists_for_patient()
# dataset.not_born_in_uk = not_born_in_uk

# immig_status_excl_refugee_asylum = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.immigra_status_excl_ref_and_asylum_codes)).exists_for_patient()
# dataset.immig_status_excl_refugee_asylum = immig_status_excl_refugee_asylum

# refugee_asylum_status = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.asylum_refugee_migrant_codes)).exists_for_patient()
# dataset.refugee_asylum_status = refugee_asylum_status

# english_not_main_language = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.english_not_main_language_excl_interpreter_migrant_codes)).exists_for_patient()
# dataset.english_not_main_language = english_not_main_language 

# interpreter_required = clinical_events.where(clinical_events.snomedct_code.is_in(codelists.interpreter_migrant_codes)).exists_for_patient()
# dataset.interpreter_required = interpreter_required


# date_of_first_migration_code = (
#     clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
#     .sort_by(clinical_events.date)
#     .first_for_patient().date)

# dataset.date_of_first_migration_code = date_of_first_migration_code

# dataset.number_of_migration_codes = (
#     clinical_events.where(clinical_events.snomedct_code.is_in(all_migrant_codes))
#     .count_for_patient()
# )



# # Add variables to indicate the type of migration code


# dataset.has_cob_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(cob_migrant_codes)).exists_for_patient()
# dataset.has_asylum_or_refugee_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(asylum_refugee_migrant_codes)).exists_for_patient()
# dataset.has_interpreter_migrant_code = clinical_events.where(clinical_events.snomedct_code.is_in(interpreter_migrant_codes)).exists_for_patient()

# # Add first practice registration date

# date_of_first_practice_registration = (
#     practice_registrations.sort_by(practice_registrations.start_date)
#     .first_for_patient().start_date
# )

# dataset.date_of_first_practice_registration = date_of_first_practice_registration

# # Calculate time from first registration to first migration code 

# time_to_first_migration_code  = (date_of_first_migration_code - date_of_first_practice_registration).days

# dataset.time_to_first_migration_code = time_to_first_migration_code

# # Add ethnicity variable



# # Add year of birth variable and categorise into bands 

# year_of_birth = (patients.date_of_birth).year
# dataset.year_of_birth = year_of_birth

# dataset.year_of_birth_band = case(
#     when((year_of_birth >= 1900) & (year_of_birth <= 1925)).then("1900-1925"),
#     when((year_of_birth > 1925) & (year_of_birth <= 1945)).then("1926-1945"),
#     when((year_of_birth > 1945) & (year_of_birth <= 1965)).then("1946-1965"),
#     when((year_of_birth > 1965) & (year_of_birth <= 1985)).then("1966-1985"),
#     when((year_of_birth > 1985) & (year_of_birth <= 2005)).then("1986-2005"),
#     when((year_of_birth > 2005) & (year_of_birth <= 2025)).then("2006-2025") 
# )

# # age 

# age_on_census_date = patients.age_on(census_date)
# dataset.age_on_census_date  = age_on_census_date

# dataset.age_band = case(
#         when(age_on_census_date < 16).then("0-15"),
#         when((age_on_census_date >= 16) & (age_on_census_date < 25)).then("16-24"),
#         when((age_on_census_date >= 25) & (age_on_census_date < 35)).then("25-34"),
#         when((age_on_census_date >= 35) & (age_on_census_date < 50)).then("35-49"),
#         when((age_on_census_date >= 50) & (age_on_census_date < 65)).then("50-64"),
#         when((age_on_census_date >= 65) & (age_on_census_date < 75)).then("65-74"),
#         when((age_on_census_date >= 75) & (age_on_census_date < 85)).then("75-84"),
#         when(age_on_census_date >= 85).then("85 plus"),
#         otherwise="missing",
# )

# # Add MSOA 

# address = addresses.for_patient_on(census_date) 

# dataset.msoa_code = address.msoa_code

# # Add IMD based on patient's address 

# dataset.imd_decile = address.imd_decile
# dataset.imd_quintile = address.imd_quintile

# # Add practice region (at study start)

# dataset.region = practice_registrations.for_patient_on(census_date).practice_nuts1_region_name



dataset.configure_dummy_data(population_size=1000)

show(dataset)