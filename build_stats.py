"""
build_stats.py — pulls REAL NFL data from nflverse and builds player_stats.json,
the statistical basis your draft assistant reasons over.

Why these stats (the "rhyme or reason"):
  OPPORTUNITY predicts fantasy points better than efficiency, because volume is stickier
  year to year than yards-per-touch. So the file leans on:
    - ppg_ppr        : points per game (PPR) — the historical target itself
    - touches_pg     : carries + receptions per game (raw volume)
    - target_share   : % of team targets — the single best WR/TE opportunity signal
    - wopr           : weighted opportunity rating (1.5*target_share + 0.7*air_yards_share)
    - air_yards_share: downfield usage (ceiling indicator)
  EFFICIENCY (regresses, but flags talent/role):
    - ypt            : yards per target;  yac_pr : YAC per reception
    - epa_pg         : expected points added per game
  AVAILABILITY & CONSISTENCY (floor vs ceiling):
    - games          : durability
    - ppr_std        : week-to-week volatility
    - floor / ceiling: 25th / 85th percentile weekly PPR
    - boom_rate      : share of games above a startable weekly threshold

Re-run this in-season for 2026 to refresh. Regular season only.
"""

import json
import nflreadpy as nfl
import polars as pl

SEASONS = [2023, 2024, 2025]      # 2025 = most recent complete season
PRIMARY = 2025                    # season the assistant weights most
POSITIONS = ["QB", "RB", "WR", "TE"]
TOP_N = 200                       # cap the file so the cached prefix stays token-reasonable
BOOM = {"QB": 20, "RB": 15, "WR": 15, "TE": 12}   # weekly PPR "startable game" thresholds


def build_season(year: int) -> pl.DataFrame:
    wk = nfl.load_player_stats(seasons=[year])
    wk = wk.filter((pl.col("season_type") == "REG") & pl.col("position").is_in(POSITIONS))

    # weekly consistency stats
    consist = wk.group_by("player_id").agg(
        games=pl.len(),
        ppr_std=pl.col("fantasy_points_ppr").std(),
        floor=pl.col("fantasy_points_ppr").quantile(0.25),
        ceiling=pl.col("fantasy_points_ppr").quantile(0.85),
    )

    # season aggregates -> per game
    agg = wk.group_by("player_id").agg(
        name=pl.col("player_display_name").first(),
        pos=pl.col("position").first(),
        team=pl.col("team").last(),
        g=pl.len(),
        ppr=pl.col("fantasy_points_ppr").sum(),
        touches=(pl.col("carries") + pl.col("receptions")).sum(),
        targets=pl.col("targets").sum(),
        rec_yards=pl.col("receiving_yards").sum(),
        yac=pl.col("receiving_yards_after_catch").sum(),
        receptions=pl.col("receptions").sum(),
        target_share=pl.col("target_share").mean(),
        air_yards_share=pl.col("air_yards_share").mean(),
        wopr=pl.col("wopr").mean(),
        epa=(pl.col("receiving_epa").fill_null(0) + pl.col("rushing_epa").fill_null(0)
             + pl.col("passing_epa").fill_null(0)).sum(),
    )

    # boom rate per player
    booms = (
        wk.with_columns(
            thr=pl.col("position").replace_strict(BOOM, default=15),
        )
        .with_columns(boom=(pl.col("fantasy_points_ppr") >= pl.col("thr")).cast(pl.Int8))
        .group_by("player_id")
        .agg(boom_rate=pl.col("boom").mean())
    )

    out = (
        agg.join(consist, on="player_id", how="left")
        .join(booms, on="player_id", how="left")
        .with_columns(
            season=pl.lit(year),
            ppg_ppr=(pl.col("ppr") / pl.col("g")).round(1),
            touches_pg=(pl.col("touches") / pl.col("g")).round(1),
            targets_pg=(pl.col("targets") / pl.col("g")).round(1),
            ypt=pl.when(pl.col("targets") > 0)
                .then(pl.col("rec_yards") / pl.col("targets")).otherwise(0).round(2),
            yac_pr=pl.when(pl.col("receptions") > 0)
                .then(pl.col("yac") / pl.col("receptions")).otherwise(0).round(2),
            epa_pg=(pl.col("epa") / pl.col("g")).round(2),
            ppr_std=pl.col("ppr_std").round(1),
            floor=pl.col("floor").round(1),
            ceiling=pl.col("ceiling").round(1),
            boom_rate=pl.col("boom_rate").round(2),
            target_share=pl.col("target_share").round(3),
            air_yards_share=pl.col("air_yards_share").round(3),
            wopr=pl.col("wopr").round(3),
        )
    )
    return out


def main():
    seasons = {yr: build_season(yr) for yr in SEASONS}
    primary = seasons[PRIMARY].sort("ppr", descending=True).head(TOP_N)

    players = []
    for row in primary.iter_rows(named=True):
        pid = row["player_id"]
        # attach prior-year ppg for trend, where it exists
        history = {}
        for yr in SEASONS:
            hit = seasons[yr].filter(pl.col("player_id") == pid)
            if hit.height:
                r = hit.row(0, named=True)
                history[str(yr)] = {"ppg_ppr": r["ppg_ppr"], "games": r["g"]}
        players.append({
            "name": row["name"], "pos": row["pos"], "team": row["team"],
            "season": PRIMARY, "games": row["g"],
            "ppg_ppr": row["ppg_ppr"],
            "opportunity": {
                "touches_pg": row["touches_pg"], "targets_pg": row["targets_pg"],
                "target_share": row["target_share"], "air_yards_share": row["air_yards_share"],
                "wopr": row["wopr"],
            },
            "efficiency": {"ypt": row["ypt"], "yac_per_rec": row["yac_pr"], "epa_pg": row["epa_pg"]},
            "consistency": {
                "ppr_std": row["ppr_std"], "floor": row["floor"],
                "ceiling": row["ceiling"], "boom_rate": row["boom_rate"],
            },
            "ppg_by_season": history,
        })

    doc = {
        "_meta": {
            "source": "nflverse (nflreadpy) — real regular-season data",
            "primary_season": PRIMARY, "seasons_pulled": SEASONS,
            "players": len(players),
            "note": "Historical stats only — NOT a projection. Pair with live ADP/expert "
                    "rankings for the actual pick. Rookies won't appear (no NFL history); "
                    "add them from a rankings source.",
            "glossary": {
                "wopr": "1.5*target_share + 0.7*air_yards_share; best single WR/TE opportunity metric",
                "boom_rate": "share of games at/above a startable weekly PPR score",
                "floor/ceiling": "25th / 85th percentile weekly PPR",
            },
        },
        "players": players,
    }
    with open("player_stats.json", "w") as f:
        json.dump(doc, f, indent=1)
    print(f"wrote player_stats.json — {len(players)} players")


if __name__ == "__main__":
    main()
