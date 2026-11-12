* Encoding: UTF-8.
* =====================================================================
* 01_prepare_data.sps : from the published file to an analysis file
*
* 1. Declare the survey's missing-value codes, which the file leaves as
*    ordinary numbers.
* 2. Build the place, person and outcome variables used in the analysis.
* 3. Rebuild the sampling clusters, which the public file does not
*    identify, and check the result three ways.
* 4. Save a small analysis file.
*
* Paths are relative to the project folder (see 00_run_all.sps).
* =====================================================================.

GET FILE = 'data/raw/nigeria_r10_2024.sav'.
DATASET NAME survey.

* The published file arrives with weighting switched on. Everything in
* this script counts respondents, so weighting is switched off here.
* The weight is applied later, through the analysis plan, and nowhere else.
WEIGHT OFF.

* ---------------------------------------------------------------------
* 1. Missing values.
* In the published file "refused" (8), "don't know" (9) and "not
* applicable" (7) are stored as ordinary answers. Left alone, a mean of
* a 0-to-4 scale would count every "don't know" as a 9.
* Code 7 is declared only for the clinic questions, which were asked
* only of people who had contact with a public clinic or hospital.
* ---------------------------------------------------------------------.
MISSING VALUES Q7A TO Q7E Q41A Q42A Q42B (8, 9).
MISSING VALUES Q40B TO Q40H (7, 8, 9).
MISSING VALUES Q96 (98, 99).

* ---------------------------------------------------------------------
* 2a. Place.
* The 36 states and the FCT are grouped into the six geopolitical zones.
* ---------------------------------------------------------------------.
RECODE REGION (626, 634, 642, 643, 645, 646, 651 = 1)
              (621, 624, 627, 635, 654, 655 = 2)
              (637 THRU 641, 653, 656 = 3)
              (620, 623, 630, 633, 636 = 4)
              (622, 625, 628, 629, 631, 652 = 5)
              (632, 644, 647 THRU 650 = 6) INTO zone.
RECODE URBRUR (1 = 0) (2 = 1) INTO rural.
COMPUTE clinic_nearby = EA_FAC_D.
COMPUTE no_clinic = 1 - clinic_nearby.

* ---------------------------------------------------------------------
* 2b. Person.
* ---------------------------------------------------------------------.
RECODE Q101 (1 = 0) (2 = 1) INTO female.
RECODE Q1 (18 THRU 25 = 1) (26 THRU 35 = 2) (36 THRU 45 = 3) (46 THRU 55 = 4) (56 THRU 120 = 5) INTO age_group.
COMPUTE age_decades = Q1 / 10.
RECODE Q96 (0, 1 = 1) (2, 3 = 2) (4, 5 = 3) (6 THRU 9 = 4) INTO education.
RECODE Q41A (0 = 0) (1 = 1) INTO insured.

* ---------------------------------------------------------------------
* 2c. Going without, and the deprivation index.
* Question 7 asks how often in the past year "you or anyone in your
* family" went without five things. The answers therefore describe the
* respondent's household, not only the respondent.
* The outcome is going without medicines or medical treatment "several
* times", "many times" or "always".
* The deprivation index is the mean of four other things people went
* without (food, water, cooking fuel, cash income), each scored 0 never
* to 4 always. Medical care is left out of it on purpose: it is the
* outcome, and an index that contained it would predict itself.
* lived_poverty is the survey's standard five-item index, kept for
* comparison with published Afrobarometer figures.
* MEAN.4 and MEAN.5 give a value only when every item was answered.
* ---------------------------------------------------------------------.
RECODE Q7C (0, 1 = 0) (2 THRU 4 = 1) INTO without_care.
COMPUTE deprivation = MEAN.4(Q7A, Q7B, Q7D, Q7E).
COMPUTE lived_poverty = MEAN.5(Q7A, Q7B, Q7C, Q7D, Q7E).
RECODE deprivation (0 THRU 1 = 1) (1 THRU 2 = 2) (2 THRU 4 = 3) INTO deprivation_level.

* ---------------------------------------------------------------------
* 2d. Experience at public clinics and hospitals, and two opinions.
* The clinic questions were asked of people who had had contact with a
* public clinic or hospital in the past 12 months. The bribe question
* covers paying a bribe, giving a gift or doing a favour for health
* staff in order to get care.
* A problem counts when it was met "a few times" or "often".
* ---------------------------------------------------------------------.
COMPUTE clinic_user = Q40A.
RECODE Q40B (1, 2 = 0) (3, 4 = 1) INTO care_difficult.
RECODE Q40C (0 = 0) (1 THRU 3 = 1) INTO paid_bribe.
RECODE Q40D Q40E Q40F Q40G Q40H (0, 1 = 0) (2, 3 = 1)
  INTO no_medicine staff_absent long_wait poor_facility cost_problem.
RECODE Q42A (0 THRU 2 = 0) (3 = 1) INTO worry_cost.
RECODE Q42B (1 THRU 3 = 0) (4, 5 = 1) INTO care_for_all.

