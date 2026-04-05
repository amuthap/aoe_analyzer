"""AOE2 AI Coach - LLM-powered analysis using Qwen via OpenAI-compatible API."""

import json
from openai import OpenAI
from knowledge_base import AOE2_KNOWLEDGE_BASE, get_civ_matchup_context, get_player_specific_context
from game_stats import format_player_stats_for_ai

# LLM Config
LLM_BASE_URL = "http://llm.hyperbig.com:4000"
LLM_API_KEY = "sk-GtL5TQcP1PIN2xnPHBtDZg"
LLM_MODEL = "qwen/qwen3.6-plus"

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

SYSTEM_PROMPT = f"""You are a top-100 Age of Empires 2 player reviewing a recorded game. You have access to the FULL replay data: every unit trained, every research completed, every building placed, exact age-up times, and army compositions.

Analyze this game like a pro coach watching the recording. Reference SPECIFIC data points:
- "You trained 163 Archers but only 33 Spearmen — against Khmer elephants you needed Halberdiers"
- "Your Double-Bit Axe came at 15.3min — it should be instant on hitting Feudal at 7-8min"
- "You rang town bell 8 times — that means you had no walls and kept getting raided"
- "You trained 19 War Wagons as Persians — War Wagons are a Korean unit, not yours"

Rules:
- Reference ACTUAL numbers from the data (unit counts, research timings, age-up times)
- Point out specific mistakes with exact timestamps
- Tell them what units they SHOULD have made based on what the enemy built
- Compare their timings to benchmarks for their ELO bracket
- Identify the moment the game was lost/won
- Every sentence must reference game data

OUTPUT FORMAT (mandatory — always use this structure):

## Dark Age (0-10 min)
- bullet points about dark age performance (loom timing, build order, TC idle time, scouting)

## Feudal Age (10-20 min)
- bullet points about feudal decisions (military choice, eco upgrades, walling, aggression)

## Castle Age (20-35 min)
- bullet points about castle age (TC count, army comp, upgrades, map control)

## Imperial Age (35+ min)
- bullet points about late game (trade, composition switches, siege, trash wars)

## Verdict
- 2-3 sentence summary: what lost/won the game, #1 thing to fix

Adjust the time ranges based on the player's actual age-up times. Skip an age section if the game ended before reaching it. Keep each bullet concise (1 sentence max).

{AOE2_KNOWLEDGE_BASE}
"""


def _build_game_summary(analysis: dict) -> str:
    """One-line game summary."""
    return (f"{analysis.get('game_type','?')} | {analysis.get('duration_display','?')} | "
            f"{len(analysis.get('players',[]))} players")


def _build_all_players_block(analysis: dict, coaching: dict) -> str:
    """Build compact player listing for context."""
    lines = []
    for p in analysis.get("players", []):
        status = "WON" if not p.get("resigned") else "LOST"
        lines.append(f"  [T{p.get('team','?')}] {p['name']} | {p['civilization']} | "
                     f"ELO:{p.get('elo',0)} EAPM:{p.get('eapm',0)} | {status}")
    return "\n".join(lines)


def _build_player_deep_context(player_name: str, analysis: dict, coaching: dict) -> str:
    """Build deep context for a specific player including full game stats."""
    lines = []
    player = None
    player_index = None
    for i, p in enumerate(analysis.get("players", [])):
        if player_name.lower() in p["name"].lower():
            player = p
            player_index = i
            break
    if not player:
        return f"Player '{player_name}' not found in game data."

    duration_min = analysis.get("duration_seconds", 0) / 60

    # Player's ELO-level context
    lines.append(get_player_specific_context(
        player["civilization"], player.get("elo", 0),
        player.get("eapm", 0), duration_min,
        not player.get("resigned", True)
    ))

    # === DEEP GAME STATS ===
    game_stats = analysis.get("game_stats", {})
    # Find player's stats by matching player index+1 (player IDs are 1-based)
    pid_str = str(player_index + 1) if player_index is not None else None
    # Try to find by matching player name in stats keys
    if pid_str and pid_str in game_stats:
        pstats = game_stats[pid_str]
        lines.append("")
        lines.append(format_player_stats_for_ai(player_name, pstats, duration_min))
    else:
        # Try all keys
        for pid_key, pstats in game_stats.items():
            lines.append("")
            lines.append(f"(Stats key {pid_key} available but couldn't match to player)")
            break

    # Opponent civs (from player's perspective)
    player_team = player.get("team")
    opponents = [p for p in analysis["players"] if p.get("team") != player_team]
    opp_civs = [p["civilization"] for p in opponents]
    if opp_civs:
        lines.append("")
        lines.append(f"Enemy civs you faced: {', '.join(opp_civs)}")
        lines.append(get_civ_matchup_context(player["civilization"], opp_civs[0]))

        # Include opponent army composition if available
        for oi, opp in enumerate(opponents):
            opp_pid = None
            for j, ap in enumerate(analysis["players"]):
                if ap["name"] == opp["name"]:
                    opp_pid = str(j + 1)
                    break
            if opp_pid and opp_pid in game_stats:
                os = game_stats[opp_pid]
                opp_units = os.get("units_trained", {})
                top_opp = [(n, c) for n, c in sorted(opp_units.items(), key=lambda x: -x[1]) if n != "Villager"][:4]
                if top_opp:
                    lines.append(f"  {opp['name']} built: {', '.join(f'{n}({c})' for n, c in top_opp)}")

    # Civ bonuses
    for r in coaching.get("player_reports", []):
        if player_name.lower() in r.get("name", "").lower():
            if r.get("civ_bonuses"):
                lines.append(f"\nYour civ bonuses: {'; '.join(r['civ_bonuses'][:3])}")
            if r.get("unique_units"):
                lines.append(f"Your unique units: {', '.join(r['unique_units'])}")
            break

    return "\n".join(lines)


