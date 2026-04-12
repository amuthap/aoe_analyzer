"""AOE2 Real-time AI Bot - Main loop.

Attaches to AOE2:DE, reads game state, consults LLM when needed,
and writes strategic number adjustments to enhance the Extreme AI.

Usage:
    python -m realtime_bot.bot --ai-player 2 --ai-civ Franks --opp-civ Britons --map Arabia

Or via the web UI at http://localhost:8080
"""

import argparse
import json
import logging
import sys
import time
import threading
from dataclasses import asdict
from typing import Optional

from realtime_bot.memory import AOE2Memory, GameState, STRATEGIC_NUMBERS
from realtime_bot.strategist import Strategist, MatchContext, StrategicDecision

log = logging.getLogger("aoe2bot")

# Bot states
STATE_IDLE = "idle"
STATE_WAITING = "waiting_for_game"
STATE_RUNNING = "running"
STATE_PAUSED = "paused"
STATE_STOPPED = "stopped"
STATE_ERROR = "error"


class AOE2Bot:
    """Main bot that connects memory reading, LLM strategy, and game control.

    Lifecycle:
        1. start() → attaches to AOE2:DE process
        2. Waits for a game to begin (detects game_time > 0)
        3. Sends initial strategy from LLM
        4. Main loop: read state every 5s, consult LLM every ~2min
        5. Applies strategic number changes
        6. Stops when game ends or stop() is called
    """

    def __init__(self, match_context: MatchContext):
        self.ctx = match_context
        self.memory = AOE2Memory()
        self.strategist: Optional[Strategist] = None
        self.state = STATE_IDLE
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Start unpaused

        # Stats
        self.stats = {
            "game_time": "0:00",
            "state_reads": 0,
            "llm_calls": 0,
            "sn_writes": 0,
            "errors": 0,
            "last_error": "",
            "decisions": [],
        }

        # Event log for the web UI
        self.event_log: list[dict] = []

    def start(self):
        """Start the bot in a background thread."""
        if self.state == STATE_RUNNING:
            log.warning("Bot already running")
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="aoe2bot")
        self._thread.start()
        self._log_event("Bot started", "info")

    def stop(self):
        """Stop the bot gracefully."""
        self._stop_event.set()
        self._pause_event.set()  # Unpause if paused so thread can exit
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10)
        self.memory.detach()
        self.state = STATE_STOPPED
        self._log_event("Bot stopped", "info")

    def pause(self):
        """Pause the bot (stops LLM calls but keeps reading state)."""
        self._pause_event.clear()
        self.state = STATE_PAUSED
        self._log_event("Bot paused", "info")

    def resume(self):
        """Resume the bot."""
        self._pause_event.set()
        self.state = STATE_RUNNING
        self._log_event("Bot resumed", "info")

    def _run_loop(self):
        """Main bot loop. Runs in a background thread."""
        self.state = STATE_WAITING

        # Step 1: Attach to AOE2:DE
        self._log_event("Looking for AOE2:DE process...", "info")
        while not self._stop_event.is_set():
            if self.memory.attach():
                self._log_event("Attached to AOE2:DE!", "success")
                break
            time.sleep(3)

        if self._stop_event.is_set():
            return

        # Step 2: Initialize strategist
        self.strategist = Strategist(self.ctx)

        # Step 3: Wait for game to start
        self._log_event("Waiting for game to start...", "info")
        game_started = False
        while not self._stop_event.is_set():
            state = self.memory.read_game_state()
            if state.is_running and state.game_time_seconds > 5:
                game_started = True
                self._log_event(
                    f"Game detected! {len(state.players)} players, time: {state.game_time_display}",
                    "success"
                )
                break
            time.sleep(2)

        if not game_started:
            return

        # Step 4: Apply initial strategy
        self._log_event("Getting initial strategy from LLM...", "info")
        try:
            initial = self.strategist.get_initial_strategy()
            if initial and initial.changes:
                wrote = self.memory.write_strategic_numbers(
                    self.ctx.ai_player_id, initial.changes
                )
                self.stats["sn_writes"] += wrote
                self.stats["llm_calls"] += 1
                self._log_event(
                    f"Initial strategy applied: {initial.reasoning} ({wrote} SNs written)",
                    "decision"
                )
                self.stats["decisions"].append({
                    "time": "0:00",
                    "reasoning": initial.reasoning,
                    "changes": initial.changes,
                })
        except Exception as e:
            self._log_event(f"Initial strategy failed: {e}", "error")

        # Step 5: Main loop
        self.state = STATE_RUNNING
        self._log_event("Bot is LIVE - monitoring game...", "success")

        read_interval = 5  # Read state every 5 seconds
        last_state: Optional[GameState] = None

        while not self._stop_event.is_set():
            # Wait if paused
            self._pause_event.wait(timeout=1)
            if self._stop_event.is_set():
                break

            try:
                # Check process is still alive
                if not self.memory.is_attached:
                    self._log_event("Lost connection to AOE2:DE", "error")
                    self.state = STATE_ERROR
                    # Try to reattach
                    time.sleep(5)
                    if self.memory.attach():
                        self._log_event("Reattached to AOE2:DE", "success")
                        self.state = STATE_RUNNING
                    else:
                        break

                # Read game state
                game_state = self.memory.read_game_state()
                self.stats["state_reads"] += 1

                if not game_state.is_running:
                    self._log_event("Game ended or not in match", "info")
                    # Wait and check again (might be loading screen)
                    time.sleep(10)
                    game_state = self.memory.read_game_state()
                    if not game_state.is_running:
                        self._log_event("Game over. Bot stopping.", "info")
                        break

                self.stats["game_time"] = game_state.game_time_display
                last_state = game_state

                # Log periodic status
                if self.stats["state_reads"] % 12 == 0:  # Every ~60 seconds
                    ai = None
                    for p in game_state.players:
                        if p.player_id == self.ctx.ai_player_id:
                            ai = p
                            break
                    if ai:
                        self._log_event(
                            f"[{game_state.game_time_display}] AI: Pop {ai.population} "
                            f"| F:{int(ai.food)} W:{int(ai.wood)} G:{int(ai.gold)} S:{int(ai.stone)}",
                            "status"
                        )

                # Consult LLM if needed
                decision = self.strategist.analyze_and_decide(game_state)
                if decision and decision.changes:
                    wrote = self.memory.write_strategic_numbers(
                        self.ctx.ai_player_id, decision.changes
                    )
                    self.stats["sn_writes"] += wrote
                    self.stats["llm_calls"] += 1
                    self._log_event(
                        f"[{game_state.game_time_display}] LLM: {decision.reasoning} "
                        f"({wrote} SNs adjusted)",
                        "decision"
                    )
                    self.stats["decisions"].append({
                        "time": game_state.game_time_display,
                        "reasoning": decision.reasoning,
                        "changes": decision.changes,
                    })

            except Exception as e:
                self.stats["errors"] += 1
                self.stats["last_error"] = str(e)
                log.error(f"Bot loop error: {e}", exc_info=True)
                self._log_event(f"Error: {e}", "error")

            time.sleep(read_interval)

        # Cleanup
        self.memory.detach()
        self.state = STATE_STOPPED
        self._log_event("Bot stopped", "info")

    def _log_event(self, message: str, level: str = "info"):
        """Add an event to the log (for web UI display)."""
        event = {
            "time": time.strftime("%H:%M:%S"),
            "message": message,
            "level": level,
        }
        self.event_log.append(event)
        # Keep last 100 events
        if len(self.event_log) > 100:
            self.event_log = self.event_log[-100:]

        # Also log normally
        if level == "error":
            log.error(message)
        else:
            log.info(message)

    def get_status(self) -> dict:
        """Get full bot status for the web UI."""
        status = {
            "state": self.state,
            "stats": self.stats,
            "events": self.event_log[-20:],  # Last 20 events
            "match": {
                "ai_player_id": self.ctx.ai_player_id,
                "ai_civ": self.ctx.ai_civ,
                "opponent_civs": self.ctx.opponent_civs,
                "map": self.ctx.map_name,
            },
        }
        if self.strategist:
            status["strategist"] = self.strategist.get_status()
        return status


