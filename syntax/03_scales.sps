* Encoding: UTF-8.
* =====================================================================
* 03_scales.sps : is the deprivation index a sound measure?
*
* The index averages four questions on how often the household went
* without food, water, cooking fuel and a cash income. Before it is
* used as a predictor, three things are checked:
*   1. do the four items hang together (Cronbach's alpha, item-total
*      correlations);
*   2. do they measure one thing (principal components);
*   3. does the index vary across the country the way poverty is known
*      to (design-based means by zone and by urban or rural).
*
* Checks 1 and 2 describe the questionnaire items, not the population,
* so they are run on the respondents as interviewed, without weights.
* =====================================================================.

GET FILE = 'data/nigeria_r10_analysis.sav'.
DATASET NAME survey.

* ---------------------------------------------------------------------
* 1. Internal consistency: the four-item index, and the survey's own
*    five-item Lived Poverty Index for comparison.
* ---------------------------------------------------------------------.
!table_start name = scale_reliability subtype = 'Reliability Statistics'.
!table_start name = scale_items subtype = 'Item Total Statistics'.
RELIABILITY /VARIABLES = Q7A Q7B Q7D Q7E
  /SCALE('Deprivation index, four items') ALL /MODEL = ALPHA /SUMMARY = TOTAL.
RELIABILITY /VARIABLES = Q7A Q7B Q7C Q7D Q7E
  /SCALE('Lived Poverty Index, five items') ALL /MODEL = ALPHA /SUMMARY = TOTAL.
!table_end name = scale_items.
!table_end name = scale_reliability.

* ---------------------------------------------------------------------
* 2. One dimension or several: principal components of the four items.
*    One component with an eigenvalue above 1, and every item loading
*    on it, supports adding the items into a single index.
* ---------------------------------------------------------------------.
!table_start name = scale_kmo subtype = 'KMO and Bartlett Test'.
!table_start name = scale_components subtype = 'Total Variance Explained'.
!table_start name = scale_loadings subtype = 'Factor Matrix'.
FACTOR /VARIABLES Q7A Q7B Q7D Q7E /MISSING LISTWISE
  /PRINT INITIAL KMO EXTRACTION /CRITERIA MINEIGEN(1) /EXTRACTION PC /ROTATION NOROTATE.
!table_end name = scale_loadings.
!table_end name = scale_components.
!table_end name = scale_kmo.

* ---------------------------------------------------------------------
* 3. The index across the country: weighted means with design-based
*    standard errors. CSGLM with one factor gives the mean of each
*    group, and an adjusted Wald F test of whether the groups differ:
*    a one-way analysis of variance that respects the sample design.
* ---------------------------------------------------------------------.
!table_start name = deprivation_overall subtype = 'Univariate Statistics'.
CSDESCRIPTIVES /PLAN FILE = 'data/design.csaplan'
  /SUMMARY VARIABLES = deprivation lived_poverty /MEAN /STATISTICS SE CIN(95) COUNT DEFF
  /MISSING SCOPE = ANALYSIS CLASSMISSING = EXCLUDE.
!table_end name = deprivation_overall.

!table_start name = deprivation_by_group subtype = 'Estimates'.
!table_start name = deprivation_tests subtype = 'TestsOfModelEffects'.
CSGLM deprivation BY zone /PLAN FILE = 'data/design.csaplan'
  /MODEL zone /INTERCEPT INCLUDE = YES SHOW = YES
  /STATISTICS PARAMETER SE CINTERVAL /TEST TYPE = ADJF PADJUST = LSD
  /EMMEANS TABLES = zone /MISSING CLASSMISSING = EXCLUDE /CRITERIA CILEVEL = 95.
CSGLM deprivation BY rural /PLAN FILE = 'data/design.csaplan'
  /MODEL rural /INTERCEPT INCLUDE = YES SHOW = YES
  /STATISTICS PARAMETER SE CINTERVAL /TEST TYPE = ADJF PADJUST = LSD
  /EMMEANS TABLES = rural /MISSING CLASSMISSING = EXCLUDE /CRITERIA CILEVEL = 95.
!table_end name = deprivation_tests.
!table_end name = deprivation_by_group.
