"""Recompute the SPSS results in Python, from the published data file, and compare.

    python -I scripts/cross_check.py

Nothing here reads anything SPSS built except the result tables it is checking.
The variables, the sampling clusters, the design-based standard errors and the
logistic regressions are all rebuilt from the raw file with numpy and pandas,
so agreement means two independent implementations reached the same numbers.

The standard errors use Taylor linearisation for a stratified cluster sample
drawn with replacement: add up each respondent's contribution within a
cluster, then measure how much the cluster totals vary inside each stratum.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "nigeria_r10_2024.sav"
RESULTS = ROOT / "results"

ZONES = {1: ("North Central", [626, 634, 642, 643, 645, 646, 651]), 2: ("North East", [621, 624, 627, 635, 654, 655]),
         3: ("North West", [637, 638, 639, 640, 641, 653, 656]), 4: ("South East", [620, 623, 630, 633, 636]),
         5: ("South South", [622, 625, 628, 629, 631, 652]), 6: ("South West", [632, 644, 647, 648, 649, 650])}
YES_NO = {0: "No", 1: "Yes"}
# label used in the SPSS tables -> (column here, {code: category label})
VARIABLES = {
    "Geopolitical zone": ("zone", {code: name for code, (name, _) in ZONES.items()}),
    "Rural enumeration area": ("rural", {0: "Urban", 1: "Rural"}),
    "Health clinic in the enumeration area": ("clinic_nearby", {0: "No clinic in the area", 1: "Clinic in the area"}),
    "Deprivation level": ("deprivation_level", {1: "Low (0 to 1)", 2: "Moderate (above 1 to 2)", 3: "High (above 2)"}),
    "Education": ("education", {1: "No formal schooling", 2: "Primary", 3: "Secondary", 4: "Post-secondary"}),
    "Age group": ("age_group", {1: "18 to 25", 2: "26 to 35", 3: "36 to 45", 4: "46 to 55", 5: "56 and over"}),
    "Woman": ("female", {0: "Men", 1: "Women"}),
    "Has medical aid cover": ("insured", {0: "No cover", 1: "Has cover"}),
    "Had contact with a public clinic or hospital in the past year": ("clinic_user", YES_NO),
    "Q7c. How often gone without medical care": ("Q7C", {0: "Never", 1: "Just once or twice", 2: "Several times",
                                                          3: "Many times", 4: "Always"}),
    "Went without medicines or medical treatment several times or more in the past year": ("without_care", YES_NO),
    "Worries a lot about being unable to get or afford medical care": ("worry_cost", YES_NO),
    "Agrees government should ensure health care for all, even if taxes rise": ("care_for_all", YES_NO),
    "Found it difficult or very difficult to get the care needed": ("care_difficult", YES_NO),
    "Paid a bribe, gave a gift or did a favour to get care, at least once": ("paid_bribe", YES_NO),
    "Lack of medicines or supplies, a few times or often": ("no_medicine", YES_NO),
    "Absence of doctors or other staff, a few times or often": ("staff_absent", YES_NO),
    "Long waiting time, a few times or often": ("long_wait", YES_NO),
    "Poor condition of facilities, a few times or often": ("poor_facility", YES_NO),
    "High cost prevented care or medicines, a few times or often": ("cost_problem", YES_NO),
}


class Checker:
    def __init__(self) -> None:
        self.compared = 0
        self.problems: list[str] = []

    def same(self, label: str, from_spss, recomputed, tolerance: float = 1e-6) -> None:
        self.compared += 1
        a, b = float(from_spss), float(recomputed)
        if not abs(a - b) <= tolerance * max(1.0, abs(a)):
            self.problems.append(f"{label}: SPSS {a!r}, Python {b!r}")


# ------------------------------------------------------------------ data

def build() -> pd.DataFrame:
    """The analysis variables, rebuilt from the published file."""
    raw, _ = pyreadstat.read_sav(str(RAW), apply_value_formats=False)

    def answers(column: str, valid: list[int]) -> pd.Series:
        """Keep real answers; refused, don't know and not applicable become missing."""
        return raw[column].where(raw[column].isin(valid))

    d = pd.DataFrame({"weight": raw["withinwt_hh"]})
    d["zone"] = raw["REGION"].map({state: code for code, (_, states) in ZONES.items() for state in states})
    d["rural"] = (raw["URBRUR"] == 2).astype(float)
    d["clinic_nearby"] = raw["EA_FAC_D"]
    d["no_clinic"] = 1 - d["clinic_nearby"]
    d["female"] = (raw["Q101"] == 2).astype(float)
    d["age_decades"] = raw["Q1"] / 10
    d["age_group"] = pd.cut(raw["Q1"], [17, 25, 35, 45, 55, 120], labels=False) + 1
    schooling = answers("Q96", list(range(10)))
    d["education"] = pd.cut(schooling, [-1, 1, 3, 5, 9], labels=False) + 1
    d["insured"] = answers("Q41A", [0, 1])
    for item in ("Q7A", "Q7B", "Q7C", "Q7D", "Q7E"):
        d[item] = answers(item, [0, 1, 2, 3, 4])
    d["without_care"] = (d["Q7C"] >= 2).astype(float).where(d["Q7C"].notna())
    d["deprivation"] = d[["Q7A", "Q7B", "Q7D", "Q7E"]].mean(axis=1, skipna=False)
    d["lived_poverty"] = d[["Q7A", "Q7B", "Q7C", "Q7D", "Q7E"]].mean(axis=1, skipna=False)
    d["deprivation_level"] = np.select([d["deprivation"] <= 1, d["deprivation"] <= 2, d["deprivation"] <= 4], [1, 2, 3], np.nan)
    d["clinic_user"] = raw["Q40A"]
    difficulty = answers("Q40B", [1, 2, 3, 4])
    d["care_difficult"] = (difficulty >= 3).astype(float).where(difficulty.notna())
    bribe = answers("Q40C", [0, 1, 2, 3])
    d["paid_bribe"] = (bribe >= 1).astype(float).where(bribe.notna())
    for source, name in (("Q40D", "no_medicine"), ("Q40E", "staff_absent"), ("Q40F", "long_wait"),
                         ("Q40G", "poor_facility"), ("Q40H", "cost_problem")):
        problem = answers(source, [0, 1, 2, 3])
        d[name] = (problem >= 2).astype(float).where(problem.notna())
    worry = answers("Q42A", [0, 1, 2, 3])
    d["worry_cost"] = (worry == 3).astype(float).where(worry.notna())
    opinion = answers("Q42B", [1, 2, 3, 4, 5])
    d["care_for_all"] = (opinion >= 4).astype(float).where(opinion.notna())

    # Sampling clusters: respondents who share state, urban/rural, local government area, the
    # enumeration-area weight and all 22 field observations of the area were interviewed in the same area.
    keys = ["REGION", "URBRUR", "LOCATION.LEVEL.1", "withinwt_ea"] + [c for c in raw.columns if c.startswith("EA_")]
    d["psu"] = raw.groupby(keys, dropna=False).ngroup()
    d["stratum"] = d["zone"] * 10 + d["rural"]
    d["interviewer"] = raw["Q108"]
    return d


