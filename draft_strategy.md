# Draft strategy — rules to apply on every pick

These are standing instructions for how to pick. Apply them alongside the stats files.

## 1. Don't over-stack one NFL team

Clustering several skill players from the **same NFL team** concentrates risk: shared bye
week, one bad game for that offense tanks multiple starters, and same-team pass-catchers
cannibalize each other's targets.

- **Avoid:** two or more of the same team's RB/WR/TE clogging your starting lineup
  (e.g., two WRs from the same offense fighting for the same targets).
- **Fine — and sometimes good:** a **QB + one of his own pass-catchers** (a "stack").
  Their scoring is positively correlated — a QB-to-WR touchdown scores for both — so a
  QB+WR or QB+TE pairing is a *profitable* correlation, not a redundancy. **QB + RB** is
  neutral and also fine.
- **The test:** pair players from one team only when it's a QB+pass-catcher stack that's
  genuinely the best value on the board. Otherwise spread exposure across offenses.
  Never take the second same-team skill player just because you like the team.

## 2. Don't reach — take the value, not the name

Never spend a pick on a player you could reasonably still get a round (or two) later.
The goal is maximum talent per draft slot, which means drafting against **ADP** (average
draft position), not gut.

- Before recommending a pick, weigh the player's ADP against **when your next pick comes**
  (in a snake draft your turns are far apart at the turn, close together in the middle).
- If a target will very likely still be there at your next pick, take the **scarcer or
  higher-value** player now and circle back to them.
- Only "reach" (pick ahead of ADP) when: positional scarcity is about to cliff, it
  completes a profitable stack, or the player's live news has clearly outrun a stale ADP.
- **Requires live ADP.** Either add an ADP export to the Project knowledge, or I'll pull
  current ADP via search on draft day. Rookie ADP notes live in `rookies_2026.json`.

## 3. ADP is VALUE, not a schedule — adapt to the actual room

Critical: `adp_2026.json` (expert consensus) tells you what a player is *worth*. It does **not**
predict when *your* room will draft him. Your league is casuals who chase big names, so the
board will not follow ADP — and that's an **edge**, not a problem.

- **Big names and QBs will go early (overdrafted).** When Bo Nix goes in the first round,
  that is NOT a signal to draft a QB. It means real value at other positions is sliding toward
  you. Let the names go; scoop the players falling past their ADP.
- **Never chase the room's reaches.** One casual overpick doesn't change what anyone is worth.
  Don't match a reach just because someone "went here."
- **The "can I wait?" question is answered by THIS room, not national ADP.** Feed me each pick
  as it happens. I track how your room drafts (QB-happy? name-chasing? position runs?) and
  compare who's actually gone vs. their ADP to surface the biggest value left on the board.
- **Only move up when:** a real run is starting at a position you *need* and you won't get back
  to it, or a specific target realistically won't survive to your next pick *given how this
  room is drafting* — not because a name "should" go here nationally.

So the logic never breaks on a weird pick: value is anchored to ADP, timing is learned live
from the room. A casual room drafting badly just means more value falls to you.

## 4. Avoid flags are a discount trigger, not a ban

A player carrying an `avoid` flag (see `espn_avoid_2026.json`) is not off-limits. The flag
means "don't pay full price for this risk" — but the manager IS willing to gamble when the
player slides far enough that the reward beats the risk. Apply it as a price rule:

- **At or above ADP → pass.** Paying market price for a known injury/role/regression risk is
  the trap the list exists to prevent.
- **Slid past ADP → live candidate.** Once he falls enough that his risk-adjusted value beats
  the best clean alternative on the board for a position of need, take the swing. Rough
  discount needed, scaled to the reason:
  - **Availability risk** (McCaffrey, Nabers, Skattebo): needs the biggest slide for a
    *starting* slot; a smaller slide is fine if it's a **bench stash** you can absorb.
  - **Role/committee or unsustainable-efficiency** (Tuten, Stafford, Jeudy): a moderate
    slide is enough — the downside is a lower ceiling/floor, not a zero.
  - **Rookie-hype caution** (Love): treat as "don't pay the hype tax"; fair at a discount to
    the hype price, strong value if he falls to his floor cost.
- **When I recommend a flagged player, I'll say it out loud:** name the flag, the reason, how
  far he's slid past ADP, and why the discount now makes the gamble worth it (or not).

The point: the list tempers the *price*, and I'll pull the trigger when the price is right.

## How I'll fold these in when you ask "what's the next best pick?"

1. Best available by talent + opportunity (player_stats) and roster need.
2. **ADP check** (adp_2026 + the room's live behavior) — is this the pick, or does the way
   *this* room is drafting mean I can grab someone scarcer first and circle back? I won't tell
   you to match a casual reach.
3. **Roster-construction check** — does this over-stack a team? If so, is it a QB+pass-catcher
   stack worth the correlation, or should I pivot to a different offense?
4. **Avoid-flag check** — if flagged, is he still at/above ADP (pass) or has he slid enough
   that the discount makes the gamble worth it (take the swing, and I'll say why)?
5. Live news override (injuries, depth chart) — always wins over stale numbers.
6. Schedule/matchup as the final tiebreaker.
