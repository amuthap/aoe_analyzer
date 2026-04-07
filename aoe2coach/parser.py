"""AOE2 Replay Parser - uses aoe2rec-py with subprocess isolation for crash safety."""

import io
import json
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field, asdict
from typing import Optional

# Import accurate civ data from wiki-sourced database
from civ_database import CIV_IDS, CIV_DATABASE, get_civ_by_id

# Build CIV_NAMES from database
CIV_NAMES = {0: "Gaia"}
CIV_NAMES.update(CIV_IDS)

MAP_NAMES = {
    9: "Arabia", 10: "Archipelago", 11: "Baltic", 12: "Black Forest",
    13: "Coastal", 14: "Continental", 15: "Crater Lake", 16: "Fortress",
    17: "Gold Rush", 18: "Highland", 19: "Islands", 20: "Mediterranean",
    21: "Migration", 22: "Rivers", 23: "Team Islands", 24: "Full Random",
    25: "Scandinavia", 26: "Mongolia", 27: "Yucatan", 28: "Salt Marsh",
    29: "Arena", 31: "Oasis", 32: "Ghost Lake", 33: "Nomad",
    49: "MegaRandom", 67: "Lombardia", 71: "Steppe", 72: "Budapest",
    74: "Valley", 75: "Atlantic", 76: "Land of Lakes", 77: "Land Nomad",
    79: "Cenotes", 80: "Golden Pit", 86: "Hamburger",
    137: "Socotra", 139: "Four Lakes", 140: "MegaRandom",
    142: "Ravines", 143: "Wolf Hill", 144: "Sacred Springs",
    147: "Amazon Tunnel", 148: "Coastal Forest", 149: "African Clearing",
    150: "Atacama", 152: "Seize the Mountain", 153: "Crater",
    154: "Crossroads", 155: "Michi", 156: "Team Moats",
    160: "Acclivity", 161: "Eruption", 165: "Runestones",
}


@dataclass
class PlayerStats:
    name: str
    civilization: str
    civ_id: int
    color_id: int
    team: Optional[int] = None
    elo: int = 0
    eapm: int = 0
    resigned: bool = False
    winner: bool = False
    profile_id: int = 0


