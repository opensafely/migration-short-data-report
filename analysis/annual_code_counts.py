# #############################################################################
# Annual migration coding 
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

# This is a script that uses measures to create an annual coding count of all migration-related codes 
# in order to compare with this OCC paper: https://bjgpopen.org/content/early/2026/02/20/BJGPO.2025.0138

from ehrql import create_measures, INTERVAL
from ehrql.tables.tpp import patients, practice_registrations, clinical_events, addresses
import migration_status_variables
from analysis import utilities 
import codelists

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=False)  # enable on real data

common = utilities.build_common_vars(INTERVAL)
measures.define_defaults(intervals=common["intervals"])
                        # group_by = common["subgroups"])

# denominator is not default because for this I want number of people with a migrant code
# in the given interval ONLY, whereas the default denominator is anyone registered and alive in 
# the interval

date_of_entry_code = ["860021000000109"]

migrant_codes_and_date_of_uk_entry = codelists.all_migrant_codes + date_of_entry_code

migration_codes_in_interval_excl_date_of_uk_entry = clinical_events.where(
    clinical_events.snomedct_code.is_in(codelists.all_migrant_codes)).where(
        clinical_events.date.is_during(INTERVAL))
# (because the BJGPO paper did not include date of UK entry code)

migration_codes_in_interval_incl_date_of_uk_entry = clinical_events.where(
    clinical_events.snomedct_code.is_in(migrant_codes_and_date_of_uk_entry)).where(
        clinical_events.date.is_during(INTERVAL))

measures.define_measure(
    name="all_migration_codes_excl_date_of_uk_entry", 
    numerator=migration_codes_in_interval_excl_date_of_uk_entry.count_for_patient(),
    denominator=migration_codes_in_interval_excl_date_of_uk_entry.exists_for_patient())

measures.define_measure(
    name="all_migration_codes_incl_date_of_uk_entry", 
    numerator=migration_codes_in_interval_incl_date_of_uk_entry.count_for_patient(),
    denominator=migration_codes_in_interval_incl_date_of_uk_entry.exists_for_patient())

