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

dataset.configure_dummy_data(population_size=1000)

show(dataset)