"""
ESPN fantasy draft assistant (skeleton).

Architecture:
  - draft_context.json  -> STATIC cached prefix (rankings, league rules). Sent identically every pick.
  - live draft state    -> VOLATILE tail (who's drafted, your roster). Changes every pick, NOT cached.

The Anthropic API is stateless: nothing persists between calls. Each pick, your script
resends the cached prefix + the fresh tail. Prompt caching makes the prefix ~90% cheaper to reuse.
"""

import json
import time
import requests
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env

# --- ESPN read-only endpoint (undocumented). Fill these in. -------------------
LEAGUE_ID = "YOUR_LEAGUE_ID"
SEASON = 2026
TEAM_ID = 1
ESPN_COOKIES = {"espn_s2": "YOUR_ESPN_S2", "SWID": "{YOUR_SWID}"}
READ_URL = (
    f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{SEASON}"
    f"/segments/0/leagues/{LEAGUE_ID}?view=mDraftDetail"
)


def load_static_context() -> str:
    """The file on disk -> a string in the payload. This is the cached prefix."""
    with open("draft_context.json", "r", encoding="utf-8") as f:
        return f.read()


def poll_draft_state() -> dict:
    """Poll ESPN for picks so far. Returns {'drafted': [...names...], 'my_roster': [...]}"""
    r = requests.get(READ_URL, cookies=ESPN_COOKIES, timeout=10)
    r.raise_for_status()
    data = r.json()
    picks = data.get("draftDetail", {}).get("picks", [])
    drafted = [p["playerId"] for p in picks]              # map IDs->names via a players view
    my_roster = [p["playerId"] for p in picks if p.get("teamId") == TEAM_ID]
    return {"drafted": drafted, "my_roster": my_roster}


def get_recommendation(static_context: str, state: dict) -> str:
    """
    Static context = cached prefix (marked with cache_control).
    Volatile state  = uncached tail in the user message.
    Anything before the cache_control breakpoint must be byte-identical across picks,
    or you get a cache miss and pay full price. So the drafted list goes AFTER it.
    """
    resp = client.messages.create(
        model="claude-sonnet-4-6",  # fast/cheap for a per-pick loop; swap if you prefer
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": (
                    "You are a fantasy draft advisor. Use the rankings, tiers, VOR, and league "
                    "rules below. Recommend exactly ONE best available player given the drafter's "
                    "roster needs and value. Reply with the player name on the first line, then a "
                    "one-sentence reason.\n\n"
                    + static_context
                ),
                "cache_control": {"type": "ephemeral"},  # <-- breakpoint: everything above is cached
            }
        ],
        messages=[
            {
                "role": "user",
                "content": (
                    f"Already drafted (unavailable): {state['drafted']}\n"
                    f"My current roster: {state['my_roster']}\n"
                    "Who should I take right now?"
                ),
            }
        ],
    )
    return resp.content[0].text


def click_player(player_name: str) -> None:
    """
    STUB. Filter ESPN's on-screen player list by name and click Draft.
    pyautogui (OS-level cursor) is simplest and harder for ESPN to detect than DOM injection,
    but it's pure coordinates -> brittle to scroll/resolution/layout. Playwright clicking by
    text is sturdier but more likely to trip automation flags. Pick your poison; verify the
    name every time before committing the click.
    """
    print(f"[would click] {player_name}")


def main():
    static_context = load_static_context()  # loaded ONCE; resent every pick
    seen = None
    while True:
        state = poll_draft_state()
        if state["drafted"] != seen:          # something changed -> it may be your turn
            seen = state["drafted"]
            rec = get_recommendation(static_context, state)
            name = rec.splitlines()[0].strip()
            print("Recommendation:\n", rec)
            # click_player(name)   # <- uncomment when you trust it; keep a human in the loop first
        time.sleep(5)             # snake picks are ~60-90s; poll well under that


if __name__ == "__main__":
    main()
