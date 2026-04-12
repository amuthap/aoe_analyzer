"""Auto-detection daemon — watches for AOE2:DE and active games.

Runs in background, detects:
1. AOE2:DE process starting/stopping
2. Game match starting (game_time > 0)
3. Players, civs, ages — all auto-discovered from memory
4. Game ending

Emits events that the dashboard consumes via polling.
"""

import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import psutil

from realtime_bot.memory import AOE2Memory, GameState, PlayerState, PROCESS_NAME, AGE_NAMES

log = logging.getLogger("aoe2bot.monitor")

# Civ IDs to names — import from parent project
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from civ_database import CIV_IDS


@dataclass
class DetectedPlayer:
    """A player detected in the current game."""
    player_id: int = 0
    name: str = ""
    civ_id: int = 0
    civ_name: str = ""
    is_ai: bool = False
    food: float = 0
    wood: float = 0
    stone: float = 0
    gold: float = 0
    population: int = 0
    pop_cap: int = 200
    civilian_pop: int = 0
    military_pop: int = 0
    current_age: int = 0
    age_name: str = "Dark Age"
    is_alive: bool = True


@dataclass
class MonitorState:
    """Current state of the monitor."""
    aoe2_running: bool = False
    aoe2_pid: int = 0
    in_game: bool = False
    game_time: str = "0:00"
    game_time_seconds: float = 0
    num_players: int = 0
    players: list = field(default_factory=list)
    bot_active: bool = False
    bot_ai_player: int = 0
    events: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "aoe2_running": self.aoe2_running,
            "aoe2_pid": self.aoe2_pid,
            "in_game": self.in_game,
            "game_time": self.game_time,
            "game_time_seconds": self.game_time_seconds,
            "num_players": self.num_players,
            "players": [_player_dict(p) for p in self.players],
            "bot_active": self.bot_active,
            "bot_ai_player": self.bot_ai_player,
            "events": self.events[-30:],
        }


def _player_dict(p: DetectedPlayer) -> dict:
    return {
        "player_id": p.player_id,
        "name": p.name,
        "civ_id": p.civ_id,
        "civ_name": p.civ_name,
        "is_ai": p.is_ai,
        "food": round(p.food),
        "wood": round(p.wood),
        "stone": round(p.stone),
        "gold": round(p.gold),
        "population": p.population,
        "pop_cap": p.pop_cap,
        "civilian_pop": p.civilian_pop,
        "military_pop": p.military_pop,
        "current_age": p.current_age,
        "age_name": p.age_name,
        "is_alive": p.is_alive,
    }


AGE_NAMES_MAP = {0: "Dark Age", 1: "Feudal Age", 2: "Castle Age", 3: "Imperial Age"}


class GameMonitor:
    """Background monitor that auto-detects AOE2:DE and game state."""

    def __init__(self):
        self.memory = AOE2Memory()
        self.state = MonitorState()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._callbacks = []  # [(event_name, callback)]

    def start(self):
        """Start background monitoring."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="game-monitor")
        self._thread.start()
        log.info("Game monitor started")

    def stop(self):
        """Stop monitoring."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self.memory.detach()
        log.info("Game monitor stopped")

    def get_state(self) -> MonitorState:
        """Thread-safe state access."""
        with self._lock:
            return self.state

    def on_event(self, callback):
        """Register a callback for monitor events."""
        self._callbacks.append(callback)

    def _emit(self, event: str, data: str = ""):
        """Emit an event to callbacks and event log."""
        entry = {"time": time.strftime("%H:%M:%S"), "event": event, "data": data}
        with self._lock:
            self.state.events.append(entry)
            if len(self.state.events) > 100:
                self.state.events = self.state.events[-100:]
        for cb in self._callbacks:
            try:
                cb(event, data)
            except Exception:
                pass

    def _monitor_loop(self):
        """Main monitoring loop."""
        was_running = False
        was_in_game = False

        while not self._stop.is_set():
            try:
                # Check if AOE2:DE is running
                aoe2_running, aoe2_pid = self._check_process()

                with self._lock:
                    self.state.aoe2_running = aoe2_running
                    self.state.aoe2_pid = aoe2_pid

                if aoe2_running and not was_running:
                    self._emit("process_started", f"AOE2:DE detected (PID: {aoe2_pid})")
                    self.memory.attach()
                elif not aoe2_running and was_running:
                    self._emit("process_stopped", "AOE2:DE closed")
                    self.memory.detach()
                    with self._lock:
                        self.state.in_game = False
                        self.state.players = []

                was_running = aoe2_running

                if not aoe2_running:
                    time.sleep(3)
                    continue

                # Ensure attached
                if not self.memory.is_attached:
                    self.memory.attach()
                    if not self.memory.is_attached:
                        time.sleep(3)
                        continue

                # Read game state
                game_state = self.memory.read_game_state()
                in_game = game_state.is_running and game_state.game_time_seconds > 2

                if in_game and not was_in_game:
                    self._emit("game_started", f"{len(game_state.players)} players detected")
                elif not in_game and was_in_game:
                    self._emit("game_ended", "Match ended")

                was_in_game = in_game

                # Update state
                with self._lock:
                    self.state.in_game = in_game
                    self.state.game_time = game_state.game_time_display
                    self.state.game_time_seconds = game_state.game_time_seconds
                    self.state.num_players = len(game_state.players)

                    if in_game:
                        self.state.players = [
                            self._build_player(p) for p in game_state.players
                        ]

                # Poll rate: faster during games
                time.sleep(3 if in_game else 5)

            except Exception as e:
                log.debug(f"Monitor loop error: {e}")
                time.sleep(5)

    def _check_process(self) -> tuple:
        """Check if AOE2:DE is running. Returns (running, pid)."""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and PROCESS_NAME.lower() in proc.info['name'].lower():
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False, 0

    def _build_player(self, ps: PlayerState) -> DetectedPlayer:
        """Convert memory PlayerState to DetectedPlayer with civ info."""
        civ_name = CIV_IDS.get(ps.civ_id if hasattr(ps, 'civ_id') else 0, "Unknown")
        return DetectedPlayer(
            player_id=ps.player_id,
            civ_id=getattr(ps, 'civ_id', 0),
            civ_name=civ_name,
            food=ps.food,
            wood=ps.wood,
            stone=ps.stone,
            gold=ps.gold,
            population=ps.population,
            pop_cap=ps.pop_cap,
            civilian_pop=ps.civilian_pop,
            military_pop=ps.military_pop,
            current_age=ps.current_age,
            age_name=AGE_NAMES_MAP.get(ps.current_age, "Unknown"),
            is_alive=ps.is_alive,
        )
