"""AOE2:DE memory reader/writer using pymem.

Reads game state and writes strategic number adjustments to the AI player's memory.
Strategic numbers (sn-) are the knobs that control AI behavior: gather ratios,
attack timing, army size, retreat conditions, etc.

Memory layout changes with patches — offsets are found via signature scanning.
"""

import time
import ctypes
import struct
import logging
from dataclasses import dataclass, field
from typing import Optional

import pymem
import pymem.process
import pymem.pattern

log = logging.getLogger("aoe2bot.memory")

# --- AOE2:DE Process ---
PROCESS_NAME = "AoE2DE_s.exe"

# --- Signature patterns for key structures ---
# These patterns are stable across many DE patches because they match
# code/data patterns rather than absolute addresses.
# Format: (pattern_bytes, offset_from_match, description)

# Resource array signature: the 4 resource floats (food/wood/stone/gold)
# are stored contiguously per player. We find the base game pointer first.
# Pattern for the main game object pointer (stable across DE patches)
GAME_OBJ_PATTERNS = [
    # DE 2024+ pattern: mov [reg], game_obj followed by resource access
    b"\x48\x8B\x05....\x48\x85\xC0\x74.\x48\x8B\x40\x08",
    # Fallback: older DE pattern
    b"\x48\x8B\x0D....\x48\x85\xC9\x0F\x84",
]

# Strategic number array: 512 int32 values per AI player
# sn-index -> 4-byte int at base + (index * 4)
SN_COUNT = 512


@dataclass
class PlayerState:
    """Snapshot of a player's game state."""
    player_id: int = 0
    food: float = 0.0
    wood: float = 0.0
    stone: float = 0.0
    gold: float = 0.0
    population: int = 0
    pop_cap: int = 200
    civilian_pop: int = 0
    military_pop: int = 0
    current_age: int = 0  # 0=Dark, 1=Feudal, 2=Castle, 3=Imperial
    is_alive: bool = True


@dataclass
class GameState:
    """Full snapshot of the current game."""
    game_time_seconds: float = 0.0
    game_speed: float = 1.5  # Normal=1.5, Fast=2.0
    map_id: int = 0
    num_players: int = 0
    players: list = field(default_factory=list)
    is_running: bool = False

    @property
    def game_time_display(self) -> str:
        m = int(self.game_time_seconds) // 60
        s = int(self.game_time_seconds) % 60
        return f"{m}:{s:02d}"


# --- Key Strategic Numbers ---
# These are the sn- indices the LLM can adjust to influence the AI
STRATEGIC_NUMBERS = {
    # Economy
    "sn-food-gatherer-percentage": 1,
    "sn-wood-gatherer-percentage": 2,
    "sn-stone-gatherer-percentage": 3,
    "sn-gold-gatherer-percentage": 4,
    "sn-percent-civilian-explorers": 5,
    "sn-percent-civilian-builders": 6,
    "sn-percent-civilian-gatherers": 7,
    "sn-cap-civilian-explorers": 8,
    "sn-cap-civilian-builders": 9,
    "sn-cap-civilian-gatherers": 10,
    "sn-minimum-civilian-explorers": 11,
    # Military
    "sn-percent-attack-soldiers": 33,
    "sn-percent-attack-boats": 34,
    "sn-minimum-attack-group-size": 35,
    "sn-maximum-attack-group-size": 36,
    "sn-number-attack-groups": 38,
    "sn-minimum-defend-group-size": 39,
    "sn-maximum-defend-group-size": 40,
    "sn-number-defend-groups": 41,
    "sn-attack-group-size-randomness": 42,
    "sn-percent-enemy-sighted-response": 48,
    "sn-enemy-sighted-response-distance": 49,
    # Attack control
    "sn-group-commander-selection-method": 44,
    "sn-consecutive-idle-unit-limit": 45,
    "sn-task-ungrouped-soldiers": 46,
    "sn-number-explore-groups": 47,
    # Retreat/defense
    "sn-hits-before-alliance-change": 54,
    "sn-attack-diplomacy-impact": 55,
    "sn-percent-half-exploration": 56,
    "sn-zero-priority-distance": 57,
    # Town management
    "sn-town-center-placement": 84,
    "sn-minimum-town-size": 90,
    "sn-maximum-town-size": 91,
    # Trade
    "sn-minimum-number-trade-carts": 165,
    "sn-maximum-number-trade-carts": 166,
    # Misc
    "sn-do-not-scale-for-difficulty-level": 174,
    "sn-number-build-attempts-before-skip": 203,
    "sn-max-skips-per-attempt": 204,
}

