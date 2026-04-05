"""AOE2 AI Coach - LLM-powered analysis using Qwen via OpenAI-compatible API."""

import json
from openai import OpenAI

# LLM Config
LLM_BASE_URL = "http://llm.hyperbig.com:4000"
LLM_API_KEY = "sk-GtL5TQcP1PIN2xnPHBtDZg"
LLM_MODEL = "qwen/qwen3.6-plus"

client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
)

SYSTEM_PROMPT = """You are an expert Age of Empires 2: Definitive Edition coach. You analyze recorded game data and provide specific, actionable advice to help players improve.

Your coaching style:
- Be direct and specific, not generic
- Reference actual game data (EAPM, ELO, civ choice, game duration)
- Prioritize the 1-2 most impactful improvements
- Use concrete examples ("At your ELO, you should be hitting Feudal by 8:00")
- Reference pro players or educational content when relevant
- Be encouraging but honest
- Keep it concise - players want quick actionable tips, not essays

You know all 53 civilizations in AOE2:DE including recent DLCs (The Last Chieftains, Three Kingdoms). You understand the current meta, civ matchups, and common strategies at every ELO level."""


def build_game_context(analysis_dict: dict, coaching_dict: dict, focus_player: str = None) -> str:
    """Build a concise game context string for the LLM."""
    a = analysis_dict
    c = coaching_dict

    lines = [
        f"Game: {a.get('game_type', '?')} | Duration: {a.get('duration_display', '?')} | Map: {a.get('map_name', 'Unknown')}",
        "",
        "Players:",
    ]

    for p in a.get("players", []):
        marker = " <<<FOCUS" if focus_player and focus_player.lower() in p["name"].lower() else ""
        status = "WON" if not p.get("resigned", True) else "LOST (resigned)"
        lines.append(
            f"  [{p.get('team', '?')}] {p['name']} - {p['civilization']} "
            f"(ELO: {p.get('elo', 0)}, EAPM: {p.get('eapm', 0)}) - {status}{marker}"
        )

    # Add coaching report for the focus player
    if focus_player:
        for report in c.get("player_reports", []):
            if focus_player.lower() in report.get("name", "").lower():
                lines.append("")
                lines.append(f"Rule-based analysis for {report['name']}:")
                lines.append(f"  Grade: {report.get('grade', '?')}")
                lines.append(f"  Civ type: {report.get('civ_type', '?')}")
                if report.get("civ_bonuses"):
                    lines.append(f"  Civ bonuses: {'; '.join(report['civ_bonuses'][:3])}")
                if report.get("unique_units"):
                    lines.append(f"  Unique units: {', '.join(report['unique_units'])}")
                for imp in report.get("improvements", []):
                    lines.append(f"  [{imp['severity'].upper()}] {imp['area']}: {imp['message']}")
                for s in report.get("strengths", []):
                    lines.append(f"  [STRENGTH] {s}")
                break

    # Add chat context (if any interesting comms)
    if a.get("chats"):
        game_chats = [c for c in a["chats"] if c.get("time", "0:00") != "0:00"]
        if game_chats:
            lines.append("")
            lines.append("In-game chat (sample):")
            for chat in game_chats[:5]:
                lines.append(f"  [{chat['time']}] {chat['player']}: {chat['message']}")

    return "\n".join(lines)


def get_ai_analysis(analysis_dict: dict, coaching_dict: dict, focus_player: str = None) -> dict:
    """Get AI-powered analysis from Qwen LLM.

    Returns dict with:
        success: bool
        analysis: str (the AI coaching text)
        model: str (model used)
        tokens_used: int
        error: str (if failed)
    """
    try:
        game_context = build_game_context(analysis_dict, coaching_dict, focus_player)

        if focus_player:
            user_prompt = (
                f"Analyze this AOE2 game and give personalized coaching for {focus_player}. "
                f"Focus on their biggest weaknesses and give 3-4 specific tips to improve. "
                f"Mention their civ choice and whether it was good for this matchup.\n\n"
                f"{game_context}"
            )
        else:
            user_prompt = (
                f"Analyze this AOE2 game. Summarize what happened, who played well, "
                f"and give key takeaways for improvement.\n\n"
                f"{game_context}"
            )

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1000,
            temperature=0.7,
        )

        ai_text = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0

        return {
            "success": True,
            "analysis": ai_text,
            "model": LLM_MODEL,
            "tokens_used": tokens,
        }

    except Exception as e:
        return {
            "success": False,
            "analysis": "",
            "model": LLM_MODEL,
            "tokens_used": 0,
            "error": str(e),
        }
