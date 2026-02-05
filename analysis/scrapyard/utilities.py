
# # Dictionary for analysis (ehrQL expressions)
# ehrql_subgroups = {
#     "": {},
#     "age": {"age_band": age_band},
#     "sex": {"sex": patients.sex},
#     "ethnicity": {"ethnicity": ethnicity},
#     "imd": {"imd_quintile": imd_quintile},
#     "region": {"region": region},
# }

# # Dictionary for plotting (column names as strings)
# plot_subgroups = {
#     "": [],
#     "age": ["age_band"],
#     "sex": ["sex"],
#     "ethnicity": ["ethnicity"],
#     "imd": ["imd_quintile"],
#     "region": ["region"]
# }

# function to load codelists 
from ehrql import codelist_from_csv

from ehrql import codelist_from_csv

def load_all_codelists():
    return {
        "all_migrant_codes": codelist_from_csv("codelists/user-YaminaB-migration-status.csv", column="code"),
        "cob_migrant_codes": codelist_from_csv("codelists/user-YaminaB-born-outside-the-uk.csv", column="code"),
        "asylum_refugee_migrant_codes": codelist_from_csv("codelists/user-YaminaB-asylum-seeker-or-refugee.csv", column="code"),
        "interpreter_migrant_codes": codelist_from_csv("codelists/user-YaminaB-interpreter-required.csv", column="code"),
        "ethnicity_codelist": codelist_from_csv(
            "codelists/opensafely-ethnicity-snomed-0removed.csv",
            column="code",
            category_column="Label_6",
        ),
    }
