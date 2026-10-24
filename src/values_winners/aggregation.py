"""Aggregation of the value and winner columns on the integrated dataset.

Groups the procedures by year, procedure type, election period, COVID period,
fund category and contracting authority, and aggregates the winners (contracts
and market share per winner).

Amounts are summarized with the **median**: sums and means would be dominated
by the logically impossible values (up to 35 trillion lek) that are handled
in Part II.

Usage (from the repository root):
    python -m src.values_winners.aggregation [csv_folder]

If no folder is given, data/raw/ is used. Per-winner tables are saved to
data/processed/ (not tracked by git); the group tables go to reports/.
"""
import sys
from pathlib import Path

import pandas as pd

from src.common.aggregation import aggregate, share
from src.common.data_loading import DATA_DIR, YEARS, read_years
from src.time_integration.integrated_dataset import integrate, prepare_parts

OUT_DIR = Path("reports/values_winners")
PROCESSED_DIR = Path("data/processed")
TOP_AUTHORITIES = 20
TOP_WINNERS = 20

GROUPS = {
    "year": "year",
    "procedure_type": "Lloji_i_procedures",
    "election_period": "afersia_me_zgjedhjet",
    "covid_period": "periudha_covid",
    "fund_category": "kategoria_e_fondit",
}

METRICS = {
    "with_winner": ("Fituesi", "count"),
    "consortia": ("fitues_i_perbashket", "sum"),
    "with_vat": ("me_tvsh", "sum"),
    "median_fund": ("Fondi_limit", "median"),
    "median_winner_value": ("Vlera_e_fituesit", "median"),
    "median_savings_pct": ("kursimi_pct", "median"),
}


def build_integrated(raw):
    return integrate(prepare_parts(raw))


def by_group(df, column):
    out = aggregate(df, column, METRICS)
    out.insert(2, "with_winner_pct", share(out["with_winner"], out["procedures"]))
    out.insert(len(out.columns) - 3, "with_vat_pct", share(out["with_vat"], out["procedures"]))
    return out


def top_authorities(df):
    out = by_group(df, "Autoriteti_kontraktues")
    return out.sort_values("procedures", ascending=False).head(TOP_AUTHORITIES)


def winners(df):
    """One row per winner (NIPT): contracts, market share and median value."""
    won = df.dropna(subset=["NIPT_i_fituesit"])
    out = aggregate(won, "NIPT_i_fituesit", {
        "winner": ("Fituesi", "first"),
        "years_active": ("year", "nunique"),
        "first_year": ("year", "min"),
        "last_year": ("year", "max"),
        "median_winner_value": ("Vlera_e_fituesit", "median"),
    }).rename(columns={"procedures": "contracts"})
    out.insert(3, "market_share_pct", share(out["contracts"], len(won)))
    return out.sort_values("contracts", ascending=False).reset_index(drop=True)


def concentration(winner_table):
    """How much of the market the largest winners hold (by number of contracts)."""
    total = winner_table["contracts"].sum()
    rows = [{"winners": "All", "count": len(winner_table), "contracts": int(total), "share_pct": 100.0}]
    for n in [1, 10, 100]:
        top = winner_table.head(n)["contracts"].sum()
        rows.append({"winners": f"Top {n}", "count": n, "contracts": int(top),
                     "share_pct": round(top / total * 100, 2)})
    return pd.DataFrame(rows)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA_DIR
    raw = read_years(folder)
    print(f"Years {YEARS.start}-{YEARS.stop - 1}: {len(raw):,} procedures\n")
    df = build_integrated(raw)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    tables = {f"aggregation_by_{name}": by_group(df, col) for name, col in GROUPS.items()}
    tables["aggregation_top_authorities"] = top_authorities(df)

    winner_table = winners(df)
    tables["aggregation_top_winners"] = winner_table.head(TOP_WINNERS)
    tables["aggregation_winner_concentration"] = concentration(winner_table)

    for name, table in tables.items():
        table.to_csv(OUT_DIR / f"{name}.csv", index=False)
    winner_table.to_csv(PROCESSED_DIR / "values_winners_by_winner.csv", index=False)

    with pd.option_context("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 40):
        for name, table in tables.items():
            print(f"{name}:\n{table.to_string(index=False)}\n")


if __name__ == "__main__":
    main()
