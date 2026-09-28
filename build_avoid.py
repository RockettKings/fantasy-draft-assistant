"""
build_avoid.py — builds espn_avoid_2026.json (do-not-draft / bust consensus with REAL 2025
stat lines) and stamps an "avoid" flag onto every matching player in the player-keyed files,
so the warning travels with the player wherever the assistant looks.

Reasons are paraphrased (not copied). ESPN = Eric Karabell's 'Do Not Draft' list; other names
are the broader cross-site bust consensus, labeled by source. ESPN's full list is longer than
the four confirmed here — ESPN pages are JS-rendered and didn't return clean text.
"""

import json
import nflreadpy as nfl
import polars as pl

OUT = "/mnt/user-data/outputs"

# name -> (pos, team, source, paraphrased reason)
AVOID = {
    "Christian McCaffrey": ("RB", "SF", "ESPN (Karabell)",
        "400+ touches and 900+ snaps in 2025; RBs historically don't repeat after 400-carry seasons, plus a long injury history."),
    "Malik Nabers": ("WR", "NYG", "ESPN (Karabell)",
        "ACL + meniscus tear in Week 4 2025 that needed a follow-up procedure; Week 1 availability uncertain."),
    "Cam Skattebo": ("RB", "NYG", "ESPN (Karabell)",
        "Reckless style = injury risk; likely a committee with Tracy/Singletary/Harris; ADP too rich for that role."),
    "Jaxson Dart": ("QB", "NYG", "ESPN (Karabell)",
        "Young Giants trio barely shared the field in 2025; availability and consistency unproven at his cost."),
    "De'Von Achane": ("RB", "MIA", "Sporting News",
        "Loses McDaniel's RB-centric scheme; Miami offense looks shakier, threatening his volume."),
    "Jerry Jeudy": ("WR", "CLE", "FantasyPros",
        "Finished WR51 in 2025 with poor yards-per-route and points below expectation; Browns drafted two WRs early under new staff."),
    "Matthew Stafford": ("QB", "LAR", "FantasyPros",
        "46 pass TDs on a 7.7% TD rate is historically unsustainable; no rushing to fall back on if TDs regress."),
    "Bhayshul Tuten": ("RB", "JAX", "FanDuel / ESPN tiers",
        "ADP climbed into the top ~60 on breakout hype, but his role is uncertain and he's shown little as a pass-catcher."),
    "Jeremiyah Love": ("RB", "ARI", "Sporting News (hype caution)",
        "Rookie hype outrunning reality: preseason high-ankle sprain, Allgeier starting Week 1, backfield crowded with Conner/Benson."),
}


def stat_lines():
    wk = nfl.load_player_stats(seasons=[2025]).filter(pl.col("season_type") == "REG")
    lines = {}
    for n in AVOID:
        r = wk.filter(pl.col("player_display_name") == n)
        if r.height == 0:
            lines[n] = {"note": "no 2025 NFL stats (rookie)"}
            continue
        g = r["week"].n_unique()
        line = {"season": 2025, "games": g,
                "ppg_ppr": round(r["fantasy_points_ppr"].sum() / g, 1)}
        ry, rtd = int(r["rushing_yards"].sum()), int(r["rushing_tds"].sum())
        rec, recy, rectd = int(r["receptions"].sum()), int(r["receiving_yards"].sum()), int(r["receiving_tds"].sum())
        py, ptd = int(r["passing_yards"].sum()), int(r["passing_tds"].sum())
        if py: line["passing"] = {"yards": py, "tds": ptd}
        if ry or rtd: line["rushing"] = {"yards": ry, "tds": rtd}
        if rec: line["receiving"] = {"rec": rec, "yards": recy, "tds": rectd}
        lines[n] = line
    return lines


def norm(s):
    return s.lower().replace(".", "").replace("'", "").replace("  ", " ").strip()


def main():
    lines = stat_lines()

    avoid_doc = {
        "_meta": {
            "purpose": "Do-not-draft / bust consensus. These aren't bad players — they're bad VALUE at current ADP (injury, workload, role, or unsustainable 2025). Weigh against the room: if one slides well past ADP, the discount can make them worth it.",
            "espn_note": "ESPN entries are Eric Karabell's 'Do Not Draft' list (confirmed names only; full list is longer). Others labeled by source.",
            "stat_line": "Real 2025 regular-season actuals from nflverse — NOT a projection.",
        },
        "avoid": [
            {"name": n, "pos": AVOID[n][0], "team": AVOID[n][1],
             "source": AVOID[n][2], "reason": AVOID[n][3], "stat_line_2025": lines[n]}
            for n in AVOID
        ],
    }
    json.dump(avoid_doc, open(f"{OUT}/espn_avoid_2026.json", "w"), indent=1)
    print("wrote espn_avoid_2026.json —", len(AVOID), "players")

    # stamp flag onto player-keyed files
    lookup = {norm(n): {"source": AVOID[n][2], "reason": AVOID[n][3]} for n in AVOID}
    targets = {
        "player_stats.json": ("players", "name"),
        "player_advanced.json": ("players", "name"),
        "adp_2026.json": ("adp", "player"),
        "rookies_2026.json": ("rookies", "name"),
    }
    for fname, (arr_key, name_key) in targets.items():
        path = f"{OUT}/{fname}"
        doc = json.load(open(path))
        hits = 0
        for entry in doc[arr_key]:
            flag = lookup.get(norm(entry[name_key]))
            if flag:
                entry["avoid"] = flag
                hits += 1
        doc["_meta"]["avoid_flag"] = "players carrying an 'avoid' field are on a do-not-draft/bust list (see espn_avoid_2026.json)"
        json.dump(doc, open(path, "w"), indent=1)
        print(f"  flagged {hits} in {fname}")


if __name__ == "__main__":
    main()