# --- Singleton bot instance for the web app ---
_bot_instance: Optional[AOE2Bot] = None


def get_bot() -> Optional[AOE2Bot]:
    return _bot_instance


def start_bot(ai_player_id: int, ai_civ: str, opponent_civs: list,
              map_name: str = "Arabia", game_type: str = "1v1") -> AOE2Bot:
    """Start a new bot instance."""
    global _bot_instance

    if _bot_instance and _bot_instance.state == STATE_RUNNING:
        _bot_instance.stop()

    ctx = MatchContext(
        ai_player_id=ai_player_id,
        ai_civ=ai_civ,
        opponent_civs=opponent_civs,
        map_name=map_name,
        game_type=game_type,
    )

    _bot_instance = AOE2Bot(ctx)
    _bot_instance.start()
    return _bot_instance


def stop_bot():
    """Stop the current bot instance."""
    global _bot_instance
    if _bot_instance:
        _bot_instance.stop()
        _bot_instance = None


# --- CLI entry point ---
def main():
    parser = argparse.ArgumentParser(
        description="AOE2 Real-time AI Bot - LLM-enhanced Extreme AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m realtime_bot.bot --ai-player 2 --ai-civ Franks --opp-civ Britons --map Arabia
  python -m realtime_bot.bot --ai-player 2 --ai-civ Mongols --opp-civ Goths --map "Black Forest"
  python -m realtime_bot.bot --scan  (diagnostic: scan memory offsets)

How to use:
  1. Start AOE2:DE
  2. Set up a skirmish game with Extreme AI
  3. Start this bot (it auto-attaches to the game)
  4. The bot will enhance the AI's strategy in real-time
  5. Press Ctrl+C to stop
        """
    )
    parser.add_argument("--ai-player", type=int, default=2,
                        help="Player ID of the AI to enhance (default: 2)")
    parser.add_argument("--ai-civ", type=str, default="Franks",
                        help="AI's civilization name")
    parser.add_argument("--opp-civ", type=str, nargs="+", default=["Britons"],
                        help="Opponent civilization(s)")
    parser.add_argument("--map", type=str, default="Arabia",
                        help="Map name")
    parser.add_argument("--game-type", type=str, default="1v1",
                        help="Game type (1v1, 2v2, etc.)")
    parser.add_argument("--scan", action="store_true",
                        help="Diagnostic: scan for memory offsets and exit")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Diagnostic mode
    if args.scan:
        print("Scanning AOE2:DE memory structure...")
        mem = AOE2Memory()
        if not mem.attach():
            print("ERROR: Could not attach to AOE2:DE. Is it running?")
            sys.exit(1)
        info = mem.scan_for_offsets()
        print(json.dumps(info, indent=2))
        mem.detach()
        sys.exit(0)

    # Normal mode
    print(f"""
    ╔══════════════════════════════════════════════╗
    ║   AOE2 Real-time AI Bot                      ║
    ║   LLM-Enhanced Extreme AI                    ║
    ╠══════════════════════════════════════════════╣
    ║   AI Player: {args.ai_player} ({args.ai_civ})
    ║   Opponents: {', '.join(args.opp_civ)}
    ║   Map:       {args.map}
    ║   Type:      {args.game_type}
    ╠══════════════════════════════════════════════╣
    ║   Press Ctrl+C to stop                       ║
    ╚══════════════════════════════════════════════╝
    """)

    bot = start_bot(
        ai_player_id=args.ai_player,
        ai_civ=args.ai_civ,
        opponent_civs=args.opp_civ,
        map_name=args.map,
        game_type=args.game_type,
    )

    try:
        while bot.state not in (STATE_STOPPED, STATE_ERROR):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        stop_bot()
        print("Bot stopped.")


if __name__ == "__main__":
    main()
