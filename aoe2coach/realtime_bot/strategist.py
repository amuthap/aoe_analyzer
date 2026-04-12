"""LLM Strategist - the brain that coaches the Extreme AI in real-time.

Uses the existing knowledge base (unit counters, build orders, civ matchups)
and the LLM connection to make strategic decisions every ~2 minutes.

The LLM receives a compact game state summary and returns specific
strategic number adjustments to nudge the AI's behavior.
"""

import json
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

# Import from the parent project
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from knowledge_base import AOE2_KNOWLEDGE_BASE, get_civ_matchup_context
from civ_database import CIV_DATABASE
from realtime_bot.memory import GameState, PlayerState, STRATEGIC_NUMBERS

log = logging.getLogger("aoe2bot.strategist")

# LLM Config (same as llm_coach.py)
LLM_BASE_URL = "http://llm.hyperbig.com:4000"
LLM_API_KEY = "sk-GtL5TQcP1PIN2xnPHBtDZg"
LLM_MODEL = "qwen/qwen3.6-plus"

AGE_NAMES = {0: "Dark Age", 1: "Feudal Age", 2: "Castle Age", 3: "Imperial Age"}


@dataclass
class MatchContext:
    """Pre-game context about the match."""
    ai_player_id: int = 2          # Which player ID is our AI (1-based)
    ai_civ: str = ""               # AI's civilization name
    opponent_civs: list = field(default_factory=list)  # Opponent civ names
    map_name: str = "Arabia"
    game_type: str = "1v1"


@dataclass
class StrategicDecision:
    """A decision from the LLM with strategic number changes."""
    reasoning: str = ""
    changes: dict = field(default_factory=dict)  # {sn_name: value}
    priority: str = "normal"       # "urgent" for immediate threats
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


STRATEGIST_SYSTEM_PROMPT = f"""You are an expert AOE2 AI coach embedded in a real-time game. You control an Extreme AI by adjusting its strategic numbers (sn- values).

You receive game state snapshots every ~2 minutes. Your job: analyze the situation and return SPECIFIC strategic number adjustments to improve the AI's play.

AVAILABLE STRATEGIC NUMBERS YOU CAN ADJUST:

Economy (percentages must sum to ~100):
  sn-food-gatherer-percentage (1): % of villagers on food [0-100]
  sn-wood-gatherer-percentage (2): % of villagers on wood [0-100]
  sn-stone-gatherer-percentage (3): % of villagers on stone [0-100]
  sn-gold-gatherer-percentage (4): % of villagers on gold [0-100]

Military:
  sn-percent-attack-soldiers (33): % of military to send on attacks [0-100]
  sn-minimum-attack-group-size (35): min units before attacking [1-40]
  sn-maximum-attack-group-size (36): max attack group [5-60]
  sn-number-attack-groups (38): how many attack groups [1-5]
  sn-minimum-defend-group-size (39): min units for defense [1-20]
  sn-maximum-defend-group-size (40): max defend group [5-40]
  sn-number-defend-groups (41): defense groups [1-3]
  sn-percent-enemy-sighted-response (48): % troops responding to threats [0-100]

Exploration:
  sn-percent-civilian-explorers (5): % villagers scouting [0-20]

Trade:
  sn-minimum-number-trade-carts (165): min trade carts [0-30]
  sn-maximum-number-trade-carts (166): max trade carts [0-60]

RULES:
- Return a JSON object with "reasoning" (1-2 sentences) and "changes" (dict of sn-name: value)
- Only change what NEEDS changing based on the current situation
- Economy percentages should roughly sum to 95-100
- Be aggressive: Extreme AI already plays well, your job is to make it SMARTER
- Key scenarios to react to:
  * Enemy going knights → increase food+gold, decrease wood
  * Enemy going archers → increase food+gold for skirms/knights
  * Late game → set up trade (sn-minimum-number-trade-carts: 15+)
  * Being raided → increase defend group sizes, lower attack aggression
  * Winning → push harder (increase attack group size, attack soldiers %)
  * Floating resources → you have too many gatherers for that resource, rebalance

OUTPUT FORMAT (strict JSON, no markdown):
{{"reasoning": "Enemy is in Castle Age with knights. Need more pikes and halbs. Shift eco to food-heavy for pike production.", "changes": {{"sn-food-gatherer-percentage": 50, "sn-wood-gatherer-percentage": 20, "sn-gold-gatherer-percentage": 20, "sn-stone-gatherer-percentage": 10, "sn-minimum-attack-group-size": 15}}}}

{AOE2_KNOWLEDGE_BASE}
"""


