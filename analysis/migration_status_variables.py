
from ehrql import create_dataset, codelist_from_csv, show, case, when
from ehrql.tables.tpp import clinical_events
import codelists

migrant_flags = {
    "any_migrant": codelists.all_migrant_codes,
    "born_in_uk": codelists.uk_cob_codes,
    "not_born_in_uk": codelists.cob_migrant_codes,
    "immig_status_excl_refugee_asylum": codelists.immigra_status_excl_ref_and_asylum_codes,
    "refugee_asylum_status": codelists.asylum_refugee_migrant_codes,
    "english_not_main_language": codelists.english_not_main_language_excl_interpreter_migrant_codes,
    "interpreter_required": codelists.interpreter_migrant_codes,
}

def build_migrant_indicators(date):

    return {
        name: (
            clinical_events
            .where(clinical_events.snomedct_code.is_in(codes))
            .where(clinical_events.date.is_on_or_before(date))
            .exists_for_patient()
        )
        for name, codes in migrant_flags.items()
    }

def build_mig_status_2_cat(migrant_indicators):
    """
    2-category migrant status:
      - "Migrant" if migrant_indicators["any_migrant"] is True
      - "Non-migrant" otherwise
    """
    migrant = migrant_indicators.get("any_migrant", False)

    return case(
        when(migrant).then("Migrant"),
        otherwise="Non-migrant"
    )

def build_mig_status_3_cat(migrant_indicators, latest_ethnicity_expr):
    """
    3-category migrant status:
      - "Migrant" if migrant_indicators["migrant"]
      - "Non-migrant" if born_in_uk OR (ethnicity == "White - British" AND no migrant code)
      - "Unknown" otherwise
    """
    migrant = migrant_indicators.get("any_migrant", False)
    born_in_uk = migrant_indicators.get("born_in_uk", False)

    non_migrant_cond = born_in_uk | ((latest_ethnicity_expr == "White - British") & ~migrant)

    return case(
        when(migrant).then("Migrant"),
        when(non_migrant_cond).then("Non-migrant"),
        otherwise="Unknown"
    )

def build_mig_status_6_cat(migrant_indicators, latest_ethnicity_expr=None):
    """
    6-category migrant status (priority order):
      - Definite migrant: not_born_in_uk
      - Highly likely migrant: immig_status_excl_refugee_asylum OR refugee_asylum_status
      - Likely migrant: english_not_main_language OR interpreter_required
      - Definite non-migrant: born_in_uk 
      - Likely non-migrant: latest_ethnicity == "White - British"  (if latest_ethnicity_expr supplied) AND no migrant code 
      - Unknown: otherwise
    """
    migrant = migrant_indicators.get("any_migrant", False)
    not_born_in_uk = migrant_indicators.get("not_born_in_uk", False)
    immig_excl = migrant_indicators.get("immig_status_excl_refugee_asylum", False)
    refugee_asylum = migrant_indicators.get("refugee_asylum_status", False)
    english_not_main = migrant_indicators.get("english_not_main_language", False)
    interpreter_required = migrant_indicators.get("interpreter_required", False)
    born_in_uk = migrant_indicators.get("born_in_uk", False)

    # Compose combined conditions
    highly_likely = immig_excl | refugee_asylum
    likely_migrant = english_not_main | interpreter_required

    # Build the case expression in precedence order
    clauses = [
        (not_born_in_uk, "Definite migrant"),
        (highly_likely, "Highly likely migrant"),
        (likely_migrant, "Likely migrant"),
        (born_in_uk, "Definite non-migrant"),
    ]

    # Start assembling call to case(...) with only the non-empty conditions
    case_args = []
    for cond, label in clauses:
        case_args.append(when(cond).then(label))

    # ethnicity clause if provided
    if latest_ethnicity_expr is not None:
        case_args.append(when((latest_ethnicity_expr == "White - British") & (~migrant)).then("Likely non-migrant"))

    return case(
        *case_args,
        otherwise="Unknown"
    )

