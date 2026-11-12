# Data notes

## Source

Afrobarometer Data, Nigeria, Round 10, 2024, available at http://www.afrobarometer.org.

The file comes from the survey's own page, https://www.afrobarometer.org/survey-resource/nigeria-round-10-data-2024/, where it is published as `NIG_R10.Data_18Nov24.wtd_.final_.release_updated.13Feb25.sav`. Afrobarometer data are free to use and protected by copyright, so the file is not stored in this repository.

## Getting the data

```bash
python scripts/01_download_data.py
```

The script saves the file as `data/raw/nigeria_r10_2024.sav` (1.68 MB) and writes its size and SHA-256 to `data/raw/manifest.json`. When this project was built the SHA-256 began `876545eeb59ace51`.

## The file as published

| | |
|---|---|
| Respondents | 1,600 adults aged 18 to 92 |
| Variables | 382 |
| Interviews | 19 June to 17 July 2024, face to face |
| Places | 36 states and the FCT; 67 local government areas; 200 enumeration areas, eight respondents in each |
| Weight | `withinwt_hh`, scaled to add up to 1,600 |

Three things about the file shape the analysis:

- "Refused" (8), "don't know" (9) and "not applicable" (7) are stored as ordinary values, not declared as missing.
- The file opens with weighting switched on.
- There is no variable that numbers the enumeration areas.

## Questions used

Wording is shortened here; the full wording is in Afrobarometer's questionnaire for the round.

| Variable | Question | Answers |
|---|---|---|
| `Q7A` to `Q7E` | Over the past year, how often, if ever, have you or anyone in your family gone without: enough food to eat; enough clean water for home use; medicines or medical treatment; enough fuel to cook your food; a cash income? | 0 never, 1 just once or twice, 2 several times, 3 many times, 4 always |
| `Q40A` | Contact with a public clinic or hospital in the past 12 months | 0 no, 1 yes |
| `Q40B` | How easy or difficult it was to obtain the care needed | 1 very easy to 4 very difficult; 7 no contact |
| `Q40C` | How often had to pay a bribe, give a gift or do a favour for health staff to get care | 0 never to 3 often; 7 no contact |
| `Q40D` to `Q40H` | Problems met at a public clinic or hospital: lack of medicines or other supplies; absence of doctors or other medical personnel; long waiting time; poor condition of facilities; high cost that prevented getting care or medicines | 0 never to 3 often; 7 no contact |
| `Q41A` | Has medical aid coverage that helps pay medical bills | 0 no, 1 yes |
| `Q42A` | How much the respondent worries about being unable to obtain or afford needed medical care | 0 not at all to 3 a lot |
| `Q42B` | Government should ensure all citizens have access to adequate healthcare, even if that means raising taxes | 1 strongly disagree to 5 strongly agree |
| `Q1`, `Q101`, `Q96` | Age, gender, education | |
| `REGION`, `URBRUR`, `LOCATION.LEVEL.1` | State, urban or rural, local government area | |
| `EA_SVC_A` to `EA_TM_NIG` | 22 things the field team recorded about the enumeration area: services, facilities (including a health clinic, `EA_FAC_D`), security presence, roads | |
| `withinwt_ea`, `Q108` | Enumeration-area weight; interviewer number | |

## Variables built by `syntax/01_prepare_data.sps`

| Variable | Meaning |
|---|---|
| `zone` | Geopolitical zone, from the state: North Central, North East, North West, South East, South South, South West |
| `rural` | 1 rural, 0 urban |
| `clinic_nearby`, `no_clinic` | Whether the field team recorded a health clinic in the enumeration area, coded both ways |
| `female` | 1 woman, 0 man |
| `age_group`, `age_decades` | Five age bands; age divided by ten |
| `education` | No formal schooling (including informal schooling only), primary, secondary, post-secondary |
| `insured` | Has medical aid cover |
| `without_care` | 1 if the respondent or their family went without medicines or medical treatment several times, many times or always in the past year |
| `deprivation` | Mean of `Q7A`, `Q7B`, `Q7D` and `Q7E` (food, water, cooking fuel, cash income), 0 to 4. Missing unless all four were answered |
| `deprivation_level` | Low (0 to 1), moderate (above 1 to 2), high (above 2) |
| `lived_poverty` | Mean of all five `Q7` items: Afrobarometer's Lived Poverty Index |
| `clinic_user` | Had contact with a public clinic or hospital in the past year |
| `care_difficult` | Found it difficult or very difficult to get the care needed (clinic users) |
| `paid_bribe` | Paid a bribe, gave a gift or did a favour at least once (clinic users) |
| `no_medicine`, `staff_absent`, `long_wait`, `poor_facility`, `cost_problem` | Met the problem a few times or often (clinic users) |
| `worry_cost` | Worries a lot about being unable to get or afford care |
| `care_for_all` | Agrees or strongly agrees that government should ensure health care for all, even if taxes rise |
| `psu` | Enumeration area, rebuilt (1 to 200) |
| `stratum` | Zone by urban or rural (12 strata) |

## Sample design used in the analysis

| | |
|---|---|
| Strata | 12: geopolitical zone by urban or rural |
| Clusters | 200 rebuilt enumeration areas, 8 to 34 per stratum |
| Weight | `withinwt_hh` |
| Variance | Taylor linearisation, clusters treated as drawn with replacement |
| Design degrees of freedom | 188 (200 clusters minus 12 strata) |

## Result tables in `results/`

| File | Holds |
|---|---|
| `check_clusters.csv`, `check_strata.csv` | The checks on the rebuilt clusters, and clusters per stratum |
| `scale_reliability.csv`, `scale_items.csv` | Cronbach's alpha and item-total statistics |
| `scale_kmo.csv`, `scale_components.csv`, `scale_loadings.csv` | Principal components of the deprivation items |
| `deprivation_overall.csv`, `deprivation_by_group.csv`, `deprivation_tests.csv` | Design-based means of the index, and tests of differences |
| `headline.csv` | National percentages |
| `without_care_by_group.csv`, `without_care_tests.csv` | Going without care by place and person, with Rao-Scott tests |
| `model1_*.csv`, `model2_*.csv` | Logistic regression estimates, tests of effects and fit |
| `clinic_experience.csv`, `difficulty_by_group.csv`, `bribe_by_group.csv`, `clinic_tests.csv` | Experience of public clinic users |

The tables are written by SPSS's Output Management System, so they keep SPSS's layout: one row per table row, with the row labels in the `Var` columns. An empty cell holds a single space.