def _build_team_context(team_id: str, analysis: dict, coaching: dict) -> str:
    """Build context for an entire team."""
    lines = []
    team_players = [p for p in analysis["players"] if str(p.get("team")) == str(team_id)]
    if not team_players:
        return f"Team {team_id} not found."

    won = not any(p.get("resigned") for p in team_players)
    lines.append(f"Team {team_id} ({'WON' if won else 'LOST'}):")

    for p in team_players:
        lines.append(f"  {p['name']} | {p['civilization']} | ELO:{p.get('elo',0)} EAPM:{p.get('eapm',0)}")
        lines.append(f"    " + get_player_specific_context(
            p["civilization"], p.get("elo", 0), p.get("eapm", 0),
            analysis.get("duration_seconds", 0) / 60, not p.get("resigned", True)
        ).replace("\n", "\n    "))

    # Opponents
    opp_players = [p for p in analysis["players"] if str(p.get("team")) != str(team_id)]
    if opp_players:
        lines.append(f"\nOpponents (Team {opp_players[0].get('team','?')}):")
        for p in opp_players:
            lines.append(f"  {p['name']} | {p['civilization']} | ELO:{p.get('elo',0)} EAPM:{p.get('eapm',0)}")

    return "\n".join(lines)


def get_ai_analysis(analysis_dict: dict, coaching_dict: dict,
                    mode: str = "game", target: str = None,
                    focus_player: str = None) -> dict:
    """Get AI-powered analysis from Qwen LLM.

    Modes:
        game: Full game analysis
        player: Specific player analysis (target = player name)
        team: Specific team analysis (target = team id)
    """
    try:
        game_summary = _build_game_summary(analysis_dict)
        all_players = _build_all_players_block(analysis_dict, coaching_dict)

        if mode == "player" and target:
            deep_context = _build_player_deep_context(target, analysis_dict, coaching_dict)

            # Build teammate context
            player_team = None
            for p in analysis_dict.get("players", []):
                if target.lower() in p["name"].lower():
                    player_team = p.get("team")
                    break
            teammates = [p for p in analysis_dict["players"]
                         if p.get("team") == player_team and target.lower() not in p["name"].lower()]
            teammate_lines = "\n".join(
                f"  {t['name']} ({t['civilization']}) ELO:{t.get('elo',0)} EAPM:{t.get('eapm',0)}"
                for t in teammates
            ) if teammates else "None (1v1)"

            user_prompt = (
                f"Game: {game_summary}\n\n"
                f"=== COACHING FOR: {target} ===\n{deep_context}\n\n"
                f"Teammates:\n{teammate_lines}\n\n"
                f"You are reviewing this game as a pro coach watching {target}'s recording. "
                f"Talk directly to them as 'you'. Analyze their ACTUAL game data:\n"
                f"1. Their exact age-up times vs benchmarks for their ELO\n"
                f"2. Their army composition — did they make the right units? Reference exact counts\n"
                f"3. Their eco upgrade timings — were Double-Bit Axe, Horse Collar on time?\n"
                f"4. Their civ bonuses — did they actually use their unique strengths?\n"
                f"5. When they got raided (town bells), what they should have done\n"
                f"6. What they should have built differently based on what enemies made\n"
                f"Frame opponents from the player's perspective only: "
                f"'they built 90 knights so you needed halbs, not more archers'.\n"
                f"Reference specific numbers from the data. Every claim must have evidence."
            )
        elif mode == "team" and target:
            team_context = _build_team_context(target, analysis_dict, coaching_dict)
            user_prompt = (
                f"Game: {game_summary}\nAll players:\n{all_players}\n\n"
                f"=== TEAM ANALYSIS ===\n{team_context}\n\n"
                f"Analyze this team's performance together. How was their coordination? "
                f"Did the flank/pocket roles make sense for their civs? What should they "
                f"have done differently as a team? Who was the weak link and how can they improve?"
            )
        else:
            # Full game
            player_name = focus_player or target or ""
            user_prompt = (
                f"Game: {game_summary}\nAll players:\n{all_players}\n\n"
                f"Analyze this full game. Who played well and why? Who struggled? "
                f"What decided the game — was it eco, military, or strategy? "
                f"Give the top 3 takeaways."
            )
            if player_name:
                deep = _build_player_deep_context(player_name, analysis_dict, coaching_dict)
                user_prompt += f"\n\nFocus especially on: {player_name}\n{deep}"

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )

        return {
            "success": True,
            "analysis": response.choices[0].message.content,
            "model": LLM_MODEL,
            "tokens_used": response.usage.total_tokens if response.usage else 0,
        }

    except Exception as e:
        return {
            "success": False,
            "analysis": "",
            "model": LLM_MODEL,
            "tokens_used": 0,
            "error": str(e),
        }
