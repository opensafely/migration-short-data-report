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

claim_permissions("appointments")

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=True)

# common denominator conditions

was_alive_on_1Jan = patients.is_alive_on(INTERVAL.start_date)

was_registered_at_any_point_during_interval = practice_registrations.where(
        # registered for the entire interval
        ((practice_registrations.start_date.is_on_or_before(INTERVAL.start_date)) 
        & (practice_registrations.end_date.is_on_or_after(INTERVAL.end_date))) |
        
        # registered during the interval and end date is after the interval end date
        ((practice_registrations.start_date.is_after(INTERVAL.start_date))
         & (practice_registrations.end_date.is_on_or_after(INTERVAL.end_date))) |
         
         # registered before the interval and registration is ongoing
         ((practice_registrations.start_date.is_on_or_before(INTERVAL.start_date)) &
          (practice_registrations.end_date.is_null())) |
          
          # registered after interval start date and registration is ongoing
          ((practice_registrations.start_date.is_after(INTERVAL.start_date)) &
           (practice_registrations.end_date.is_null())) |
           
           # registered before the interval start date and end date is before the end date, but after the start date 
           ((practice_registrations.start_date.is_before(INTERVAL.start_date)) &
           (practice_registrations.end_date.is_between_but_not_on(INTERVAL.start_date, INTERVAL.end_date))) |
           
           # registered for part of the interval only
           ((practice_registrations.start_date.is_between_but_not_on(INTERVAL.start_date, INTERVAL.end_date)) &
            (practice_registrations.end_date.is_between_but_not_on(INTERVAL.start_date, INTERVAL.end_date)))
    ).exists_for_patient()

has_recorded_sex = patients.sex.is_in(["male", "female"])

has_possible_age = (
        (patients.age_on(INTERVAL.start_date) < 110)
        & (patients.age_on(INTERVAL.start_date) > 0)
    )

# migrant  = clinical_events.where(
#         clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)).where(
#                 clinical_events.date.is_on_or_between(patients.date_of_birth, INTERVAL.end_date)).where(
#                         (clinical_events.date.is_on_or_before(patients.date_of_death)) | (patients.date_of_death.is_null())).exists_for_patient()

denominators_separate = migration_status_variables.build_migrant_indicators(INTERVAL.end_date)
mig3_expr = migration_status_variables.build_mig_status_3_cat_withdoe(denominators_separate)

migrant_denominator = (mig3_expr == "Migrant")

migrant_denominator = (
        was_alive_on_1Jan
        & was_registered_at_any_point_during_interval
        & has_recorded_sex
        & has_possible_age
        & migrant_denominator 
    )

# any planned primary care contacts during the interval 
# code reference: https://github.com/opensafely/winter-pressures-phase-II/blob/main/analysis/appointments/app_measures.py (Accessed 18/06/26)
planned_and_actual_encounters = appointments.where(
    appointments.start_date.is_during(INTERVAL) | 
    appointments.seen_date.is_during(INTERVAL)).exists_for_patient() 

planned_encounters_only = appointments.where(
    appointments.start_date.is_during(INTERVAL)).exists_for_patient()

labels = ["Migrant", "Non-migrant", "Unknown"]
for label in labels:
    migrant_denom = was_alive_on_1Jan & was_registered_at_any_point_during_interval & has_recorded_sex & has_possible_age & (mig3_expr == label)
    safe_label = label.lower().replace("-", "_")
    name = f"planned_and_actual_primary_care_activity_{safe_label}"
    measures.define_measure(
        name=name, 
        numerator=planned_and_actual_encounters,
        denominator=migrant_denom,
        intervals = years(17).starting_on("2009-01-01") 
        )

for label in labels:
    migrant_denom = was_alive_on_1Jan & was_registered_at_any_point_during_interval & has_recorded_sex & has_possible_age & (mig3_expr == label)
    safe_label = label.lower().replace("-", "_")
    name = f"planned_primary_care_activity_{safe_label}"
    measures.define_measure(
        name=name, 
        numerator=planned_encounters_only,
        denominator=migrant_denom,
        intervals = years(17).starting_on("2009-01-01") 
        )