# ------------------------------------------------------------------ design-based estimation

class Design:
    """Stratified cluster sample, clusters treated as drawn with replacement."""

    def __init__(self, data: pd.DataFrame) -> None:
        self.stratum = data["stratum"].to_numpy()
        self.psu = data["psu"].to_numpy()
        self.weight = data["weight"].to_numpy()
        clusters = data.groupby("stratum")["psu"].nunique()
        self.df = int(clusters.sum() - len(clusters))
        self.t = stats.t.ppf(0.975, self.df)

    def covariance(self, contributions: np.ndarray) -> np.ndarray:
        """Covariance of the column totals of `contributions` (one row per respondent, zeros where a
        respondent is outside the analysis: they still belong to their cluster)."""
        z = np.asarray(contributions, dtype=float).reshape(len(self.psu), -1)
        totals = pd.DataFrame(z).groupby([self.stratum, self.psu]).sum()
        cov = np.zeros((z.shape[1], z.shape[1]))
        for _, block in totals.groupby(level=0):
            n = len(block)
            deviations = block.to_numpy() - block.to_numpy().mean(axis=0)
            cov += n / (n - 1) * deviations.T @ deviations
        return cov

    def mean(self, y: pd.Series, domain: pd.Series | None = None, table: pd.Series | None = None) -> dict:
        """Weighted mean of y over the respondents in `domain` with a valid y.

        The design effect compares the design-based variance with the variance a simple random
        sample of the same respondents would give. `table` marks the respondents the table is
        built from (those with valid answers); when the estimate is for a group inside the table,
        a simple random sample would also be uncertain about how big that group is.
        """
        inside = y.notna().to_numpy() if domain is None else (y.notna() & domain).to_numpy()
        w = np.where(inside, self.weight, 0.0)
        values = np.where(inside, y.to_numpy(dtype=float), 0.0)
        total_weight = w.sum()
        estimate = (w * values).sum() / total_weight
        variance = self.covariance(w * (values - estimate) / total_weight)[0, 0]
        in_table = inside if table is None else table.to_numpy()
        srs_variance = (self.weight[in_table].sum() * (w * (values - estimate) ** 2).sum()
                        / ((in_table.sum() - 1) * total_weight ** 2))
        return {"estimate": estimate, "se": np.sqrt(variance), "n": int(inside.sum()),
                "deff": variance / srs_variance if srs_variance > 0 else np.nan}

    def percent(self, y: pd.Series, domain: pd.Series | None = None, table: pd.Series | None = None) -> dict:
        """A percentage with the logit-transformed confidence interval SPSS reports."""
        result = self.mean(y, domain, table)
        p, se = result["estimate"], result["se"]
        if 0 < p < 1:
            half = self.t * se / (p * (1 - p))
            logit = np.log(p / (1 - p))
            low, high = 1 / (1 + np.exp(-(logit - half))), 1 / (1 + np.exp(-(logit + half)))
        else:
            low = high = p
        return {"estimate": 100 * p, "se": 100 * se, "low": 100 * low, "high": 100 * high, "n": result["n"],
                "deff": result["deff"]}

    def logistic(self, y: pd.Series, X: pd.DataFrame) -> dict:
        """Weighted logistic regression; the covariance is the design-based sandwich."""
        complete = (y.notna() & X.notna().all(axis=1)).to_numpy()
        w = np.where(complete, self.weight, 0.0)
        design_matrix = np.where(complete[:, None], X.to_numpy(dtype=float), 0.0)
        outcome = np.where(complete, y.to_numpy(dtype=float), 0.0)
        beta = np.zeros(design_matrix.shape[1])
        for _ in range(100):
            p = 1 / (1 + np.exp(-design_matrix @ beta))
            information = (design_matrix * (w * p * (1 - p))[:, None]).T @ design_matrix
            step = np.linalg.solve(information, design_matrix.T @ (w * (outcome - p)))
            beta = beta + step
            if np.abs(step).max() < 1e-12:
                break
        p = 1 / (1 + np.exp(-design_matrix @ beta))
        information = (design_matrix * (w * p * (1 - p))[:, None]).T @ design_matrix
        bread = np.linalg.inv(information)
        cov = bread @ self.covariance(design_matrix * (w * (outcome - p))[:, None]) @ bread
        log_likelihood = (w * (outcome * np.log(p) + (1 - outcome) * np.log(1 - p))).sum()
        p0 = (w * outcome).sum() / w.sum()
        null_log_likelihood = (w * (outcome * np.log(p0) + (1 - outcome) * np.log(1 - p0))).sum()
        return {"names": list(X.columns), "beta": beta, "se": np.sqrt(np.diag(cov)), "n": int(complete.sum()),
                "population": w.sum(), "ll": log_likelihood, "ll0": null_log_likelihood}


