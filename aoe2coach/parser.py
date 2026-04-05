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
    players: list = field(default_factory=list)
    teams: dict = field(default_factory=dict)
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
import io, json, sys

def parse_data(data_bytes):
    from aoe2rec_py.summary import RecSummary
    f = io.BytesIO(data_bytes)
    s = RecSummary(f)

    result = {
        "duration": s.duration,
        "players": {},
        "chats": [],
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

    return result

if __name__ == "__main__":
    import os
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
