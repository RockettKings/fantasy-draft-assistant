"""
build_advanced.py — adds the four requested layers from REAL nflverse data:
  (2) snap share            — % of offensive snaps (workload; is he even on the field)
  (4) Next Gen Stats        — separation, YAC-over-expected, air-yards share (WR/TE);
                              rush-yards-over-expected, efficiency (RB) -> talent vs scheme
  (3) red-zone usage        — carries/targets inside the 20/10/5 -> TD equity
  (5) depth chart + role    — CURRENT 2026 role and target competition per team

Outputs: player_advanced.json (top-200 skill players, 2025) and depth_2026.json (live role).
"""

import json
import nflreadpy as nfl
import polars as pl

Y = 2025

def top200_ids():
    wk = nfl.load_player_stats(seasons=[Y]).filter(
        (pl.col("season_type") == "REG") & pl.col("position").is_in(["QB", "RB", "WR", "TE"])
    )
    agg = (wk.group_by("player_id")
             .agg(name=pl.col("player_display_name").first(), pos=pl.col("position").first(),
                  team=pl.col("team").last(), g=pl.col("week").n_unique(),
                  ppr=pl.col("fantasy_points_ppr").sum())
             .sort("ppr", descending=True).head(200))
    return agg

def main():
    base = top200_ids()
    xwalk = nfl.load_players().select(["gsis_id", "pfr_id"])  # pfr -> gsis for snaps

    # (2) snap share
    snaps = nfl.load_snap_counts(seasons=[Y]).filter(pl.col("game_type") == "REG")
    snaps = (snaps.join(xwalk, left_on="pfr_player_id", right_on="pfr_id", how="left")
                  .group_by("gsis_id").agg(snap_pct=(pl.col("offense_pct").mean() * 100).round(1)))

    # (4) NGS
    rec = nfl.load_nextgen_stats(seasons=[Y], stat_type="receiving").filter(pl.col("week") > 0)
    rec = rec.group_by("player_gsis_id").agg(
        avg_separation=pl.col("avg_separation").mean().round(2),
        air_yards_share=(pl.col("percent_share_of_intended_air_yards").mean()).round(1),
        yac_above_exp=pl.col("avg_yac_above_expectation").mean().round(2),
        catch_pct=pl.col("catch_percentage").mean().round(1),
    )
    rush = nfl.load_nextgen_stats(seasons=[Y], stat_type="rushing").filter(pl.col("week") > 0)
    rush = rush.group_by("player_gsis_id").agg(
        ryoe_per_att=pl.col("rush_yards_over_expected_per_att").mean().round(2),
        rush_efficiency=pl.col("efficiency").mean().round(2),
        rush_pct_over_exp=pl.col("rush_pct_over_expected").mean().round(1),
    )

    # (3) red zone from pbp
    pbp = nfl.load_pbp(seasons=[Y]).filter((pl.col("season_type") == "REG"))
    def rz_rush(thresh):
        return (pbp.filter((pl.col("rush_attempt") == 1) & (pl.col("yardline_100") <= thresh))
                   .group_by("rusher_player_id").agg(pl.len().alias(f"rush_in{thresh}")))
    def rz_tgt(thresh):
        return (pbp.filter((pl.col("pass_attempt") == 1) & (pl.col("yardline_100") <= thresh)
                           & pl.col("receiver_player_id").is_not_null())
                   .group_by("receiver_player_id").agg(pl.len().alias(f"tgt_in{thresh}")))

    df = base
    df = df.join(snaps, left_on="player_id", right_on="gsis_id", how="left")
    df = df.join(rec, left_on="player_id", right_on="player_gsis_id", how="left")
    df = df.join(rush, left_on="player_id", right_on="player_gsis_id", how="left")
    for t in (20, 10, 5):
        df = df.join(rz_rush(t), left_on="player_id", right_on="rusher_player_id", how="left")
        df = df.join(rz_tgt(t), left_on="player_id", right_on="receiver_player_id", how="left")

    players = []
    for r in df.iter_rows(named=True):
        g = max(r["g"], 1)
        ngs = {}
        if r["pos"] in ("WR", "TE", "RB"):
            ngs.update({k: r[k] for k in ("avg_separation", "air_yards_share", "yac_above_exp", "catch_pct") if r[k] is not None})
        if r["pos"] == "RB":
            ngs.update({k: r[k] for k in ("ryoe_per_att", "rush_efficiency", "rush_pct_over_exp") if r[k] is not None})
        players.append({
            "name": r["name"], "pos": r["pos"], "team": r["team"],
            "snap_pct": r["snap_pct"],
            "ngs": ngs,
            "redzone": {
                "carries_in20": r["rush_in20"] or 0, "carries_in10": r["rush_in10"] or 0,
                "carries_in5": r["rush_in5"] or 0,
                "targets_in20": r["tgt_in20"] or 0, "targets_in10": r["tgt_in10"] or 0,
                "rz_touches_pg": round(((r["rush_in20"] or 0) + (r["tgt_in20"] or 0)) / g, 1),
            },
        })

    json.dump({
        "_meta": {
            "source": "nflverse — real 2025 regular season",
            "snap_pct": "avg % of team offensive snaps (workload/role)",
            "ngs": "separation/air_yards_share/yac_above_exp/catch_pct (receiving); ryoe_per_att/efficiency/rush_pct_over_exp (rushing). Talent vs scheme signal.",
            "redzone": "carries & targets inside the 20/10/5 = touchdown equity. rz_touches_pg = red-zone touches per game.",
        },
        "players": players,
    }, open("player_advanced.json", "w"), indent=1)
    print("wrote player_advanced.json —", len(players), "players")

    # (5) CURRENT role + target competition (2026 depth charts, latest snapshot)
    dc = nfl.load_depth_charts(seasons=[2026])
    latest = dc["dt"].max()
    dc = dc.filter((pl.col("dt") == latest) & pl.col("pos_abb").is_in(["QB", "RB", "WR", "TE"]))
    depth = {}
    for team in sorted(dc["team"].unique().to_list()):
        t = dc.filter(pl.col("team") == team)
        role = {}
        for pos in ["QB", "RB", "WR", "TE"]:
            ranked = (t.filter(pl.col("pos_abb") == pos)
                        .sort("pos_rank").select("player_name").to_series().to_list())
            if ranked:
                role[pos] = ranked[:5]
        depth[team] = role
    json.dump({
        "_meta": {
            "source": "nflverse depth charts — current snapshot " + str(latest),
            "use": "Role (starter vs backup) and target competition. Lists are depth order; "
                   "position 1 = projected starter. Refresh near draft day.",
        },
        "depth_by_team": depth,
    }, open("depth_2026.json", "w"), indent=1)
    print("wrote depth_2026.json —", len(depth), "teams")


if __name__ == "__main__":
    main()