@dataclass
class GameAnalysis:
    map_name: str = "Unknown"
    game_type: str = "Team Game"
    game_version: str = "DE"
    duration_seconds: float = 0
    duration_display: str = "0:00"
    lobby_name: str = ""
    game_speed: str = "Normal"
    ranked: bool = False
    pop_limit: int = 200
    players: list = field(default_factory=list)
    teams: dict = field(default_factory=dict)
    game_stats: dict = field(default_factory=dict)  # Deep per-player stats
    chats: list = field(default_factory=list)
    raw_errors: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def format_time(seconds: float) -> str:
    """Format seconds into MM:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


# Subprocess script that does the actual parsing (isolates Rust panics)
_PARSE_SCRIPT = r'''
import io, json, sys, os
from collections import defaultdict

def parse_data(data_bytes):
    from aoe2rec_py.summary import RecSummary
    from aoe2rec_py.aoe2rec_py import parse_rec

    f = io.BytesIO(data_bytes)
    s = RecSummary(f)

    result = {
        "duration": s.duration,
        "players": {},
        "chats": [],
        "game_stats": {},
        "map_id": None,
        "lobby_name": "",
        "speed": None,
        "ranked": False,
        "pop_limit": 200,
    }

    for pid, pdata in s.players.items():
        result["players"][str(pid)] = {
            "name": pdata.get("name", f"Player {pid}"),
            "civ_id": pdata.get("civ_id", 0),
            "color_id": pdata.get("color_id", 0),
            "elo": pdata.get("elo", 0),
            "eapm": pdata.get("eapm", 0),
            "resigned": pdata.get("resigned", False),
            "resolved_team_id": pdata.get("resolved_team_id", 0),
            "profile_id": pdata.get("profile_id", 0),
        }

    if hasattr(s, "chats") and s.chats:
        for chat in s.chats[:20]:
            ts = chat.timestamp
            if hasattr(ts, "total_seconds"):
                ts_sec = ts.total_seconds()
            else:
                ts_sec = float(ts) / 1000 if ts else 0
            result["chats"].append({
                "time_sec": ts_sec,
                "player": chat.player,
                "message": chat.message,
            })

    # === DEEP STATS: Extract operations + game settings ===
    try:
        raw = parse_rec(data_bytes)
        ops = raw.get("operations", [])

        # Extract game settings from header
        try:
            gs = raw.get("zheader", {}).get("game_settings", {})
            result["map_id"] = gs.get("selected_map_id") or gs.get("resolved_map_id")
            result["lobby_name"] = gs.get("lobby_name", "")
            result["speed"] = gs.get("speed")
            result["ranked"] = bool(gs.get("ranked", False))
            result["pop_limit"] = gs.get("population_limit", 200)
        except Exception:
            pass

        # Aggregate per-player stats from operations
        unit_prod = defaultdict(lambda: defaultdict(int))
        research = defaultdict(list)
        build_ct = defaultdict(int)
        wall_ct = defaultdict(int)
        town_bells = defaultdict(int)
        flares = defaultdict(int)
        market = defaultdict(int)
        resign = {}
        action_ct = defaultdict(int)

        for op in ops:
            if "Action" not in op:
                continue
            act = op["Action"]
            time_ms = act.get("world_time", 0)
            t_min = time_ms / 1000 / 60
            ad = act.get("action_data", {})

            for atype, adata in ad.items():
                if atype == "Game":
                    action_ct[adata.get("player_id", 0)] += 1
                    continue
                pid = adata.get("player_id", 0)
                action_ct[pid] += 1

                if atype == "DeQueue":
                    unit_prod[pid][adata.get("unit_id", 0)] += adata.get("amount", 1)
                elif atype == "Research":
                    research[pid].append((round(t_min, 1), adata.get("technology_type", 0)))
                elif atype == "Build":
                    build_ct[pid] += 1
                elif atype == "Wall":
                    wall_ct[pid] += 1
                elif atype == "TownBell":
                    town_bells[pid] += 1
                elif atype == "Flare":
                    flares[pid] += 1
                elif atype in ("Buy", "Sell"):
                    market[pid] += 1
                elif atype == "Resign":
                    resign[pid] = round(t_min, 1)

        for pid in set(list(unit_prod.keys()) + list(research.keys()) + list(action_ct.keys())):
            # Convert unit IDs to counts (keep as IDs, game_stats.py will name them)
            units = {str(uid): count for uid, count in unit_prod[pid].items()}
            techs = [(t, tid) for t, tid in research.get(pid, [])]

            result["game_stats"][str(pid)] = {
                "units_trained": units,
                "research": techs,
                "buildings_placed": build_ct.get(pid, 0),
                "walls_built": wall_ct.get(pid, 0),
                "town_bells": town_bells.get(pid, 0),
                "flares": flares.get(pid, 0),
                "market_actions": market.get(pid, 0),
                "resign_time": resign.get(pid),
                "total_actions": action_ct.get(pid, 0),
            }
    except Exception as e:
        result["stats_error"] = str(e)[:200]

    return result

if __name__ == "__main__":
    filepath = sys.argv[1]
    with open(filepath, "rb") as f:
        data = f.read()
    try:
        result = parse_data(data)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
'''


def _parse_in_subprocess(file_data: bytes) -> dict:
    """Run aoe2rec parsing in a subprocess to isolate Rust panics."""
    # Write replay data to temp file
    with tempfile.NamedTemporaryFile(suffix='.aoe2record', delete=False) as tmp:
        tmp.write(file_data)
        tmp_path = tmp.name

    # Write parse script to temp file
    with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as script_tmp:
        script_tmp.write(_PARSE_SCRIPT)
        script_path = script_tmp.name

    try:
        # Use encoding='utf-8' with errors='replace' to handle Rust panic Unicode output on Windows
        result = subprocess.run(
            [sys.executable, script_path, tmp_path],
            capture_output=True,
            timeout=30,
            cwd=None,
        )

        # Decode stdout/stderr safely (Rust panics output Unicode box-drawing chars)
        try:
            stdout_text = result.stdout.decode('utf-8', errors='replace') if result.stdout else ""
        except Exception:
            stdout_text = ""
        try:
            stderr_text = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
        except Exception:
            stderr_text = ""

        if result.returncode != 0:
            # Check for common Rust panic patterns
            if "panicked" in stderr_text or "PanicException" in stderr_text or "bad magic" in stderr_text or not stderr_text.strip():
                return {"error": "This replay file could not be parsed. It may be an in-progress recording, a corrupted file, or from an unsupported game version. Try a completed multiplayer game replay."}
            return {"error": f"Parser error: {stderr_text[:200]}"}

        if not stdout_text.strip():
            return {"error": "Parser returned empty output"}

        return json.loads(stdout_text.strip())

    except subprocess.TimeoutExpired:
        return {"error": "Replay parsing timed out (file may be too large or corrupted)"}
    except json.JSONDecodeError:
        return {"error": "Parser returned invalid data"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
    finally:
        import os
        try:
            os.unlink(tmp_path)
        except:
            pass
        try:
            os.unlink(script_path)
        except:
            pass


def parse_replay(file_data: bytes) -> GameAnalysis:
    """Parse an AOE2 recorded game file and return analysis."""
    analysis = GameAnalysis()

    # Always use subprocess for parsing — aoe2rec Rust panics can kill
    # the process and can't be caught by Python's try/except.
    # Subprocess isolation is the only reliable protection.
    raw = _parse_in_subprocess(file_data)

    if "error" in raw:
        analysis.raw_errors.append(raw["error"])
        return analysis

    _populate_analysis(analysis, raw)
    return analysis


def _try_direct_parse(file_data: bytes) -> dict:
    """Try parsing directly in-process. May raise on Rust panics."""
    from aoe2rec_py.summary import RecSummary

    f = io.BytesIO(file_data)
    s = RecSummary(f)

    result = {"players": {}, "chats": []}

    if s.duration:
        result["duration"] = s.duration

    for pid, pdata in s.players.items():
        result["players"][str(pid)] = {
            "name": pdata.get("name", f"Player {pid}"),
            "civ_id": pdata.get("civ_id", 0),
            "color_id": pdata.get("color_id", 0),
            "elo": pdata.get("elo", 0),
            "eapm": pdata.get("eapm", 0),
            "resigned": pdata.get("resigned", False),
            "resolved_team_id": pdata.get("resolved_team_id", 0),
            "profile_id": pdata.get("profile_id", 0),
        }

    if hasattr(s, "chats") and s.chats:
        for chat in s.chats[:20]:
            ts = chat.timestamp
            if hasattr(ts, "total_seconds"):
                ts_sec = ts.total_seconds()
            else:
                ts_sec = float(ts) / 1000 if ts else 0
            result["chats"].append({
                "time_sec": ts_sec,
                "player": chat.player,
                "message": chat.message,
            })

    return result


def _populate_analysis(analysis: GameAnalysis, raw: dict):
    """Convert raw parsed data into GameAnalysis."""
    # Map name
    map_id = raw.get("map_id")
    if map_id is not None:
        analysis.map_name = MAP_NAMES.get(int(map_id), f"Map {map_id}")
    # Lobby name fallback: if lobby name contains a known map name, use that
    lobby = raw.get("lobby_name", "")
    analysis.lobby_name = lobby
    if analysis.map_name in ("Unknown", None) or (map_id is None):
        lobby_upper = lobby.upper()
        for name in MAP_NAMES.values():
            if name.upper() in lobby_upper:
                analysis.map_name = name
                break

    # Game speed
    speed_val = raw.get("speed")
    if speed_val is not None:
        speed_f = float(speed_val)
        if speed_f < 1.6:
            analysis.game_speed = "Slow" if speed_f < 1.45 else "Normal"
        else:
            analysis.game_speed = "Fast"

    # Ranked / pop limit
    analysis.ranked = bool(raw.get("ranked", False))
    pop = raw.get("pop_limit")
    if pop is not None:
        analysis.pop_limit = int(pop)

    # Duration
    duration_ms = raw.get("duration", 0)
    if duration_ms:
        total_seconds = duration_ms / 1000
        analysis.duration_seconds = total_seconds
        analysis.duration_display = format_time(total_seconds)

    # Players
    teams = {}
    for pid, pdata in raw.get("players", {}).items():
        civ_id = pdata.get("civ_id", 0)
        civ_name = CIV_NAMES.get(civ_id, f"Civ {civ_id}")
        team_id = pdata.get("resolved_team_id", 0)
        resigned = pdata.get("resigned", False)

        ps = PlayerStats(
            name=pdata.get("name", f"Player {pid}"),
            civilization=civ_name,
            civ_id=civ_id,
            color_id=pdata.get("color_id", 0),
            team=team_id,
            elo=pdata.get("elo", 0),
            eapm=pdata.get("eapm", 0),
            resigned=resigned,
            winner=not resigned,
            profile_id=pdata.get("profile_id", 0),
        )
        analysis.players.append(ps)

        if team_id not in teams:
            teams[team_id] = []
        teams[team_id].append(ps.name)

    analysis.teams = {str(k): v for k, v in teams.items()}

    # Game type
    num_teams = len(teams)
    team_sizes = [len(v) for v in teams.values()]
    if len(analysis.players) == 2:
        analysis.game_type = "1v1"
    elif num_teams == 2 and all(s == team_sizes[0] for s in team_sizes):
        analysis.game_type = f"{team_sizes[0]}v{team_sizes[0]}"
    else:
        analysis.game_type = f"{len(analysis.players)}-player"

    # Better winner detection
    team_resigned = {}
    for p in analysis.players:
        if p.team not in team_resigned:
            team_resigned[p.team] = False
        if p.resigned:
            team_resigned[p.team] = True

    winning_teams = [t for t, r in team_resigned.items() if not r]
    for p in analysis.players:
        p.winner = p.team in winning_teams

    # Chats
    for chat in raw.get("chats", []):
        analysis.chats.append({
            "time": format_time(chat.get("time_sec", 0)),
            "player": chat.get("player", ""),
            "message": chat.get("message", ""),
        })

    # Deep game stats (from operations parsing)
    raw_stats = raw.get("game_stats", {})
    if raw_stats:
        from game_stats import UNIT_NAMES, TECH_NAMES, _categorize_unit
        for pid_str, pstats in raw_stats.items():
            # Convert unit IDs to names and categorize
            units_named = {}
            unit_cats = {}
            villager_count = 0
            military_count = 0
            for uid_str, count in pstats.get("units_trained", {}).items():
                uid = int(uid_str)
                uname = UNIT_NAMES.get(uid, f"Unit#{uid}")
                units_named[uname] = count
                cat = _categorize_unit(uid)
                unit_cats[cat] = unit_cats.get(cat, 0) + count
                if uid == 83:
                    villager_count = count
                elif cat not in ("Villager", "Trade", "Naval"):
                    military_count += count

            # Convert tech IDs to names + extract age times
            research_named = []
            age_times = {}
            eco_upgrades = {}
            for t_min, tid in pstats.get("research", []):
                tname = TECH_NAMES.get(tid, f"Tech#{tid}")
                research_named.append({"time": t_min, "name": tname})
                if tid == 100: age_times["feudal"] = t_min
                elif tid == 101: age_times["castle"] = t_min
                elif tid == 102: age_times["imperial"] = t_min
                elif tid == 22: eco_upgrades["loom"] = t_min
                elif tid == 199: eco_upgrades["double_bit_axe"] = t_min
                elif tid == 202: eco_upgrades["horse_collar"] = t_min
                elif tid == 65: eco_upgrades["wheelbarrow"] = t_min
                elif tid == 219: eco_upgrades["hand_cart"] = t_min

            analysis.game_stats[pid_str] = {
                "units_trained": units_named,
                "unit_categories": unit_cats,
                "research_timeline": research_named,
                "age_times": age_times,
                "eco_upgrades": eco_upgrades,
                "buildings_placed": pstats.get("buildings_placed", 0),
                "walls_built": pstats.get("walls_built", 0),
                "town_bells": pstats.get("town_bells", 0),
                "flares": pstats.get("flares", 0),
                "market_actions": pstats.get("market_actions", 0),
                "resign_time": pstats.get("resign_time"),
                "total_actions": pstats.get("total_actions", 0),
                "villager_count": villager_count,
                "military_count": military_count,
            }