* ---------------------------------------------------------------------
* 3. Rebuild the sampling clusters.
* Afrobarometer interviews eight people in each enumeration area (EA),
* and people in the same EA resemble each other, so standard errors
* must be computed by cluster. The public file has no EA number.
* It does record, for every respondent, the state, urban or rural, the
* local government area, the EA-level weight and 22 things the field
* team observed about the EA (electricity grid, school, road surface and
* so on). Respondents who share all 26 values were interviewed in the
* same EA. AUTORECODE numbers each distinct combination.
* ---------------------------------------------------------------------.
STRING ea_key (A200).
COMPUTE ea_key = CONCAT(LOCATION.LEVEL.1, STRING(REGION, F4), STRING(URBRUR, F1), STRING(withinwt_ea, F14.10)).
DO REPEAT observed = EA_SVC_A TO EA_TM_NIG.
  COMPUTE ea_key = CONCAT(RTRIM(ea_key), STRING(observed, F3)).
END REPEAT.
AUTORECODE VARIABLES = ea_key /INTO psu.

* Strata: zone by urban or rural. The survey was stratified by state and
* urban or rural, but 22 of those 73 strata hold a single cluster, and a
* variance cannot be estimated from one cluster. Twelve broader strata
* hold 8 to 34 clusters each.
COMPUTE stratum = zone * 10 + rural.
EXECUTE.

VARIABLE LABELS
  zone 'Geopolitical zone'
  rural 'Rural enumeration area'
  clinic_nearby 'Health clinic in the enumeration area'
  no_clinic 'No health clinic in the enumeration area'
  female 'Woman'
  age_group 'Age group'
  age_decades 'Age in decades'
  education 'Education'
  insured 'Has medical aid cover'
  without_care 'Went without medicines or medical treatment several times or more in the past year'
  deprivation 'Deprivation index: food, water, cooking fuel, cash income (0 never to 4 always)'
  lived_poverty 'Lived Poverty Index, five items (0 to 4)'
  deprivation_level 'Deprivation level'
  clinic_user 'Had contact with a public clinic or hospital in the past year'
  care_difficult 'Found it difficult or very difficult to get the care needed'
  paid_bribe 'Paid a bribe, gave a gift or did a favour to get care, at least once'
  no_medicine 'Lack of medicines or supplies, a few times or often'
  staff_absent 'Absence of doctors or other staff, a few times or often'
  long_wait 'Long waiting time, a few times or often'
  poor_facility 'Poor condition of facilities, a few times or often'
  cost_problem 'High cost prevented care or medicines, a few times or often'
  worry_cost 'Worries a lot about being unable to get or afford medical care'
  care_for_all 'Agrees government should ensure health care for all, even if taxes rise'
  psu 'Enumeration area (rebuilt)'
  stratum 'Stratum: zone by urban or rural'.

VALUE LABELS zone 1 'North Central' 2 'North East' 3 'North West' 4 'South East' 5 'South South' 6 'South West'
  /rural 0 'Urban' 1 'Rural'
  /clinic_nearby 0 'No clinic in the area' 1 'Clinic in the area'
  /no_clinic 0 'Clinic in the area' 1 'No clinic in the area'
  /female 0 'Men' 1 'Women'
  /age_group 1 '18 to 25' 2 '26 to 35' 3 '36 to 45' 4 '46 to 55' 5 '56 and over'
  /education 1 'No formal schooling' 2 'Primary' 3 'Secondary' 4 'Post-secondary'
  /insured 0 'No cover' 1 'Has cover'
  /deprivation_level 1 'Low (0 to 1)' 2 'Moderate (above 1 to 2)' 3 'High (above 2)'
  /without_care clinic_user care_difficult paid_bribe no_medicine staff_absent long_wait poor_facility
   cost_problem worry_cost care_for_all 0 'No' 1 'Yes'.

FORMATS zone rural clinic_nearby no_clinic female age_group education insured without_care deprivation_level clinic_user
        care_difficult paid_bribe no_medicine staff_absent long_wait poor_facility cost_problem worry_cost
        care_for_all (F1.0) psu (F3.0) stratum (F2.0) deprivation lived_poverty (F4.2).

* ---------------------------------------------------------------------
* 3b. Check the rebuilt clusters against what the fieldwork rules imply.
*   - 200 clusters of exactly eight respondents;
*   - four interviewers per cluster, two interviews each;
*   - four men and four women per cluster (interviewers alternate).
* None of these facts was used to build the clusters.
* ---------------------------------------------------------------------.
COMPUTE man = 1 - female.
DATASET DECLARE cluster_check.
AGGREGATE /OUTFILE = 'cluster_check' /BREAK = psu Q108 /interviews = N /men = SUM(man).
DATASET ACTIVATE cluster_check.
AGGREGATE /OUTFILE = * /BREAK = psu /interviewers = N /respondents = SUM(interviews) /men = SUM(men).
VARIABLE LABELS respondents 'Respondents in the cluster' interviewers 'Interviewers who worked in the cluster'
  men 'Men in the cluster'.
!table_start name = check_clusters subtype = 'Frequencies'.
FREQUENCIES VARIABLES = respondents interviewers men.
!table_end name = check_clusters.
DATASET CLOSE cluster_check.

* ---------------------------------------------------------------------
* 4. Save the analysis file.
* ---------------------------------------------------------------------.
SAVE OUTFILE = 'data/nigeria_r10_analysis.sav'
  /KEEP = RESPNO psu stratum withinwt_hh zone rural clinic_nearby no_clinic female Q1 age_group age_decades
          education insured
          Q7A Q7B Q7C Q7D Q7E deprivation deprivation_level lived_poverty without_care
          clinic_user Q40B Q40C Q40D Q40E Q40F Q40G Q40H care_difficult paid_bribe
          no_medicine staff_absent long_wait poor_facility cost_problem
          Q42A Q42B worry_cost care_for_all.
