"""Data quality of the value and winner columns before and after cleaning.

Runs the same checks on the raw data and on the cleaned data (cleaning plus the
disguised missing values, see src.values_winners.cleaning and missing_values),
and states for each check whether the problem was fixed or is kept on purpose.

Usage (from the repository root):
    python -m src.values_winners.quality_after [csv_folder]

If no folder is given, data/raw/ is used.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.cleaning import JOINT_SEPARATOR
from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.common.quality import ALBANIAN_NIPT, duplicate_rows, has_extra_whitespace, run_checks
from src.values_winners.cleaning import clean
from src.values_winners.columns import COLUMNS, NUMERIC
from src.values_winners.missing_values import mark_disguised_missing
from src.values_winners.quality import REFERENCE, build_checks

OUT_DIR = Path("reports/values_winners")

FIXED = "Rregulluar"
KEPT = "Mbetet qëllimisht"


def names_per_nipt(winner, nipt):
    """NIPTs written with more than one winner name."""
    pairs = pd.DataFrame({"nipt": nipt, "name": winner}).dropna()
    return int(pairs.groupby("nipt")["name"].nunique().gt(1).sum())


def after_checks(df, cancelled):
    """The quality checks on the cleaned columns, with the same names as before cleaning."""
    winner, nipt = df["Fituesi"], df["NIPT_i_fituesit"]
    fund, value, contract = df["Fondi_limit"], df["Vlera_e_fituesit"], df["Vlera_e_fituesit_ne_lidhjen_e_kontrates"]
    single_nipt = nipt.notna() & ~nipt.str.contains(JOINT_SEPARATOR, regex=False, na=False)
    all_rows = pd.Series(True, index=df.index)

    checks = [
        ("Uniqueness", "All columns", "Exact duplicate row (all 21 columns)",
         duplicate_rows(df, [c for c in df.columns if c != "year"]), all_rows),
        ("Uniqueness", REFERENCE, "Reference number used by more than one procedure",
         df[REFERENCE].notna() & df.duplicated(subset=[REFERENCE], keep=False), all_rows),
    ]
    checks += [("Completeness", col, "Missing value", df[col].isna(), all_rows) for col in COLUMNS]
    checks += [
        ("Format", "NIPT_i_fituesit", "Extra whitespace or newlines", has_extra_whitespace(nipt), nipt.notna()),
        ("Format", "Fituesi", "Extra whitespace or newlines", has_extra_whitespace(winner), winner.notna()),
        ("Format", "NIPT_i_fituesit", "Several NIPTs in one cell (joint winners)",
         nipt.str.contains(JOINT_SEPARATOR, regex=False, na=False), nipt.notna()),
        ("Format", "Fituesi", "Several winners in one cell (joint winners)",
         winner.str.contains(JOINT_SEPARATOR, regex=False, na=False), winner.notna()),
        ("Format", "NIPT_i_fituesit", "Single NIPT not in Albanian format (after trimming)",
         single_nipt & ~nipt.str.fullmatch(ALBANIAN_NIPT, na=False), single_nipt),
    ]
    for col, values in [("Fondi_limit", fund), ("Vlera_e_fituesit", value),
                        ("Vlera_e_fituesit_ne_lidhjen_e_kontrates", contract)]:
        checks += [
            ("Accuracy", col, "Value is 0", values.eq(0), values.notna()),
            ("Accuracy", col, "Value between 0 and 1 lek", values.gt(0) & values.le(1), values.notna()),
        ]
    has_fund = fund.gt(0) & value.notna()
    both = value.notna() & contract.notna()
    checks += [
        ("Accuracy", "Vlera_e_fituesit", "Winner value above fund limit", has_fund & value.gt(fund), has_fund),
        ("Accuracy", "Fondi_limit", "Fund is 0 but a winner value exists", fund.eq(0) & value.gt(0), fund.eq(0)),
        ("Consistency", "Fituesi", "Cancelled procedure with a winner", cancelled & winner.notna(), cancelled),
        ("Consistency", "Vlera_e_fituesit", "Cancelled procedure with a winner value",
         cancelled & value.notna(), cancelled),
        ("Consistency", "NIPT_i_fituesit", "NIPT without winner name", nipt.notna() & winner.isna(), nipt.notna()),
        ("Consistency", "Vlera_e_fituesit_ne_lidhjen_e_kontrates", "Contract value differs from winner value",
         both & (contract - value).abs().gt(1), both),
    ]
    return checks


# Why a problem that is still present after cleaning is kept
REASONS = {
    "Reference number used by more than one procedure":
        "Procedura të ndryshme (autoritete të ndryshme); identifikohen me referencë + autoritet",
    "Missing value": "Strategjia e vlerave të zbrazëta: NaN + flag, pa imputim",
    "Several NIPTs in one cell (joint winners)": "Konsorcium: mbahet si një fitues i përbashkët, i ndarë me ' | '",
    "Several winners in one cell (joint winners)": "Konsorcium: mbahet si një fitues i përbashkët, i ndarë me ' | '",
    "Single NIPT not in Albanian format (after trimming)": "Kompani të huaja me numër TVSH të vendit të tyre",
    "Winner value above fund limit": "Vlerë logjikisht e pamundur: trajtohet në Pjesën II",
    "Value is 0": "Vlerë logjikisht e pamundur: trajtohet në Pjesën II",
    "Value between 0 and 1 lek": "Vlerë logjikisht e pamundur: trajtohet në Pjesën II",
    "Cancelled procedure with a winner": "Shënohet me kontrate_e_lidhur / anulim_kontradiktor në dataset-in përfundimtar",
    "Cancelled procedure with a winner value":
        "Shënohet me kontrate_e_lidhur / anulim_kontradiktor në dataset-in përfundimtar",
    "NIPT without winner name": "Emri mungon në burim; NIPT-i mbahet si identifikues",
    "Contract value differs from winner value": "Mund të jetë e rregullt (negociata, TVSH, lote); kontrollohet në Pjesën II",
}


# How a problem that disappears after cleaning was handled
HOW_FIXED = {
    "Extra whitespace or newlines": "Hapësirat dhe rreshtat e rinj (\\n) u hoqën",
    "Amount stored as text": "U kthye në numër (u hoq presja e mijësheve)",
    "Po/Jo stored as text": "U kthye në boolean",
    "Value is 0": "Fondi 0 u shënua si mungesë e maskuar (NaN)",
    "Value between 0 and 1 lek": "Fondi ≤ 1 lek u shënua si mungesë e maskuar (NaN)",
    "Fund is 0 but a winner value exists": "Fondi 0 u shënua si mungesë e maskuar (NaN)",
    "NIPT written with more than one winner name": "Çdo NIPT merr emrin që përdoret më shpesh",
}


def compare(raw, cleaned, cancelled):
    """Before/after table with the status of every check."""
    keys = ["dimension", "column", "check"]
    before = run_checks(raw, build_checks(raw))[keys + ["rows"]].rename(columns={"rows": "para"})
    after = run_checks(cleaned, after_checks(cleaned, cancelled))[keys + ["rows"]].rename(columns={"rows": "pas"})
    table = before.merge(after, on=keys, how="inner")

    extra = pd.DataFrame([
        {"dimension": "Format", "column": col, "check": "Amount stored as text",
         "para": int(raw[col].notna().sum()), "pas": int(pd.api.types.is_string_dtype(cleaned[col]) * cleaned[col].notna().sum())}
        for col in NUMERIC
    ] + [
        {"dimension": "Format", "column": "Lidhja_e_kontrates_me_TVSH", "check": "Po/Jo stored as text",
         "para": int(raw["Lidhja_e_kontrates_me_TVSH"].notna().sum()),
         "pas": int(pd.api.types.is_string_dtype(cleaned["Lidhja_e_kontrates_me_TVSH"]))},
        {"dimension": "Consistency", "column": "Fituesi", "check": "NIPT written with more than one winner name",
         "para": names_per_nipt(raw["Fituesi"], raw["NIPT_i_fituesit"].str.strip()),
         "pas": names_per_nipt(cleaned["Fituesi"], cleaned["NIPT_i_fituesit"])},
    ])
    table = pd.concat([table, extra], ignore_index=True)

    def status(row):
        if row["para"] == 0 and row["pas"] == 0:
            return "Nuk ka problem"
        if row["pas"] < row["para"] and row["pas"] == 0:
            return FIXED
        if row["check"] == "Missing value" and row["pas"] > row["para"]:
            return "Rritet: fondet 0 / ≤ 1 lek u bënë mungesë (mungesa të maskuara)"
        return KEPT

    table["statusi"] = table.apply(status, axis=1)
    table["arsyeja"] = table.apply(
        lambda r: REASONS.get(r["check"], "") if r["statusi"] == KEPT
        else HOW_FIXED.get(r["check"], "") if r["statusi"] == FIXED else "", axis=1)
    above = table["check"].eq("Winner value above fund limit")
    table.loc[above, "arsyeja"] += "; bie sepse fondet ≤ 1 lek u bënë mungesë dhe nuk krahasohen më"
    order = {"Uniqueness": 0, "Completeness": 1, "Format": 2, "Accuracy": 3, "Consistency": 4}
    return table.sort_values("dimension", key=lambda s: s.map(order), kind="stable").reset_index(drop=True)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")

    cleaned = mark_disguised_missing(clean(raw))
    cancelled = raw["Anulluar"].eq("Po")
    table = compare(raw, cleaned, cancelled)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_DIR / "quality_before_after.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_colwidth", 70, "display.max_rows", 100):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
