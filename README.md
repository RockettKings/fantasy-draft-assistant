# Fantasy Draft Project — knowledge files

Drop these into a Claude Project. On draft day, tell me who's already been taken and your
current roster, then ask **"what's the next best pick?"** I'll read these files, cross-reference
them, and search recent news (injuries, depth-chart moves, holdouts) before answering.

**Feed me each pick as it happens.** Your league is casuals who chase big names, so the board
won't follow ADP. That's an edge: I read how your specific room is drafting and surface the
value sliding toward you, instead of assuming picks go by consensus. A QB going in round 1
doesn't break the logic — it just means better value is falling to you elsewhere.

## What's here

- **player_stats.json** — 200 players, real 2025 stats (+2023–24 trend) from nflverse.
  The core reasoning basis: opportunity (target share, WOPR, touches/g), efficiency
  (YPT, YAC, EPA), consistency (floor, ceiling, boom rate). *History, not a projection.*
- **team_defense_vs_position.json** — PPR points each defense allowed per game to QB/RB/WR/TE
  in 2025, ranked. Mostly a weekly-lineup tool; minor draft tiebreaker.
- **strength_of_schedule.json** — each team's 2026 opponents by week, scored against 2025
  defensive strength. Season + playoff (wks 15–17) SOS with ranks. Tiebreaker only.
- **rookies_2026.json** — upside board for the 2026 rookie class (no NFL stats exist yet),
  built from draft capital, landing spot, role, and preseason news. Ceiling bets.
- **draft_strategy.md** — standing rules: don't over-stack one NFL team (QB+pass-catcher
  stacks excepted), and don't reach — draft against ADP.
- **adp_2026.json** — FantasyPros expert-consensus ranks (ADP proxy) for 240 players, with
  each player's best/worst expert range. This is what the "don't reach" rule runs on.
- **player_advanced.json** — deeper layer for 200 players: snap share, Next Gen Stats
  (separation, YAC-over-expected, air-yards share; rush-yards-over-expected), and red-zone
  usage (carries/targets inside the 20/10/5 = touchdown equity).
- **depth_2026.json** — current role and target competition per team (depth-chart order),
  refreshed near draft day.
- **espn_avoid_2026.json** — do-not-draft / bust consensus (ESPN's Karabell list + other
  sources, labeled), each with a paraphrased reason and their REAL 2025 stat line. Players on
  it are also stamped with an `avoid` flag inside player_stats / player_advanced / adp /
  rookies, so the warning shows up wherever I look.

## How I'll weigh them (so you know what you're getting)

1. **Talent + opportunity first** (player_stats) — volume is the stickiest predictor.
2. **ADP check** (draft_strategy) — is this the pick, or can you wait and grab someone
   scarcer first? Don't reach on a player who'll be there next round.
3. **Roster fit + construction** — positional need, bye conflicts, floor vs ceiling, and
   don't clog your lineup with multiple same-team skill players (a QB + his own WR/TE is
   the good exception).
4. **Rookies** (rookies_2026) — mid/late-round upside swings once the safe picks are gone.
5. **Recent news** (live search) — overrides stale stats; a torn ACL beats any WOPR.
6. **Avoid-list check** — if a player is flagged `avoid`, I'll say so and why. It's not an
   automatic pass: a bust at ADP can become fair value if your casual room lets him slide far
   enough. The flag tempers the price, it doesn't ban the player.
7. **Schedule/matchup last** — a genuine tiebreaker, strongest for playoff-week slates.

## Honest limits

- Stats are historical. A 2025 breakout with a new team/OC won't be captured — that's what
  the live news search is for.
- **No rookies** (no NFL history to pull). Ask me about them and I'll go off news + draft capital.
- Defenses shift year to year, so SOS is soft. Don't let it outweigh a better player.
- ADP in `adp_2026.json` is an Aug 28 snapshot — re-run `build_adp.py` closer to your draft
  (or on the day) so the "don't reach" logic uses the freshest board.
- The avoid list has ESPN's four confirmed names (Karabell) plus other sources; ESPN's full
  list is longer but their pages are JS-rendered and wouldn't extract cleanly. The stat lines
  are real 2025 actuals — ESPN's *projected* lines aren't pullable here, but I can fetch a
  specific ESPN projection by search on draft day. Team files (defense/SOS/depth) don't carry
  the per-player flag; it lives in the player-keyed files and the standalone avoid file.

## Refreshing the data

Re-run `build_stats.py` and `build_matchups.py` (need `pip install nflreadpy`) to pull the
latest — useful in-season, or to swap 2025 for 2026 once games are played.
