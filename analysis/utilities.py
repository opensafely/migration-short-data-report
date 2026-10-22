# #############################################################################
# Utilities 
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

from ehrql import case, when, years
from ehrql.tables.tpp import addresses, practice_registrations, clinical_events, patients, ons_deaths
import codelists

date_of_death = case(
    when(
        patients.date_of_death.is_not_null()
        & ons_deaths.date.is_not_null()
        & (patients.date_of_death <= ons_deaths.date)
    ).then(patients.date_of_death),

    when(
        patients.date_of_death.is_not_null()
        & ons_deaths.date.is_not_null()
        & (ons_deaths.date < patients.date_of_death)
    ).then(ons_deaths.date),

    when(patients.date_of_death.is_not_null()).then(
        patients.date_of_death
    ),

    when(ons_deaths.date.is_not_null()).then(
        ons_deaths.date
    ),
)

def build_common_vars(INTERVAL):

    eligible_registration = (
        practice_registrations.where(
            # Registration overlaps interval
            practice_registrations.start_date.is_on_or_before(INTERVAL.end_date)
            & (
                practice_registrations.end_date.is_on_or_after(INTERVAL.start_date)
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

            # Patient born by interval end
            & patients.date_of_birth.is_on_or_before(INTERVAL.end_date)

            # Patient not deceased before interval start
            & (
                date_of_death.is_on_or_after(INTERVAL.start_date)
                | date_of_death.is_null()
            )
    ))

    was_alive_and_registered_during_interval = (eligible_registration.exists_for_patient())

    has_recorded_sex = patients.sex.is_in(["male", "female"])

    has_possible_age = (
        (patients.age_on(INTERVAL.start_date) <= 110)
        & (patients.age_on(INTERVAL.end_date) >= 0)
    )

    denominator = (
        was_alive_and_registered_during_interval
        & has_recorded_sex
        & has_possible_age
    )

    # -------------------
    # Subgroup variables
    # -------------------
    age_reference_date = case(when(date_of_death.is_on_or_before(INTERVAL.end_date)
    ).then(date_of_death),
    otherwise=INTERVAL.end_date)

    age = patients.age_on(age_reference_date)

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
        .where(clinical_events.snomedct_code.is_in(codelists.ethnicity_6_level_codelist))
        .where(clinical_events.date.is_on_or_before(INTERVAL.end_date))
        .sort_by(clinical_events.date)
        .last_for_patient()
        .snomedct_code.to_category(codelists.ethnicity_6_level_codelist)
        .when_null_then("unknown")
    )

    eligible_addresses = addresses.where(
    # Address overlaps interval
    addresses.start_date.is_on_or_before(INTERVAL.end_date)
    & (
        addresses.end_date.is_on_or_after(INTERVAL.start_date)
        | addresses.end_date.is_null()
    )
    # Address overlaps patient's lifetime
    & (
        addresses.end_date.is_on_or_after(patients.date_of_birth)
        | addresses.end_date.is_null()
    )
    & (addresses.start_date.is_on_or_before(date_of_death)
        | date_of_death.is_null()
    )
    # Patient born by interval end
    & patients.date_of_birth.is_on_or_before(INTERVAL.end_date)
    # Patient not deceased before interval start
    & (date_of_death.is_on_or_after(INTERVAL.start_date)
        | date_of_death.is_null()
    ))

    imd_quintile = (
    eligible_addresses
    .sort_by(addresses.start_date)
    .last_for_patient()
    .imd_quintile)

    region = (
    eligible_registration
    .sort_by(practice_registrations.start_date)
    .last_for_patient()
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
    intervals = years(17).starting_on("2009-01-01")

    return {
        "denominator": denominator,
        "intervals": intervals,
        "subgroups": subgroups,
        "age_band": age_band,
        "ethnicity": ethnicity,
        "imd_quintile": imd_quintile,
        "region": region,
    }

