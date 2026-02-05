# #############################################################################
# Cumulative number of migrants annually
# - Author: Yamina Boukari
# - Bennett Institute for Applied Data Science, University of Oxford, 2025
#############################################################################

from ehrql import INTERVAL, create_measures
from ehrql.tables.tpp import clinical_events
import migration_status_variables
import utilities   

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=False)  # set True on real data

# --------------------------
# Shared common variables and defaults (denominator, intervals, subgroups)
# --------------------------
common = utilities.build_common_vars(INTERVAL)

measures.define_defaults(
    denominator=common["denominator"],
    intervals=common["intervals"],
)

subgroups = common["subgroups"]

# --------------------------
# Build and register measures for separate migration boolean indicators only
# --------------------------

# Build separate boolean indicators (simple yes/no signals)
numerators_separate_mig_variables = migration_status_variables.build_migrant_indicators(
    INTERVAL.end_date
)

# Register measures: one measure per indicator × subgroup
for key, numerator in numerators_separate_mig_variables.items():
    for suffix, group in subgroups.items():
        measure_name = f"{key}" if suffix == "" else f"{key}_{suffix}"
        measures.define_measure(
            name=measure_name,
            numerator=numerator,
            group_by=group,
        )
