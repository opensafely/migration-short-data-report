
from ehrql import create_measures, INTERVAL
from ehrql.tables.tpp import patients, practice_registrations, clinical_events, addresses
import migration_status_variables
from analysis import utilities 
import codelists

measures = create_measures()
measures.configure_dummy_data(population_size=1000)
measures.configure_disclosure_control(enabled=False)  # enable on real data

# build shared variables and defaults
common = utilities.build_common_vars(INTERVAL)
measures.define_defaults(denominator=common["denominator"], intervals=common["intervals"])
subgroups = common["subgroups"]

# build base indicators and aggregated 2-category expression
numerators_separate = migration_status_variables.build_migrant_indicators(INTERVAL.end_date)
mig2_expr = migration_status_variables.build_mig_status_2_cat(numerators_separate)

# register one measure per label × subgroup
labels = ["Migrant", "Non-migrant"]
for label in labels:
    bool_numer = (mig2_expr == label)
    safe_label = label.lower().replace(" ", "_").replace("-", "_")
    var_name = "mig_status_2_cat"
    for suffix, group in subgroups.items():
        if suffix == "":
            name = f"{var_name}__{safe_label}"
        else:
            name = f"{var_name}__{safe_label}__{suffix}"
        measures.define_measure(name=name, numerator=bool_numer, group_by=group)
