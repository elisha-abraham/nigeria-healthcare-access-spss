* Encoding: UTF-8.
* =====================================================================
* macros.sps : small reusable tools
*
* !table_start, !table_end   save any output table as a CSV file
* !cs_by                     design-based percentage of a yes/no outcome
*                            within each level of one or more groupings
*
* The macros expect the working dataset to be named "survey" and paths
* to be relative to the project folder.
* =====================================================================.

* ---------------------------------------------------------------------
* !table_start name = <file name> subtype = '<OMS table subtype>'.
*    ... any procedures ...
* !table_end name = <file name>.
*
* Every table of the given subtype produced between the two calls is
* written to results/<file name>.csv. Results then live in plain files
* that can be compared, charted and checked, not only in a Viewer
* window. To find a table's subtype, right-click it in the Viewer and
* choose Copy OMS Table Subtype.
* ---------------------------------------------------------------------.
DEFINE !table_start (name = !TOKENS(1) / subtype = !TOKENS(1))
OMS /SELECT TABLES
    /IF SUBTYPES = [!subtype]
    /DESTINATION FORMAT = SAV OUTFILE = !QUOTE(!CONCAT('results/', !name, '.sav'))
    /TAG = !QUOTE(!name).
!ENDDEFINE.

DEFINE !table_end (name = !TOKENS(1))
OMSEND TAG = [!QUOTE(!name)].
GET FILE = !QUOTE(!CONCAT('results/', !name, '.sav')).
DATASET NAME table_out.
SAVE TRANSLATE OUTFILE = !QUOTE(!CONCAT('results/', !name, '.csv'))
    /TYPE = CSV /ENCODING = 'UTF8' /FIELDNAMES /CELLS = VALUES /REPLACE.
DATASET ACTIVATE survey.
DATASET CLOSE table_out.
!ENDDEFINE.

* ---------------------------------------------------------------------
* !cs_by outcome = <0/1 variable> groups = <one or more grouping variables>.
*
* For each grouping variable: the percentage with the outcome in every
* group, with a standard error, a 95% interval, the unweighted count and
* the design effect, plus a test of independence, all computed from the
* sampling design in data/design.csaplan.
* Respondents with a missing value on either variable stay in the design
* and are treated as outside the table, so the standard errors stay right.
* ---------------------------------------------------------------------.
DEFINE !cs_by (outcome = !TOKENS(1) / groups = !CMDEND)
!DO !group !IN (!groups)
CSTABULATE
  /PLAN FILE = 'data/design.csaplan'
  /TABLES VARIABLES = !group BY !outcome
  /CELLS ROWPCT
  /STATISTICS SE CIN(95) COUNT DEFF
  /TEST INDEPENDENCE
  /MISSING SCOPE = TABLE CLASSMISSING = EXCLUDE.
!DOEND
!ENDDEFINE.
