# This is a script to create an overall population cohort 
# for the purposes of then creating denominators split up by subgroups
# in order to calculate migrants as a percentage of the EHR population
#
# It selects all individuals who:
#          1) were registered at some point during the period AND 
#          2) has a non-disclosive sex AND
#          3) had not died before the start of the study period 
#          4) was not over 100 years old at the beginning of the study period


from ehrql import create_dataset, codelist_from_csv, show, case, when
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
from utilities import load_all_codelists 

# load codelist
ethnicity_codelist = codelist_from_csv(
    "codelists/opensafely-ethnicity-snomed-0removed.csv",
    column="code",
    category_column="Label_6",
)

# dates
study_start_date = "2009-01-01"
study_end_date = "2024-12-31"

# inclusion criteria
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

dataset = create_dataset()
dataset.define_population(is_registered_during_study & 
                          has_non_disclosive_sex & 
                          is_alive_at_study_start & 
                          was_not_over_100_at_study_start)

# add stratifying variables
dataset.sex = patients.sex

dataset.latest_ethnicity_code = (
    clinical_events.where(clinical_events.snomedct_code.is_in(ethnicity_codelist))
    .sort_by(clinical_events.date)
    .last_for_patient()
    .snomedct_code
)

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

address = addresses.for_patient_on(study_start_date) 

dataset.msoa_code = address.msoa_code

dataset.imd_decile = address.imd_decile
dataset.imd_quintile = address.imd_quintile

dataset.region = practice_registrations.for_patient_on(study_start_date).practice_nuts1_region_name

dataset.TPP_death_date = patients.date_of_death
dataset.ons_death_date = ons_deaths.date

dataset.configure_dummy_data(population_size=1000)