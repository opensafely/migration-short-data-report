## Script to load codelists
## that can be imported to all other relevant scripts
## Author: Yamina Boukari
####

from ehrql import codelist_from_csv

all_migrant_codes = codelist_from_csv("codelists/opensafely-migration-status.csv", column="code")

uk_cob_codes = codelist_from_csv("codelists/opensafely-born-in-the-uk.csv", column="code")

cob_migrant_codes = codelist_from_csv("codelists/opensafely-born-outside-the-uk.csv", column="code")

immigra_status_excl_ref_and_asylum_codes = codelist_from_csv("codelists/opensafely-immigration-status-excl-refugee-asylum.csv", column="code")

asylum_refugee_migrant_codes = codelist_from_csv("codelists/opensafely-asylum-or-refugee-status.csv", column="code")

english_not_main_language_excl_interpreter_migrant_codes = codelist_from_csv("codelists/opensafely-english-not-main-language.csv", column="code")

interpreter_migrant_codes = codelist_from_csv("codelists/opensafely-interpreter-required.csv", column="code")

ethnicity_16_level_codelist =  codelist_from_csv(
            "codelists/opensafely-ethnicity-snomed-0removed.csv",
            column="code",
            category_column="Label_16",
        )

ethnicity_6_level_codelist =  codelist_from_csv(
            "codelists/opensafely-ethnicity-snomed-0removed.csv",
            column="code",
            category_column="Label_6",
        )