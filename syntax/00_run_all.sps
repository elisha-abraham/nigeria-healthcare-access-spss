* Encoding: UTF-8.
* =====================================================================
* Going without medical care in Nigeria
* Afrobarometer Round 10, Nigeria (fieldwork June to July 2024)
*
* 00_run_all.sps : runs the whole analysis, in order
*
* Author : Elisha Abraham
* Needs  : IBM SPSS Statistics 27 or later with the Complex Samples
*          module, and the data file in data/raw (see data/README.md)
*
* Two ways to run it.
*   From the SPSS window: run the next command once with the path to
*   this project on your computer, then run this file.
*       CD 'C:\path\to\nigeria-healthcare-access-spss'.
*   Without opening SPSS: see scripts/run_spss.py.
*
* Every script reads and writes with paths relative to the project
* folder, so nothing else needs editing. Key tables are saved as CSV
* files in results/.
* =====================================================================.

INSERT FILE = 'syntax/macros.sps' ERROR = STOP.
INSERT FILE = 'syntax/01_prepare_data.sps' ERROR = STOP.
INSERT FILE = 'syntax/02_survey_design.sps' ERROR = STOP.
INSERT FILE = 'syntax/03_scales.sps' ERROR = STOP.
INSERT FILE = 'syntax/04_prevalence.sps' ERROR = STOP.
INSERT FILE = 'syntax/05_model.sps' ERROR = STOP.
INSERT FILE = 'syntax/06_clinic_experience.sps' ERROR = STOP.