# ------------------------------------------------------------------ reading SPSS tables

def table(name: str) -> pd.DataFrame:
    """One exported SPSS table, every cell as text. SPSS writes an empty cell as a single space."""
    frame = pd.read_csv(RESULTS / f"{name}.csv", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return frame.apply(lambda column: column.str.strip())


def number(text: str) -> float:
    return float(text) if text.strip() else np.nan


def check_oneway(check: Checker, design: Design, data: pd.DataFrame, name: str) -> None:
    for _, row in table(name).iterrows():
        column, categories = VARIABLES[row["Label_"]]
        if row["Var2"] == "Total":
            check.same(f"{name} {column} total count", row["UnweightedCount"], data[column].notna().sum())
            continue
        code = next(code for code, label in categories.items() if label == row["Var2"])
        mine = design.percent((data[column] == code).astype(float).where(data[column].notna()))
        label = f"{name} {column}={row['Var2']}"
        for key, spss_column in (("estimate", "Estimate"), ("se", "StandardError"), ("low", "Lower"), ("high", "Upper"),
                                 ("n", None), ("deff", "DesignEffect")):
            if key == "n":
                check.same(f"{label} count", row["UnweightedCount"], (data[column] == code).sum())
            else:
                check.same(f"{label} {key}", row[spss_column], mine[key])


def check_twoway(check: Checker, design: Design, data: pd.DataFrame, name: str) -> None:
    frame = table(name)
    for title, part in frame.groupby("Label_", sort=False):
        group_label, outcome_label = title.split(" * ")
        group, levels = VARIABLES[group_label]
        outcome = VARIABLES[outcome_label][0]
        both = data[group].notna() & data[outcome].notna()
        for level_label, rows in part.groupby("Var1", sort=False):
            if level_label == "Total":
                domain = both
            else:
                code = next(code for code, label in levels.items() if label == level_label)
                domain = both & (data[group] == code)
            cells = {(r["Var3"], r["Var4"]): r for _, r in rows.iterrows()}
            for answer, value in (("Yes", 1), ("No", 0)):
                mine = design.percent((data[outcome] == value).astype(float).where(data[outcome].notna()), domain, both)
                label = f"{name} {group}={level_label} {outcome}={answer}"
                check.same(f"{label} estimate", cells[("Estimate", "")][answer], mine["estimate"])
                check.same(f"{label} se", cells[("Standard Error", "")][answer], mine["se"])
                check.same(f"{label} low", cells[("95% Confidence Interval", "Lower")][answer], mine["low"])
                check.same(f"{label} high", cells[("95% Confidence Interval", "Upper")][answer], mine["high"])
                check.same(f"{label} count", cells[("Unweighted Count", "")][answer], (domain & (data[outcome] == value)).sum())
                if cells[("Design Effect", "")][answer].strip():
                    check.same(f"{label} deff", cells[("Design Effect", "")][answer], mine["deff"])


def check_model(check: Checker, design: Design, data: pd.DataFrame, name: str, covariates: list[str]) -> None:
    X = pd.DataFrame({"(Intercept)": 1.0}, index=data.index)
    for code in (1, 2, 3, 4, 5):
        X[f"[zone={code}]"] = (data["zone"] == code).astype(float)
    for code in (1, 2, 3):
        X[f"[education={code}]"] = (data["education"] == code).astype(float).where(data["education"].notna())
    for column in covariates:
        X[column] = data[column]
    fit = design.logistic(data["without_care"], X)
    mine = {parameter: (b, se) for parameter, b, se in zip(fit["names"], fit["beta"], fit["se"])}
    estimates = table(f"{name}_estimates")
    for _, row in estimates.iterrows():
        if not row["Std.Error"].strip():  # reference category
            continue
        b, se = mine.pop(row["Var2"])
        label = f"{name} {row['Var2']}"
        check.same(f"{label} B", row["B"], b)
        check.same(f"{label} SE", row["Std.Error"], se)
        check.same(f"{label} lower", row["Lower"], b - design.t * se)
        check.same(f"{label} upper", row["Upper"], b + design.t * se)
        check.same(f"{label} odds ratio", row["ExpB"], np.exp(b))
        check.same(f"{label} odds ratio lower", row["Lower_A"], np.exp(b - design.t * se))
        check.same(f"{label} odds ratio upper", row["Upper_A"], np.exp(b + design.t * se))
    check.same(f"{name}: every parameter matched", 0, len(mine))
    fit_table = {row["Var1"]: number(row["Var2"]) for _, row in table(f"{name}_fit").iterrows()}
    check.same(f"{name} McFadden R2", fit_table["McFadden"], 1 - fit["ll"] / fit["ll0"])
    cox_snell = 1 - np.exp(2 * (fit["ll0"] - fit["ll"]) / fit["population"])
    check.same(f"{name} Cox and Snell R2", fit_table["Cox and Snell"], cox_snell)
    check.same(f"{name} Nagelkerke R2", fit_table["Nagelkerke"], cox_snell / (1 - np.exp(2 * fit["ll0"] / fit["population"])))
    if name == "model2":
        sample = {(row["Var1"], row["Var2"]): number(row["N"]) for _, row in table("model2_sample").iterrows()}
        check.same("model2 valid cases", sample[("Unweighted Cases", "Valid")], fit["n"])
        check.same("model2 design degrees of freedom", sample[("Sampling Design Degrees of Freedom", "")], design.df)
        check.same("model2 strata", sample[("Stage 1", "Strata")], len(np.unique(design.stratum)))
        check.same("model2 clusters", sample[("Stage 1", "Units")], len(np.unique(design.psu)))


def check_scales(check: Checker, data: pd.DataFrame) -> None:
    reliability = table("scale_reliability")
    items = table("scale_items")
    position = 0
    for (_, row), columns in zip(reliability.iterrows(), (["Q7A", "Q7B", "Q7D", "Q7E"], ["Q7A", "Q7B", "Q7C", "Q7D", "Q7E"])):
        answers = data[columns].dropna()

        def alpha(frame: pd.DataFrame) -> float:
            k = frame.shape[1]
            return k / (k - 1) * (1 - frame.var(ddof=1).sum() / frame.sum(axis=1).var(ddof=1))

        check.same(f"alpha, {len(columns)} items", row["CronbachsAlpha"], alpha(answers))
        for column in columns:
            others = answers.drop(columns=column)
            item_row = items.iloc[position]
            position += 1
            check.same(f"{len(columns)} items, {column}: item-total correlation",
                       item_row["CorrectedItemTotalCorrelation"], answers[column].corr(others.sum(axis=1)))
            check.same(f"{len(columns)} items, {column}: alpha if deleted", item_row["CronbachsAlphaifItemDeleted"], alpha(others))
    correlations = data[["Q7A", "Q7B", "Q7D", "Q7E"]].dropna().corr().to_numpy()
    eigenvalues, vectors = np.linalg.eigh(correlations)
    order = np.argsort(eigenvalues)[::-1]
    for (_, row), value in zip(table("scale_components").iterrows(), eigenvalues[order]):
        check.same(f"principal component {row['Var1']} eigenvalue", row["InitialEigenvalues_Total"], value)
    loadings = np.abs(vectors[:, order[0]] * np.sqrt(eigenvalues[order[0]]))
    for (_, row), value in zip(table("scale_loadings").iterrows(), loadings):
        check.same(f"loading of {row['Var1'][:4]}", abs(float(row["@1"])), value)
    inverse = np.linalg.inv(correlations)
    partial = -inverse / np.sqrt(np.outer(np.diag(inverse), np.diag(inverse)))
    off = ~np.eye(4, dtype=bool)
    kmo = (correlations[off] ** 2).sum() / ((correlations[off] ** 2).sum() + (partial[off] ** 2).sum())
    check.same("KMO", table("scale_kmo").iloc[0]["Var3"], kmo)


def main() -> None:
    check = Checker()
    data = build()
    design = Design(data)

    # the rebuilt clusters and the strata
    per_cluster = data.groupby("psu").agg(respondents=("weight", "size"), interviewers=("interviewer", "nunique"),
                                          men=("female", lambda s: int((s == 0).sum())))
    names = {"Respondents in the cluster": "respondents", "Interviewers who worked in the cluster": "interviewers",
             "Men in the cluster": "men"}
    for _, row in table("check_clusters").iterrows():
        if row["Var2"] != "Total":
            check.same(f"clusters with {row['Var2']} {names[row['Label_']]}", row["Frequency"],
                       (per_cluster[names[row["Label_"]]] == float(row["Var2"])).sum())
    for _, row in table("check_strata").iterrows():
        members = data[data["stratum"] == float(row["stratum"])]
        check.same(f"stratum {row['stratum']} clusters", row["clusters"], members["psu"].nunique())
        check.same(f"stratum {row['stratum']} respondents", row["respondents"], len(members))

    check_scales(check, data)

    for _, row in table("deprivation_overall").iterrows():
        column = "deprivation" if row["Var2"].startswith("Deprivation") else "lived_poverty"
        mine = design.mean(data[column])
        check.same(f"mean {column}", row["Estimate"], mine["estimate"])
        check.same(f"mean {column} se", row["StandardError"], mine["se"])
        check.same(f"mean {column} lower", row["Lower"], mine["estimate"] - design.t * mine["se"])
        check.same(f"mean {column} upper", row["Upper"], mine["estimate"] + design.t * mine["se"])
        check.same(f"mean {column} deff", row["DesignEffect"], mine["deff"])
        check.same(f"mean {column} count", row["UnweightedCount"], mine["n"])
    group_of = {label: (column, code) for column, levels in (VARIABLES["Geopolitical zone"], VARIABLES["Rural enumeration area"])
                for code, label in levels.items()}
    for _, row in table("deprivation_by_group").iterrows():
        column, code = group_of[row["Var1"]]
        mine = design.mean(data["deprivation"], data[column] == code)
        check.same(f"mean deprivation {row['Var1']}", row["Mean"], mine["estimate"])
        check.same(f"mean deprivation {row['Var1']} se", row["Std.Error"], mine["se"])
        check.same(f"mean deprivation {row['Var1']} lower", row["Lower"], mine["estimate"] - design.t * mine["se"])
        check.same(f"mean deprivation {row['Var1']} upper", row["Upper"], mine["estimate"] + design.t * mine["se"])

    check_oneway(check, design, data, "headline")
    check_twoway(check, design, data, "without_care_by_group")
    base = ["rural", "no_clinic", "age_decades", "female", "insured"]
    check_model(check, design, data, "model1", base)
    check_model(check, design, data, "model2", base + ["deprivation"])
    check_oneway(check, design, data, "clinic_experience")
    check_twoway(check, design, data, "difficulty_by_group")
    check_twoway(check, design, data, "bribe_by_group")

    print(f"{check.compared} figures compared, {len(check.problems)} differences")
    for problem in check.problems[:40]:
        print("  " + problem)
    sys.exit(1 if check.problems else 0)


if __name__ == "__main__":
    main()
