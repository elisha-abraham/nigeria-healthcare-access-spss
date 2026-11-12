* Encoding: UTF-8.
* =====================================================================
* 06_clinic_experience.sps : what happens at the public clinic?
*
* These questions were asked only of people who had contact with a public
* clinic or hospital in the past year, so they are missing for everyone
* else (script 01 declared "not applicable" as missing).
* Nobody is deleted from the file. Complex Samples keeps every
* respondent in the design and treats the clinic users as a
* subpopulation, which is what makes the standard errors right. The
* design degrees of freedom in the test tables stay at 188 for that
* reason. SELECT IF clinic_user = 1 before the analysis would throw away
* part of the design.
* =====================================================================.

GET FILE = 'data/nigeria_r10_analysis.sav'.
DATASET NAME survey.

* ---------------------------------------------------------------------
* 1. How hard was it, did it take a bribe, and what went wrong?
* ---------------------------------------------------------------------.
!table_start name = clinic_experience subtype = 'Oneway Table'.
CSTABULATE /PLAN FILE = 'data/design.csaplan'
  /TABLES VARIABLES = care_difficult paid_bribe no_medicine staff_absent long_wait poor_facility cost_problem
  /CELLS TABLEPCT
  /STATISTICS SE CIN(95) COUNT DEFF
  /MISSING SCOPE = TABLE CLASSMISSING = EXCLUDE.
!table_end name = clinic_experience.

* ---------------------------------------------------------------------
* 2. Among clinic users, do difficulty and bribes fall on the poor, on
*    rural people, or on everyone?
* ---------------------------------------------------------------------.
!table_start name = clinic_tests subtype = 'Tests of Independence'.
!table_start name = difficulty_by_group subtype = 'Twoway Table'.
!cs_by outcome = care_difficult groups = deprivation_level rural zone.
!table_end name = difficulty_by_group.
!table_start name = bribe_by_group subtype = 'Twoway Table'.
!cs_by outcome = paid_bribe groups = deprivation_level rural zone.
!table_end name = bribe_by_group.
!table_end name = clinic_tests.
