"""
build_matchups.py — builds two files from REAL nflverse data:
  1. team_defense_vs_position.json : PPR points each defense allowed per game to QB/RB/WR/TE (2025)
  2. strength_of_schedule.json     : each team's 2026 opponents, scored against 2025 defensive strength

Honest caveat baked into both: defensive strength is measured from 2025 and used as a proxy for
2026. Defenses are unstable year to year, so treat SOS as a tiebreaker — strongest for spotting soft
PLAYOFF slates (weeks 15-17) for your studs, not as a primary draft signal.
"""

import json
import nflreadpy as nfl
import polars as pl

DEF_SEASON = 2025      # measure defenses from most recent complete season
SCHED_SEASON = 2026    # upcoming season's opponents
POSITIONS = ["QB", "RB", "WR", "TE"]
PLAYOFF_WEEKS = [15, 16, 17]


def defense_vs_position():
    wk = nfl.load_player_stats(seasons=[DEF_SEASON])
    wk = wk.filter((pl.col("season_type") == "REG") & pl.col("position").is_in(POSITIONS))
    # points a player scored count AGAINST their opponent's defense
    d = (
        wk.group_by(["opponent_team", "position"])
        .agg(pts=pl.col("fantasy_points_ppr").sum(), gm=pl.col("week").n_unique())
        .with_columns(ppg_allowed=(pl.col("pts") / pl.col("gm")).round(1))
    )
    # rank within each position: rank 1 = allows the MOST = softest matchup
    d = d.with_columns(
        rank=pl.col("ppg_allowed").rank("ordinal", descending=True).over("position").cast(pl.Int32)
    )
    table = {}
    for row in d.iter_rows(named=True):
        t = row["opponent_team"]
        table.setdefault(t, {})[row["position"]] = {
            "ppr_allowed_pg": row["ppg_allowed"], "rank_softest": row["rank"]
        }
    # overall PPR allowed per game to all skill positions (for SOS)
    overall = (
        wk.group_by("opponent_team")
        .agg(pts=pl.col("fantasy_points_ppr").sum(), gm=pl.col("week").n_unique())
        .with_columns(all_pos_ppr_pg=(pl.col("pts") / pl.col("gm")).round(1))
    )
    strength = {r["opponent_team"]: r["all_pos_ppr_pg"] for r in overall.iter_rows(named=True)}
    return table, strength


def strength_of_schedule(def_strength: dict):
    sched = nfl.load_schedules(seasons=[SCHED_SEASON]).select(
        ["week", "home_team", "away_team"]
    )
    # build opponent list per team
    opps = {}
    for r in sched.iter_rows(named=True):
        opps.setdefault(r["home_team"], []).append((r["week"], r["away_team"]))
        opps.setdefault(r["away_team"], []).append((r["week"], r["home_team"]))

    league_avg = sum(def_strength.values()) / len(def_strength)
    out = {}
    for team, games in opps.items():
        games.sort()
        season_vals = [def_strength.get(o) for _, o in games if def_strength.get(o)]
        po_vals = [def_strength.get(o) for w, o in games if w in PLAYOFF_WEEKS and def_strength.get(o)]
        out[team] = {
            "opponents_by_week": {str(w): o for w, o in games},
            "season_sos": round(sum(season_vals) / len(season_vals), 1) if season_vals else None,
            "playoff_sos": round(sum(po_vals) / len(po_vals), 1) if po_vals else None,
            # higher number = opponents allowed more points = EASIER schedule
        }
    # add ranks (1 = easiest)
    for key in ("season_sos", "playoff_sos"):
        ranked = sorted([t for t in out if out[t][key] is not None],
                        key=lambda t: out[t][key], reverse=True)
        for i, t in enumerate(ranked, 1):
            out[t][key.replace("_sos", "_rank_easiest")] = i
    return out, round(league_avg, 1)


def main():
    dvp, strength = defense_vs_position()
    with open("team_defense_vs_position.json", "w") as f:
        json.dump({
            "_meta": {
                "source": "nflverse — real 2025 regular season",
                "metric": "PPR fantasy points allowed per game by each defense to each position",
                "rank_softest": "1 = allowed the most points to that position (best matchup to attack)",
                "use": "Weekly lineup tool. Minor draft input (matchup < season-long talent/volume).",
            },
            "defense_vs_position": dvp,
        }, f, indent=1)
    print("wrote team_defense_vs_position.json —", len(dvp), "teams")

    sos, league_avg = strength_of_schedule(strength)
    with open("strength_of_schedule.json", "w") as f:
        json.dump({
            "_meta": {
                "schedule_season": SCHED_SEASON,
                "defense_measured_from": DEF_SEASON,
                "league_avg_ppr_allowed_pg": league_avg,
                "reading": "season_sos / playoff_sos = avg PPR opponents' defenses allowed per game "
                           "in 2025. HIGHER = easier. rank_easiest 1 = softest schedule.",
                "caveat": "Defenses shift year to year; use as a tiebreaker, strongest for playoff "
                          "weeks 15-17.",
            },
            "strength_of_schedule": sos,
        }, f, indent=1)
    print("wrote strength_of_schedule.json —", len(sos), "teams")


if __name__ == "__main__":
    main()
