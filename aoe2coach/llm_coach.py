"""AOE2 AI Coach - LLM-powered analysis using Qwen via OpenAI-compatible API."""

import json
from openai import OpenAI
from knowledge_base import AOE2_KNOWLEDGE_BASE, get_civ_matchup_context, get_player_specific_context

# LLM Config
LLM_BASE_URL = "http://llm.hyperbig.com:4000"
LLM_API_KEY = "sk-GtL5TQcP1PIN2xnPHBtDZg"
LLM_MODEL = "qwen/qwen3.6-plus"

client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

SYSTEM_PROMPT = f"""You are an expert Age of Empires 2: Definitive Edition coach with deep knowledge of all 53 civilizations, tech trees, unit counters, build orders, and meta strategies.

You analyze SPECIFIC game data and give GAME-SPECIFIC advice — never generic tips. Reference actual numbers from the game (EAPM, ELO, duration, civs, teams). Tell the player exactly what they should have done differently in THIS game.

Your style:
- Be direct, specific, and actionable
- Reference the player's ACTUAL civ bonuses and unique units by name
- Explain what counters the opponent had and what the player should have built
- Give concrete timing targets for their ELO bracket
- Max 300 words — dense, no fluff

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
    """Build deep context for a specific player including matchup data."""
    lines = []
    player = None
    for p in analysis.get("players", []):
        if player_name.lower() in p["name"].lower():
            player = p
            break
    if not player:
        return f"Player '{player_name}' not found in game data."

    # Player's own context
    lines.append(get_player_specific_context(
        player["civilization"], player.get("elo", 0),
        player.get("eapm", 0),
        analysis.get("duration_seconds", 0) / 60,
        not player.get("resigned", True)
    ))

    # Opponents
    player_team = player.get("team")
    opponents = [p for p in analysis["players"] if p.get("team") != player_team]
    opp_civs = [p["civilization"] for p in opponents]
    if opp_civs:
        lines.append("")
        lines.append(get_civ_matchup_context(player["civilization"], opp_civs[0] if len(opp_civs) == 1 else opp_civs[0]))
        # Add all opponent civs
        for opp in opponents:
            lines.append(f"  Opponent: {opp['name']} ({opp['civilization']}) ELO:{opp.get('elo',0)} EAPM:{opp.get('eapm',0)}")

    # Coaching report
    for r in coaching.get("player_reports", []):
        if player_name.lower() in r.get("name", "").lower():
            lines.append(f"\nGrade: {r.get('grade','?')}")
            for imp in r.get("improvements", []):
                lines.append(f"[{imp['severity'].upper()}] {imp['area']}: {imp['message']}")
            if r.get("civ_bonuses"):
                lines.append(f"Civ bonuses: {'; '.join(r['civ_bonuses'][:3])}")
            if r.get("unique_units"):
                lines.append(f"Unique units: {', '.join(r['unique_units'])}")
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
            user_prompt = (
                f"Game: {game_summary}\nAll players:\n{all_players}\n\n"
                f"=== DEEP ANALYSIS FOR: {target} ===\n{deep_context}\n\n"
                f"Give {target} specific coaching for THIS game. What should they have built "
                f"against these specific opponents? What were their civ's strengths they missed? "
                f"What units counter the opponents' likely composition? Give exact timing targets "
                f"for their ELO bracket."
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
