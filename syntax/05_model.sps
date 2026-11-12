* Encoding: UTF-8.
* =====================================================================
* 05_model.sps : what goes with going without care, other things equal?
*
* Two design-based logistic regressions of going without medical care
* several times or more.
*   Model 1: place and person (zone, rural, no clinic in the area,
*            education, age, sex, medical aid cover).
*   Model 2: Model 1 plus the deprivation index.
* Comparing the two shows how much of the gap between places is a gap
* in deprivation.
*
* Reading the output:
*   (LOW) after the outcome makes "No" the reference, so the model
*   describes the odds of going without care.
*   Factors (after BY) are compared with their last category: South West
*   for zone, post-secondary for education.
*   Covariates (after WITH) are coded 0/1 or are numeric, so Exp(B) is
*   the odds ratio for a one-unit step: rural against urban, one point
*   on the deprivation index, ten years of age.
* =====================================================================.

GET FILE = 'data/nigeria_r10_analysis.sav'.
DATASET NAME survey.

* ---------------------------------------------------------------------
* Model 1: place and person.
* ---------------------------------------------------------------------.
!table_start name = model1_estimates subtype = 'ParameterEstimates'.
!table_start name = model1_effects subtype = 'TestsOfModelEffects'.
!table_start name = model1_fit subtype = 'PseudoRSquares'.
CSLOGISTIC without_care (LOW) BY zone education WITH rural no_clinic age_decades female insured
  /PLAN FILE = 'data/design.csaplan'
  /MODEL zone education rural no_clinic age_decades female insured
  /INTERCEPT INCLUDE = YES SHOW = YES
  /STATISTICS PARAMETER EXP SE CINTERVAL TTEST DEFF
  /TEST TYPE = ADJF PADJUST = LSD
  /MISSING CLASSMISSING = EXCLUDE
  /CRITERIA MXITER = 100 MXSTEP = 5 PCONVERGE = [1e-006 RELATIVE] LCONVERGE = [0] CHKSEP = 20 CILEVEL = 95
  /PRINT SUMMARY VARIABLEINFO SAMPLEINFO.
!table_end name = model1_fit.
!table_end name = model1_effects.
!table_end name = model1_estimates.

* ---------------------------------------------------------------------
* Model 2: add the deprivation index.
* ---------------------------------------------------------------------.
!table_start name = model2_estimates subtype = 'ParameterEstimates'.
!table_start name = model2_effects subtype = 'TestsOfModelEffects'.
!table_start name = model2_fit subtype = 'PseudoRSquares'.
!table_start name = model2_sample subtype = 'SampleDesignInformation'.
CSLOGISTIC without_care (LOW) BY zone education WITH rural no_clinic age_decades female insured deprivation
  /PLAN FILE = 'data/design.csaplan'
  /MODEL zone education rural no_clinic age_decades female insured deprivation
  /INTERCEPT INCLUDE = YES SHOW = YES
  /STATISTICS PARAMETER EXP SE CINTERVAL TTEST DEFF
  /TEST TYPE = ADJF PADJUST = LSD
  /MISSING CLASSMISSING = EXCLUDE
  /CRITERIA MXITER = 100 MXSTEP = 5 PCONVERGE = [1e-006 RELATIVE] LCONVERGE = [0] CHKSEP = 20 CILEVEL = 95
  /PRINT SUMMARY VARIABLEINFO SAMPLEINFO.
!table_end name = model2_sample.
!table_end name = model2_fit.
!table_end name = model2_effects.
!table_end name = model2_estimates.
