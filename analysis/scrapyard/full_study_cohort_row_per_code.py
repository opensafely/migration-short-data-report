from ehrql import create_dataset, codelist_from_csv, show, case, when
from ehrql.tables.tpp import addresses, patients, practice_registrations, clinical_events, ons_deaths
from utilities import load_all_codelists 

# load codelists 
(all_migrant_codes,
    cob_migrant_codes,
    asylum_refugee_migrant_codes,
    interpreter_migrant_codes,
    ethnicity_codelist
) = load_all_codelists().values()

# Dates

study_start_date = "2009-01-01"
study_end_date = "2024-12-31"

# general inclusion criteria

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

dataset = create_dataset()
dataset.define_population(has_any_migrant_code & 
                          is_registered_during_study & 
                          has_non_disclosive_sex & 
                          is_alive_at_study_start & 
                          was_not_over_100_at_study_start)

show(dataset)