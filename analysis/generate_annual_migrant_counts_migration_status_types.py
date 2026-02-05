from ehrql import create_measures, INTERVAL
import migration_status_variables
from analysis import utilities

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=False)  # enable on real data

# build shared variables and defaults
common = utilities.build_common_vars(INTERVAL)
measures.define_defaults(denominator=common["denominator"], intervals=common["intervals"])
subgroups = common["subgroups"]

# build base indicators 
numerators_separate = migration_status_variables.build_migrant_indicators(INTERVAL.end_date)

print("Available numerator keys:", sorted(numerators_separate.keys()))

# register one measure per numerator key × subgroup
var_name = "migration_status_types"

for key, expr in numerators_separate.items():
    # Defensive check: ensure expr is not a plain bool (must be an ehrql expression)
    if isinstance(expr, bool):
        raise TypeError(
            f"Numerator for key '{key}' is a plain boolean. "
            "Expected an ehrql expression (e.g. an exists_for_patient() expression)."
        )

    # Build a safe label for the measure name (lowercase, underscores, no spaces or hyphens)
    safe_label = key.lower().replace(" ", "_").replace("-", "_")

    for suffix, group in subgroups.items():
        if suffix == "":
            name = f"{var_name}__{safe_label}"
        else:
            name = f"{var_name}__{safe_label}__{suffix}"


        measures.define_measure(name=name, numerator=expr, group_by=group)