class Strategist:
    """LLM-powered real-time strategist for an AOE2 AI player.

    Keeps track of game state history and consults the LLM periodically
    to generate strategic number adjustments.
    """

    def __init__(self, match_context: MatchContext):
        self.ctx = match_context
        self.client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        self.decision_history: list[StrategicDecision] = []
        self.state_history: list[dict] = []  # Compact state snapshots
        self._last_llm_call = 0.0
        self._min_interval = 90  # Minimum seconds between LLM calls
        self._call_count = 0

        # Build civ matchup context once
        self._matchup_context = ""
        if self.ctx.ai_civ and self.ctx.opponent_civs:
            for opp_civ in self.ctx.opponent_civs:
                self._matchup_context += get_civ_matchup_context(
                    self.ctx.ai_civ, opp_civ
                ) + "\n"

        log.info(f"Strategist initialized: {self.ctx.ai_civ} vs {self.ctx.opponent_civs} on {self.ctx.map_name}")

    def should_consult_llm(self, game_state: GameState) -> bool:
        """Decide if we should consult the LLM now.

        Returns True when:
        - Enough time has passed since last call (~2 min)
        - A significant game event happened (age-up, large resource float, being attacked)
        """
        now = time.time()
        elapsed = now - self._last_llm_call

        # Always wait at least the minimum interval
        if elapsed < self._min_interval:
            return False

        # Normal cadence: every 2 minutes
        if elapsed >= 120:
            return True

        # Urgent: detect big resource float (>1000 of anything = waste)
        ai_player = self._get_ai_player(game_state)
        if ai_player:
            if (ai_player.food > 1500 or ai_player.wood > 1500 or
                    ai_player.gold > 1500 or ai_player.stone > 1000):
                log.info("Urgent: resource float detected, consulting LLM")
                return True

        return False

    def analyze_and_decide(self, game_state: GameState) -> Optional[StrategicDecision]:
        """Main entry point: analyze game state and return strategic changes.

        Called by the bot loop. Returns None if no LLM call needed,
        or a StrategicDecision with the changes to apply.
        """
        if not game_state.is_running:
            return None

        if not self.should_consult_llm(game_state):
            return None

        # Build the state summary for the LLM
        state_summary = self._build_state_summary(game_state)
        self.state_history.append({"time": game_state.game_time_display, "summary": state_summary})

        # Call the LLM
        decision = self._call_llm(state_summary)
        if decision:
            self.decision_history.append(decision)
            self._last_llm_call = time.time()
            self._call_count += 1
            log.info(f"LLM decision #{self._call_count}: {decision.reasoning}")
            log.info(f"Changes: {decision.changes}")

        return decision

    def get_initial_strategy(self) -> StrategicDecision:
        """Generate initial strategy before the game starts.

        Uses civ matchup data to set optimal starting eco ratios and
        aggression levels.
        """
        prompt = (
            f"Game is starting. Set initial strategic numbers.\n"
            f"AI plays: {self.ctx.ai_civ}\n"
            f"Opponents: {', '.join(self.ctx.opponent_civs)}\n"
            f"Map: {self.ctx.map_name}\n"
            f"Game type: {self.ctx.game_type}\n\n"
            f"{self._matchup_context}\n\n"
            f"Set optimal Dark Age economy split and initial military stance. "
            f"On open maps (Arabia), be more aggressive. On closed maps (Arena, BF), boom."
        )

        decision = self._call_llm(prompt)
        if decision:
            self._last_llm_call = time.time()
            self.decision_history.append(decision)

        return decision or StrategicDecision(
            reasoning="Default opening: standard eco split",
            changes={
                "sn-food-gatherer-percentage": 55,
                "sn-wood-gatherer-percentage": 25,
                "sn-gold-gatherer-percentage": 15,
                "sn-stone-gatherer-percentage": 5,
                "sn-minimum-attack-group-size": 8,
                "sn-percent-attack-soldiers": 50,
            }
        )

    def _get_ai_player(self, game_state: GameState) -> Optional[PlayerState]:
        """Find our AI player in the game state."""
        for p in game_state.players:
            if p.player_id == self.ctx.ai_player_id:
                return p
        return None

    def _build_state_summary(self, game_state: GameState) -> str:
        """Build a compact game state summary for the LLM."""
        lines = [f"GAME TIME: {game_state.game_time_display}"]

        ai_player = self._get_ai_player(game_state)
        if ai_player:
            age = AGE_NAMES.get(ai_player.current_age, "Unknown")
            lines.append(
                f"OUR AI ({self.ctx.ai_civ}): {age} | "
                f"Pop {ai_player.population}/{ai_player.pop_cap} "
                f"(Civ:{ai_player.civilian_pop} Mil:{ai_player.military_pop}) | "
                f"Food:{int(ai_player.food)} Wood:{int(ai_player.wood)} "
                f"Gold:{int(ai_player.gold)} Stone:{int(ai_player.stone)}"
            )

            # Flag resource floats
            floats = []
            if ai_player.food > 1000: floats.append(f"FLOATING {int(ai_player.food)} food!")
            if ai_player.wood > 1000: floats.append(f"FLOATING {int(ai_player.wood)} wood!")
            if ai_player.gold > 1000: floats.append(f"FLOATING {int(ai_player.gold)} gold!")
            if floats:
                lines.append("WARNING: " + " ".join(floats))

        # Opponents
        for p in game_state.players:
            if p.player_id != self.ctx.ai_player_id and p.is_alive:
                opp_idx = p.player_id - 1
                opp_civ = self.ctx.opponent_civs[opp_idx] if opp_idx < len(self.ctx.opponent_civs) else "Unknown"
                age = AGE_NAMES.get(p.current_age, "?")
                lines.append(
                    f"OPPONENT P{p.player_id} ({opp_civ}): {age} | "
                    f"Pop {p.population}/{p.pop_cap} | "
                    f"Food:{int(p.food)} Wood:{int(p.wood)} "
                    f"Gold:{int(p.gold)} Stone:{int(p.stone)}"
                )

        # Recent decision history (last 2)
        if self.decision_history:
            lines.append("\nPREVIOUS DECISIONS:")
            for d in self.decision_history[-2:]:
                lines.append(f"  - {d.reasoning}")

        return "\n".join(lines)

    def _call_llm(self, state_or_prompt: str) -> Optional[StrategicDecision]:
        """Call the LLM and parse its response into a StrategicDecision."""
        try:
            response = self.client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": STRATEGIST_SYSTEM_PROMPT},
                    {"role": "user", "content": state_or_prompt},
                ],
                max_tokens=400,
                temperature=0.3,  # Lower temp for more consistent strategic output
            )

            raw = response.choices[0].message.content.strip()
            log.debug(f"LLM raw response: {raw}")

            # Parse JSON response — handle markdown code blocks
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                raw = raw.rsplit("```", 1)[0]
            raw = raw.strip()

            # Handle /think tags from Qwen
            if "</think>" in raw:
                raw = raw.split("</think>")[-1].strip()

            data = json.loads(raw)

            # Validate changes
            changes = {}
            for key, val in data.get("changes", {}).items():
                if key in STRATEGIC_NUMBERS:
                    changes[key] = int(val)
                else:
                    log.warning(f"LLM suggested unknown SN: {key}")

            return StrategicDecision(
                reasoning=data.get("reasoning", "No reasoning provided"),
                changes=changes,
            )

        except json.JSONDecodeError as e:
            log.error(f"LLM returned non-JSON: {e}")
            return None
        except Exception as e:
            log.error(f"LLM call failed: {e}")
            return None

    def get_status(self) -> dict:
        """Return current strategist status for the web UI."""
        return {
            "ai_civ": self.ctx.ai_civ,
            "opponent_civs": self.ctx.opponent_civs,
            "map": self.ctx.map_name,
            "llm_calls": self._call_count,
            "last_decision": self.decision_history[-1].reasoning if self.decision_history else "No decisions yet",
            "last_changes": self.decision_history[-1].changes if self.decision_history else {},
            "history_length": len(self.decision_history),
        }
