###################################################
# This script creates descriptive demographic tables for the overall full cohort 
#
# Author: Yamina Boukari
#   Bennett Institute for Applied Data Science
#   University of Oxford, 2026
#
###################################################

library(tidyverse)
library(lubridate)
library(here)
library(arrow)
library(skimr)
library(fs)
library(dtplyr)
library(data.table)

## Create output directory
output_dir <- here::here("output", "tables")
fs::dir_create(output_dir)

cohort_file <- "output/cohorts/full_study_cohort.arrow"
output_file <- "output/tables/demographics_full_study_cohort.csv"

# Parse command-line argument
#args <- commandArgs(trailingOnly=TRUE)
#print(commandArgs(trailingOnly=TRUE))

#output_file <- args[[1]]
#mig_vars <- args[[2]]

# Import data ----
cohort <- read_feather(cohort_file) %>%
  mutate(
    across(
      where(is.ordered),
      ~ factor(as.character(.x))
    )
  )

# Summarize ----- 

vars_to_summarise <- c(
  "year_of_birth_band",
  "sex",
  "region",
  "latest_ethnicity_6_level_group",
  "imd_quintile"
)

mig_vars <- c(
  "mig_status_2_cat",
  "mig_status_3_cat",
  "mig_status_6_cat")

rounding <- function(vars) {
  case_when(vars == 0 ~ 0,
            vars > 7 ~ round(vars / 5) * 5)
}

cohort <- setDT(cohort)

dt <- melt(cohort, 
            measure.vars = vars_to_summarise, 
            variable.name = "subgroup", 
            value.name = "category",
            variable.factor = FALSE)

dt <- melt(dt, 
           measure.vars = mig_vars, 
           variable.name = "migration_scheme", 
           value.name = "migration_status",
           variable.factor = FALSE)

dt[is.na(category),category:= "unknown"]
dt[is.na(migration_status),migration_status:= "unknown"]

dt_counts <- dt[,.(n = .N),
                  by = .(migration_scheme, migration_status, subgroup, category)]

dt_counts[ , n_rounded := rounding(n)]
dt_counts[ , percentage := round(100 * n_rounded / sum(n_rounded), 1),
           by = .(migration_scheme, migration_status, subgroup)]


table_freq <- cohort %>%
  lazy_dt() %>%
  pivot_longer(
    cols = all_of(vars_to_summarise),
    names_to = "subgroup",
    values_to = "category"
  ) %>%
  pivot_longer(
    cols = all_of(mig_vars),
    names_to = "migration_scheme",
    values_to = "migration_status"
  ) %>%
  # make missing explicit if needed
  mutate(
    category = fct_na_value_to_level(category, "unknown"),
    migration_status = fct_na_value_to_level(migration_status, "unknown")
  ) %>%
  count(
    migration_scheme,
    migration_status,
    subgroup,
    category,
    name = "n"
  ) %>%
  group_by(migration_scheme, migration_status, subgroup) %>%
  mutate(
    n = rounding(n),
    percentage = round((100 * n / sum(n)),1)
  ) %>%
  ungroup() %>%
  as_tibble()

dir_create(path_dir(output_file))
write_csv(dt_counts, path = output_file)


