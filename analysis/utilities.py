# #############################################################################
# Utilities 
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

from ehrql import case, when, years
from ehrql.tables.tpp import addresses, practice_registrations, clinical_events, patients
import codelists

def build_common_vars(INTERVAL):
    # -------------------
    # Denominator pieces
    # -------------------
    was_alive_on_1Jan = patients.is_alive_on(INTERVAL.start_date)

    was_registered_on1Jan = (
        practice_registrations.for_patient_on(INTERVAL.start_date)
        .exists_for_patient()
    )

    has_recorded_sex = patients.sex.is_in(["male", "female"])

    has_possible_age = (
        (patients.age_on(INTERVAL.start_date) < 110)
        & (patients.age_on(INTERVAL.start_date) > 0)
    )

    denominator = (
        was_alive_on_1Jan
        & was_registered_on1Jan
        & has_recorded_sex
        & has_possible_age
    )

    # -------------------
    # Subgroup variables
    # -------------------
    age = patients.age_on(INTERVAL.start_date)
    age_band = case(
        when(age < 16).then("0-15"),
        when((age >= 16) & (age < 25)).then("16-24"),
        when((age >= 25) & (age < 35)).then("25-34"),
        when((age >= 35) & (age < 50)).then("35-49"),
        when((age >= 50) & (age < 65)).then("50-64"),
        when((age >= 65) & (age < 75)).then("65-74"),
        when((age >= 75) & (age < 85)).then("75-84"),
        when(age >= 85).then("85 plus"),
        otherwise="missing",
    )

    ethnicity = (
        clinical_events
        .where(clinical_events.snomedct_code.is_in(codelists.ethnicity_16_level_codelist))
        .where(clinical_events.date.is_on_or_before(INTERVAL.end_date))
        .sort_by(clinical_events.date)
        .last_for_patient()
        .snomedct_code.to_category(codelists.ethnicity_16_level_codelist)
        .when_null_then("unknown")
    )

    address = addresses.for_patient_on(INTERVAL.start_date)
    imd_quintile = address.imd_quintile

    region = (
        practice_registrations
        .for_patient_on(INTERVAL.start_date)
        .practice_nuts1_region_name
        .when_null_then("unknown")
    )

    subgroups = {
        "": {},
        "age": {"age_band": age_band},
        "sex": {"sex": patients.sex},
        "ethnicity": {"ethnicity": ethnicity},
        "imd": {"imd_quintile": imd_quintile},
        "region": {"region": region},
    }

    # -------------------
    # Intervals
    # -------------------
    intervals = years(16).starting_on("2009-01-01")

    return {
        "denominator": denominator,
        "intervals": intervals,
        "subgroups": subgroups,
        "age_band": age_band,
        "ethnicity": ethnicity,
        "imd_quintile": imd_quintile,
        "region": region,
    }

