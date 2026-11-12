* Encoding: UTF-8.
* =====================================================================
* 04_prevalence.sps : how many people go without medical care, and who?
*
* Every figure is a weighted percentage with a design-based standard
* error and 95% confidence interval. The design effect shows how much
* the clustering widens the interval compared with a simple random
* sample of the same size.
* =====================================================================.

GET FILE = 'data/nigeria_r10_analysis.sav'.
DATASET NAME survey.

* ---------------------------------------------------------------------
* 1. Headline figures for all adults.
*    Q7C is the full five-point answer behind the yes/no outcome.
* ---------------------------------------------------------------------.
!table_start name = headline subtype = 'Oneway Table'.
CSTABULATE /PLAN FILE = 'data/design.csaplan'
  /TABLES VARIABLES = without_care Q7C worry_cost care_for_all insured clinic_user clinic_nearby
  /CELLS TABLEPCT
  /STATISTICS SE CIN(95) COUNT DEFF
  /MISSING SCOPE = TABLE CLASSMISSING = EXCLUDE.
!table_end name = headline.

* ---------------------------------------------------------------------
* 2. Going without care, by place and person.
*    The test of independence is the Rao-Scott adjusted chi-square,
*    the survey version of the Pearson test.
* ---------------------------------------------------------------------.
!table_start name = without_care_by_group subtype = 'Twoway Table'.
!table_start name = without_care_tests subtype = 'Tests of Independence'.
!cs_by outcome = without_care
  groups = zone rural clinic_nearby deprivation_level education age_group female insured clinic_user.
!table_end name = without_care_tests.
!table_end name = without_care_by_group.