# Reverse lookup
SN_INDEX_TO_NAME = {v: k for k, v in STRATEGIC_NUMBERS.items()}


class AOE2MemoryError(Exception):
    """Raised when memory operations fail."""
    pass


class AOE2Memory:
    """Reads/writes AOE2:DE game memory.

    Architecture:
        Game Object → Players Array → Player[n] → {Resources, AI_Module}
        AI_Module → Strategic Numbers Array (512 x int32)

    This class handles:
        1. Attaching to the AOE2:DE process
        2. Finding the game object via signature scanning
        3. Reading player state (resources, age, population)
        4. Reading/writing strategic numbers for AI players
    """

    def __init__(self):
        self.pm: Optional[pymem.Pymem] = None
        self.base_address: int = 0
        self.game_obj_ptr: int = 0
        self._attached = False
        self._last_scan_time = 0
        self._scan_cache = {}

    def attach(self) -> bool:
        """Attach to the AOE2:DE process."""
        try:
            self.pm = pymem.Pymem(PROCESS_NAME)
            self.base_address = self.pm.base_address
            log.info(f"Attached to {PROCESS_NAME} (PID: {self.pm.process_id}, base: 0x{self.base_address:X})")
            self._attached = True
            return True
        except pymem.exception.ProcessNotFound:
            log.warning(f"{PROCESS_NAME} not found. Is AOE2:DE running?")
            self._attached = False
            return False
        except pymem.exception.CouldNotOpenProcess:
            log.error(f"Could not open {PROCESS_NAME}. Try running as Administrator.")
            self._attached = False
            return False
        except Exception as e:
            log.error(f"Failed to attach: {e}")
            self._attached = False
            return False

    def detach(self):
        """Detach from the process."""
        if self.pm:
            try:
                self.pm.close_process()
            except Exception:
                pass
        self.pm = None
        self._attached = False
        self._scan_cache.clear()
        log.info("Detached from AOE2:DE")

    @property
    def is_attached(self) -> bool:
        if not self._attached or not self.pm:
            return False
        try:
            # Quick check if process is still alive
            self.pm.read_int(self.base_address)
            return True
        except Exception:
            self._attached = False
            return False

    def _find_game_object(self) -> int:
        """Find the main game object pointer via signature scanning."""
        if not self.pm:
            raise AOE2MemoryError("Not attached to process")

        # Get the main module
        module = pymem.process.module_from_name(
            self.pm.process_handle, PROCESS_NAME
        )
        if not module:
            raise AOE2MemoryError("Could not find main module")

        module_base = module.lpBaseOfDll
        module_size = module.SizeOfImage

        # Try each signature pattern
        for pattern in GAME_OBJ_PATTERNS:
            try:
                addr = pymem.pattern.pattern_scan_module(
                    self.pm.process_handle, module, pattern
                )
                if addr:
                    # The pattern contains a RIP-relative offset
                    # Read the 4-byte relative offset at position 3
                    rip_offset = self.pm.read_int(addr + 3)
                    # Calculate absolute address: addr + 7 (instruction length) + rip_offset
                    abs_addr = addr + 7 + rip_offset
                    # Read the pointer at that address
                    game_ptr = self.pm.read_longlong(abs_addr)
                    if game_ptr and game_ptr > 0x10000:
                        log.info(f"Found game object at 0x{game_ptr:X}")
                        self.game_obj_ptr = game_ptr
                        return game_ptr
            except Exception as e:
                log.debug(f"Pattern scan attempt failed: {e}")
                continue

        raise AOE2MemoryError(
            "Could not find game object. The game may not be in a match, "
            "or memory signatures need updating for this game version."
        )

    def _read_ptr(self, address: int) -> int:
        """Read a 64-bit pointer."""
        return self.pm.read_longlong(address)

    def _read_int(self, address: int) -> int:
        """Read a 32-bit integer."""
        return self.pm.read_int(address)

    def _read_float(self, address: int) -> float:
        """Read a 32-bit float."""
        return self.pm.read_float(address)

    def _write_int(self, address: int, value: int):
        """Write a 32-bit integer."""
        self.pm.write_int(address, value)

    def read_game_state(self) -> GameState:
        """Read the full current game state.

        Returns a GameState with player resources, ages, population, etc.
        This is the main read method called every few seconds by the bot loop.
        """
        state = GameState()

        if not self.is_attached:
            return state

        try:
            if not self.game_obj_ptr:
                self._find_game_object()

            # Read game time (milliseconds as float at game_obj + 0x8)
            game_world = self._read_ptr(self.game_obj_ptr + 0x8)
            if game_world:
                time_ms = self._read_float(game_world + 0x8)
                state.game_time_seconds = time_ms / 1000.0
                state.is_running = time_ms > 0

                # Read number of players
                state.num_players = self._read_int(game_world + 0xEC)

                # Read each player
                players_array_ptr = self._read_ptr(game_world + 0xE8)
                if players_array_ptr:
                    for i in range(1, min(state.num_players + 1, 9)):  # Skip Gaia (0)
                        try:
                            player = self._read_player(players_array_ptr, i)
                            state.players.append(player)
                        except Exception as e:
                            log.debug(f"Failed to read player {i}: {e}")

        except AOE2MemoryError as e:
            log.warning(f"Game state read failed: {e}")
            state.is_running = False
        except Exception as e:
            log.debug(f"Memory read error: {e}")
            state.is_running = False

        return state

    def _read_player(self, players_array_ptr: int, player_id: int) -> PlayerState:
        """Read a single player's state from memory."""
        ps = PlayerState(player_id=player_id)

        # Each player pointer is at array_base + (player_id * 8)
        player_ptr = self._read_ptr(players_array_ptr + player_id * 8)
        if not player_ptr:
            return ps

        # Resources are stored as floats in the resource array
        # Resource struct is at player + 0x38, then resources at +0x0 offset
        resource_ptr = self._read_ptr(player_ptr + 0x38)
        if resource_ptr:
            # Standard resource order: food=0, wood=1, stone=2, gold=3
            resource_array = self._read_ptr(resource_ptr + 0x8)
            if resource_array:
                ps.food = max(0, self._read_float(resource_array + 0 * 4))
                ps.wood = max(0, self._read_float(resource_array + 1 * 4))
                ps.stone = max(0, self._read_float(resource_array + 2 * 4))
                ps.gold = max(0, self._read_float(resource_array + 3 * 4))
                # Population is resource index 4, pop cap is index 5
                ps.population = int(self._read_float(resource_array + 4 * 4))
                ps.pop_cap = int(self._read_float(resource_array + 5 * 4))
                # Military pop at index 41, civilian at index 40
                ps.civilian_pop = int(self._read_float(resource_array + 40 * 4))
                ps.military_pop = int(self._read_float(resource_array + 41 * 4))
                # Current age at resource index 6 (0=Dark, 1=Feudal, 2=Castle, 3=Imp)
                ps.current_age = int(self._read_float(resource_array + 6 * 4))

        ps.is_alive = ps.population > 0

        return ps

    def read_strategic_number(self, player_id: int, sn_index: int) -> Optional[int]:
        """Read a strategic number for an AI player.

        Args:
            player_id: 1-based player ID
            sn_index: Strategic number index (0-511)

        Returns:
            The strategic number value, or None if read failed.
        """
        if not self.is_attached:
            return None

        try:
            sn_base = self._get_sn_base(player_id)
            if sn_base:
                return self._read_int(sn_base + sn_index * 4)
        except Exception as e:
            log.debug(f"Failed to read SN[{sn_index}] for player {player_id}: {e}")
        return None

    def write_strategic_number(self, player_id: int, sn_index: int, value: int) -> bool:
        """Write a strategic number for an AI player.

        This is how the LLM 'coaches' the AI — by tweaking these values:
        - Gather percentages (food/wood/gold/stone allocation)
        - Attack group sizes (when to push, how many units)
        - Defense parameters (retreat thresholds)
        - Exploration settings

        Args:
            player_id: 1-based player ID
            sn_index: Strategic number index (0-511)
            value: New int32 value

        Returns:
            True if write succeeded.
        """
        if not self.is_attached:
            return False

        try:
            sn_base = self._get_sn_base(player_id)
            if sn_base:
                self._write_int(sn_base + sn_index * 4, value)
                name = SN_INDEX_TO_NAME.get(sn_index, f"sn-{sn_index}")
                log.info(f"Set {name} = {value} for player {player_id}")
                return True
        except Exception as e:
            log.error(f"Failed to write SN[{sn_index}] for player {player_id}: {e}")
        return False

    def write_strategic_numbers(self, player_id: int, changes: dict) -> int:
        """Write multiple strategic number changes at once.

        Args:
            player_id: 1-based player ID
            changes: Dict of {sn_name_or_index: value}

        Returns:
            Number of successful writes.
        """
        count = 0
        for key, value in changes.items():
            if isinstance(key, str):
                idx = STRATEGIC_NUMBERS.get(key)
                if idx is None:
                    log.warning(f"Unknown strategic number: {key}")
                    continue
            else:
                idx = int(key)

            if self.write_strategic_number(player_id, idx, int(value)):
                count += 1

        return count

    def _get_sn_base(self, player_id: int) -> Optional[int]:
        """Get the base address of the strategic numbers array for a player."""
        cache_key = f"sn_base_{player_id}"
        if cache_key in self._scan_cache:
            # Validate cached address is still good
            try:
                self._read_int(self._scan_cache[cache_key])
                return self._scan_cache[cache_key]
            except Exception:
                del self._scan_cache[cache_key]

        if not self.game_obj_ptr:
            try:
                self._find_game_object()
            except AOE2MemoryError:
                return None

        try:
            # Navigate: game_obj -> world -> players_array -> player -> ai_module -> sn_array
            game_world = self._read_ptr(self.game_obj_ptr + 0x8)
            players_array = self._read_ptr(game_world + 0xE8)
            player_ptr = self._read_ptr(players_array + player_id * 8)

            # AI module is at player + 0x250 (approximate, may vary by version)
            ai_module = self._read_ptr(player_ptr + 0x250)
            if not ai_module:
                return None

            # Strategic numbers array is at ai_module + 0x8
            sn_array = self._read_ptr(ai_module + 0x8)
            if sn_array:
                self._scan_cache[cache_key] = sn_array
                return sn_array

        except Exception as e:
            log.debug(f"Failed to find SN base for player {player_id}: {e}")

        return None

    def read_all_strategic_numbers(self, player_id: int) -> dict:
        """Read all known strategic numbers for debugging/display."""
        result = {}
        for name, idx in STRATEGIC_NUMBERS.items():
            val = self.read_strategic_number(player_id, idx)
            if val is not None:
                result[name] = val
        return result

    def scan_for_offsets(self) -> dict:
        """Diagnostic: try to find and report memory structure offsets.

        Use this when offsets break after a game patch.
        Prints what it finds for manual verification.
        """
        info = {"process": PROCESS_NAME, "attached": self.is_attached}

        if not self.is_attached:
            return info

        try:
            info["base_address"] = f"0x{self.base_address:X}"
            info["pid"] = self.pm.process_id

            game_ptr = self._find_game_object()
            info["game_object"] = f"0x{game_ptr:X}"

            game_world = self._read_ptr(game_ptr + 0x8)
            info["game_world"] = f"0x{game_world:X}"

            num_players = self._read_int(game_world + 0xEC)
            info["num_players"] = num_players

            players_array = self._read_ptr(game_world + 0xE8)
            info["players_array"] = f"0x{players_array:X}"

            # Try to read player 1
            p1 = self._read_ptr(players_array + 1 * 8)
            info["player_1_ptr"] = f"0x{p1:X}"

            # Scan nearby offsets for resource-like floats
            resource_candidates = []
            for offset in range(0x20, 0x100, 0x8):
                try:
                    ptr = self._read_ptr(p1 + offset)
                    if ptr and ptr > 0x10000:
                        arr = self._read_ptr(ptr + 0x8)
                        if arr:
                            f0 = self._read_float(arr)
                            if 0 < f0 < 100000:  # Looks like a resource value
                                resource_candidates.append({
                                    "offset": f"0x{offset:X}",
                                    "values": [self._read_float(arr + i * 4) for i in range(8)]
                                })
                except Exception:
                    pass
            info["resource_candidates"] = resource_candidates

        except Exception as e:
            info["error"] = str(e)

        return info
