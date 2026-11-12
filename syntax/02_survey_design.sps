* Encoding: UTF-8.
* =====================================================================
* 02_survey_design.sps : tell SPSS how the sample was drawn
*
* The sample is not a simple random sample. It was stratified, drawn in
* clusters of eight, and weighted. An analysis plan records those three
* facts once, and every Complex Samples procedure reads it. Estimates
* are then weighted, and standard errors allow for the clustering.
*
* ESTIMATOR TYPE = WR treats clusters as drawn with replacement, the
* usual assumption when the sampling fraction is tiny (200 enumeration
* areas out of many thousands).
*
* SRSESTIMATOR TYPE = WR sets the yardstick for the design effect: a
* simple random sample, also drawn with replacement. It matters here
* because the weights add up to the sample size (1,600), not to the
* population. With TYPE = WOR, SPSS would read them as a population of
* 1,600 people, all of whom were interviewed, and report design effects
* in the thousands.
* =====================================================================.

GET FILE = 'data/nigeria_r10_analysis.sav'.
DATASET NAME survey.

CSPLAN ANALYSIS
  /PLAN FILE = 'data/design.csaplan'
  /PLANVARS ANALYSISWEIGHT = withinwt_hh
  /SRSESTIMATOR TYPE = WR
  /PRINT PLAN
  /DESIGN STRATA = stratum CLUSTER = psu
  /ESTIMATOR TYPE = WR.

* Count the clusters and respondents in each stratum.
DATASET DECLARE strata_check.
AGGREGATE /OUTFILE = 'strata_check' /BREAK = stratum psu /respondents = N.
DATASET ACTIVATE strata_check.
AGGREGATE /OUTFILE = * /BREAK = stratum /clusters = N /respondents = SUM(respondents).
VARIABLE LABELS clusters 'Clusters in the stratum' respondents 'Respondents in the stratum'.
FORMATS clusters respondents (F4.0).
LIST.
SAVE TRANSLATE OUTFILE = 'results/check_strata.csv' /TYPE = CSV /ENCODING = 'UTF8' /FIELDNAMES /CELLS = VALUES /REPLACE.
DATASET ACTIVATE survey.
DATASET CLOSE strata_check.
