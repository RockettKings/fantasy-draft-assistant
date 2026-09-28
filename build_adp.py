"""
build_adp.py — builds adp_2026.json from FantasyPros expert-consensus rankings (via nflverse).
ECR (expert consensus rank) is the ADP proxy the 'don't reach' rule runs on.

Includes best/worst/sd so the assistant can judge how likely a player is to slip to your
next pick: a tight range means take him now or lose him; a wide range means you may be able
to wait. Re-run close to draft day — this scrapes the latest FantasyPros snapshot.
"""

import json
import nflreadpy as nfl
import polars as pl

TOP_N = 240

def main():
    r = nfl.load_ff_rankings()
    ro = r.filter((pl.col("page_type") == "redraft-overall")).sort("ecr")
    scrape = ro["scrape_date"].unique().to_list()[0]

    ro = ro.with_columns(
        pos_clean=pl.col("pos").str.replace(r"\d+$", "")  # strip any trailing rank digits
    )
    # positional rank in ECR order
    ro = ro.with_columns(
        pos_rank=pl.col("ecr").rank("ordinal").over("pos_clean").cast(pl.Int32)
    ).head(TOP_N)

    board = []
    for i, row in enumerate(ro.iter_rows(named=True), 1):
        board.append({
            "overall_rank": i,
            "ecr": round(row["ecr"], 1),
            "player": row["player"],
            "pos": row["pos_clean"],
            "pos_rank": f"{row['pos_clean']}{row['pos_rank']}",
            "team": row["tm"],
            "bye": row["bye"],
            "range": {"best": row["best"], "worst": row["worst"], "sd": round(row["sd"], 1) if row["sd"] else None},
        })

    doc = {
        "_meta": {
            "source": "FantasyPros expert consensus (ECR) via nflverse",
            "scrape_date": scrape,
            "metric": "ecr = expert consensus rank ≈ ADP. overall_rank is the draft board order.",
            "range_note": "best/worst = most optimistic/pessimistic expert; sd = spread. "
                          "Tight range -> take now or lose him. Wide range -> he may slip to your next pick.",
            "players": len(board),
        },
        "adp": board,
    }
    with open("adp_2026.json", "w") as f:
        json.dump(doc, f, indent=1)
    print(f"wrote adp_2026.json — {len(board)} players, scraped {scrape}")


if __name__ == "__main__":
    main()
