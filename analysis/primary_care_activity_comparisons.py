# #############################################################################
# Primary care activity by migration status 
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2026
#############################################################################

from ehrql.tables.core import patients
from ehrql import (
    years,
    INTERVAL,
    create_measures,
    claim_permissions
)

from ehrql.tables.tpp import (
    practice_registrations,
    appointments
)
import migration_status_variables

from utilities import date_of_death

claim_permissions("appointments")

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=True)

# common denominator conditions

was_alive_and_registered_during_interval = (
    practice_registrations.where(
        # Registration overlaps interval
        practice_registrations.start_date.is_on_or_before(INTERVAL.end_date)
        & (
            practice_registrations.end_date.is_on_or_after(INTERVAL.start_date)
            | practice_registrations.end_date.is_null()
        )

        # Registration overlaps patient's lifetime
        & (
            practice_registrations.end_date.is_on_or_after(patients.date_of_birth)
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
    ).exists_for_patient()
)

has_recorded_sex = patients.sex.is_in(["male", "female"])

has_possible_age = (
    (patients.age_on(INTERVAL.start_date) <= 110)
    & (patients.age_on(INTERVAL.end_date) >= 0)
)

denominators_separate = migration_status_variables.build_migrant_indicators(INTERVAL.end_date, date_of_death)
mig3_expr = migration_status_variables.build_mig_status_3_cat_withdoe(denominators_separate)

# any planned primary care contacts during the interval 
# code reference: https://github.com/opensafely/winter-pressures-phase-II/blob/main/analysis/appointments/app_measures.py (Accessed 18/06/26)
planned_and_actual_encounters = appointments.where(
    appointments.start_date.is_during(INTERVAL) | 
    appointments.seen_date.is_during(INTERVAL)).count_for_patient() 

planned_encounters_only = appointments.where(
    appointments.start_date.is_during(INTERVAL)).count_for_patient()

labels = ["Migrant", "Non-migrant", "Unknown"]
for label in labels:
    migrant_denom = was_alive_and_registered_during_interval & has_recorded_sex & has_possible_age & (mig3_expr == label)
    safe_label = label.lower().replace("-", "_")
    name = f"planned_and_actual_primary_care_activity_{safe_label}"
    measures.define_measure(
        name=name, 
        numerator=planned_and_actual_encounters,
        denominator=migrant_denom,
        intervals = years(17).starting_on("2009-01-01") 
        )

for label in labels:
    migrant_denom = was_alive_and_registered_during_interval & has_recorded_sex & has_possible_age & (mig3_expr == label)
    safe_label = label.lower().replace("-", "_")
    name = f"planned_primary_care_activity_{safe_label}"
    measures.define_measure(
        name=name, 
        numerator=planned_encounters_only,
        denominator=migrant_denom,
        intervals = years(17).starting_on("2009-01-01") 
        )