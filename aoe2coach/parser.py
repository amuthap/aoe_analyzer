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
    engagements: list = field(default_factory=list)  # [{time, p1, p2}]
    start_positions: dict = field(default_factory=dict)  # {pid: {x, y}}
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
        pos_buckets = defaultdict(lambda: defaultdict(list))  # time_bucket -> pid -> [(x,y)]
        unit_timeline = defaultdict(list)  # pid -> [(time, uid, amount)]

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
                    uid = adata.get("unit_id", 0)
                    amt = adata.get("amount", 1)
                    unit_prod[pid][uid] += amt
                    # Also track with timestamps for upgrade-aware labeling
                    unit_timeline[pid].append((round(t_min, 1), uid, amt))
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

                # Track positions for engagement detection
                x = adata.get("x", 0)
                y = adata.get("y", 0)
                if pid > 0 and x > 0 and y > 0 and atype in ("Move", "Interact", "Patrol", "DeAttackMove"):
                    bucket = int(t_min // 3) * 3  # 3-min buckets
                    pos_buckets[bucket][pid].append((round(x), round(y)))

        # === ENGAGEMENT DETECTION ===
        # Find when players from opposite teams had actions near each other
        # Build team map from player data
        team_map = {}
        for pid_str, pdata in result["players"].items():
            team_map[int(pid_str)] = pdata.get("resolved_team_id", 0)

        engagements = []
        for bucket, players_in_bucket in sorted(pos_buckets.items()):
            for pid1 in players_in_bucket:
                for pid2 in players_in_bucket:
                    if pid1 >= pid2 or team_map.get(pid1) == team_map.get(pid2):
                        continue
                    pts1, pts2 = players_in_bucket[pid1], players_in_bucket[pid2]
                    # Sample up to 10 positions for performance
                    for x1, y1 in pts1[:10]:
                        for x2, y2 in pts2[:10]:
                            if ((x1-x2)**2 + (y1-y2)**2) < 900:  # ~30 tiles
                                engagements.append({"time": bucket, "p1": pid1, "p2": pid2})
                                break
                        else:
                            continue
                        break

        # Deduplicate engagements to ~6min windows
        seen = set()
        deduped = []
        for e in engagements:
            key = (e["time"] // 6 * 6, min(e["p1"], e["p2"]), max(e["p1"], e["p2"]))
            if key not in seen:
                seen.add(key)
                deduped.append(e)
        result["engagements"] = deduped

        # === PLAYER STARTING POSITIONS ===
        start_pos = {}
        for op in ops[:500]:  # Check first ~500 ops
            if "Action" not in op:
                continue
            act = op["Action"]
            if act.get("world_time", 0) > 30000:
                break
            ad = act.get("action_data", {})
            for atype, adata in ad.items():
                pid = adata.get("player_id", 0)
                if pid > 0 and pid not in start_pos:
                    x, y = adata.get("x", 0), adata.get("y", 0)
                    if x > 0 and y > 0:
                        start_pos[pid] = {"x": round(x, 1), "y": round(y, 1)}
        result["start_positions"] = {str(k): v for k, v in start_pos.items()}

        for pid in set(list(unit_prod.keys()) + list(research.keys()) + list(action_ct.keys())):
            # Convert unit IDs to counts (keep as IDs, game_stats.py will name them)
            units = {str(uid): count for uid, count in unit_prod[pid].items()}
            techs = [(t, tid) for t, tid in research.get(pid, [])]

            result["game_stats"][str(pid)] = {
                "units_trained": units,
                "unit_timeline": unit_timeline.get(pid, []),
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
    """Parse an AOE2 recorded game file. Uses aoe2rec (subprocess) first, falls back to mgz."""
    analysis = GameAnalysis()

    # Try aoe2rec first (Rust, fast, has deep operations parsing)
    # Runs in subprocess to isolate Rust panics
    raw = _parse_in_subprocess(file_data)

    if "error" not in raw:
        _populate_analysis(analysis, raw)
        return analysis

    # aoe2rec failed — try mgz as fallback (pure Python, won't crash)
    mgz_raw = _parse_with_mgz(file_data)
    if mgz_raw and "error" not in mgz_raw:
        _populate_analysis(analysis, mgz_raw)
        analysis.raw_errors.append("(Parsed with mgz fallback — deep stats limited)")
        return analysis

    # Both parsers failed
    analysis.raw_errors.append(raw.get("error", "Unknown parse error"))
    if mgz_raw and "error" in mgz_raw:
        analysis.raw_errors.append(f"mgz also failed: {mgz_raw['error']}")
    return analysis


def _parse_with_mgz(file_data: bytes) -> dict:
    """Fallback parser using mgz (pure Python, no crash risk)."""
    try:
        import io
        from mgz import header as mgz_header

        h = mgz_header.parse_stream(io.BytesIO(file_data))
        if not h or not hasattr(h, 'de'):
            return {"error": "mgz: no DE header found"}

        result = {"players": {}, "chats": [], "game_stats": {}}

        # Extract duration from replay section
        if hasattr(h, 'replay') and hasattr(h.replay, 'world_time'):
            result["duration"] = h.replay.world_time

        # Extract players from DE header
        de = h.de
        if hasattr(de, 'players'):
            pid = 0
            for p in de.players:
                name_obj = getattr(p, 'name', None)
                name = ""
                if name_obj:
                    if hasattr(name_obj, 'value'):
                        name = str(name_obj.value).strip()
                    else:
                        name = str(name_obj).strip()

                if not name:
                    continue  # Skip empty player slots

                pid += 1
                civ_id = getattr(p, 'civ_id', 0)
                color_id = getattr(p, 'color_id', pid - 1)
                team_id = getattr(p, 'resolved_team_id', getattr(p, 'selected_team_id', 0))
                elo = getattr(p, 'elo', 0)
                eapm = getattr(p, 'eapm', 0)
                resigned = getattr(p, 'resigned', False)
                profile_id = getattr(p, 'profile_id', 0)

                result["players"][str(pid)] = {
                    "name": name,
                    "civ_id": civ_id if isinstance(civ_id, int) else 0,
                    "color_id": color_id if isinstance(color_id, int) else 0,
                    "elo": elo if isinstance(elo, int) else 0,
                    "eapm": eapm if isinstance(eapm, int) else 0,
                    "resigned": bool(resigned),
                    "resolved_team_id": team_id if isinstance(team_id, int) else 0,
                    "profile_id": profile_id if isinstance(profile_id, int) else 0,
                }

        if not result["players"]:
            return {"error": "mgz: no players found"}

        # Extract game settings
        if hasattr(h, 'de') and hasattr(h.de, 'game_settings'):
            gs = h.de.game_settings
            result["map_id"] = getattr(gs, 'resolved_map_id', getattr(gs, 'selected_map_id', None))
            result["lobby_name"] = getattr(gs, 'lobby_name', "")
            result["speed"] = getattr(gs, 'speed', None)
            result["ranked"] = bool(getattr(gs, 'ranked', False))
            result["pop_limit"] = getattr(gs, 'population_limit', 200)

        return result

    except Exception as e:
        return {"error": f"mgz: {type(e).__name__}: {str(e)[:150]}"}


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

    # Engagements and starting positions
    analysis.engagements = raw.get("engagements", [])
    analysis.start_positions = raw.get("start_positions", {})

    # Deep game stats (from operations parsing)
    raw_stats = raw.get("game_stats", {})
    if raw_stats:
        from game_stats import UNIT_NAMES, TECH_NAMES, _categorize_unit

        # Unit upgrade chains: base_id -> [(upgrade_tech_id, upgraded_name)]
        # When a player researches the upgrade, all FUTURE units of that base type get the new name
        UPGRADE_CHAINS = {
            4: [(215, "Arbalester"), (None, "Crossbowman")],  # Archer -> Crossbow (Castle) -> Arbalester
            74: [(211, "Champion"), (74, "Long Swordsman"), (222, "Man-at-Arms")],  # Militia line
            93: [(209, "Halberdier"), (197, "Pikeman")],  # Spearman -> Pikeman -> Halberdier
            38: [(212, "Paladin"), (75, "Cavalier")],  # Knight -> Cavalier -> Paladin
            448: [(None, "Light Cavalry")],  # Scout -> Light Cavalry (auto in Castle)
            39: [(217, "Heavy Cavalry Archer")],  # Cav Archer -> Heavy CA
            279: [(239, "Heavy Scorpion")],  # Scorpion -> Heavy Scorpion
            280: [(236, "Onager")],  # Mangonel -> Onager
            329: [(None, "Heavy Camel Rider")],  # Camel -> Heavy Camel
        }

        for pid_str, pstats in raw_stats.items():
            # Build research time lookup for this player
            research_times = {}  # tech_id -> time
            for t_min, tid in pstats.get("research", []):
                if tid not in research_times:
                    research_times[tid] = t_min

            # Upgrade-aware unit naming using timeline
            units_named = {}
            unit_cats = {}
            villager_count = 0
            military_count = 0

            unit_tl = pstats.get("unit_timeline", [])
            if unit_tl:
                # Use timeline for upgrade-aware labeling
                for t_min, uid, amt in unit_tl:
                    base_name = UNIT_NAMES.get(uid, f"Unit#{uid}")

                    # Check if this unit has an upgrade chain
                    if uid in UPGRADE_CHAINS:
                        resolved_name = base_name
                        for upgrade_tech, upgraded_name in UPGRADE_CHAINS[uid]:
                            if upgrade_tech is None:
                                # Auto-upgrade in Castle Age (e.g., Crossbowman)
                                castle_time = research_times.get(101, 999)
                                if t_min >= castle_time:
                                    resolved_name = upgraded_name
                            elif upgrade_tech in research_times and t_min >= research_times[upgrade_tech]:
                                resolved_name = upgraded_name
                        base_name = resolved_name

                    units_named[base_name] = units_named.get(base_name, 0) + amt
                    cat = _categorize_unit(uid)
                    unit_cats[cat] = unit_cats.get(cat, 0) + amt
                    if uid in (83, 84):
                        villager_count += amt
                    elif cat not in ("Villager", "Trade", "Naval"):
                        military_count += amt
            else:
                # Fallback: no timeline, use simple naming
                for uid_str, count in pstats.get("units_trained", {}).items():
                    uid = int(uid_str)
                    uname = UNIT_NAMES.get(uid, f"Unit#{uid}")
                    units_named[uname] = count
                    cat = _categorize_unit(uid)
                    unit_cats[cat] = unit_cats.get(cat, 0) + count
                    if uid in (83, 84):
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
