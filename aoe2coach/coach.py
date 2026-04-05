"""AOE2 AI Coach - generates actionable improvement advice from game analysis."""

from parser import GameAnalysis, PlayerStats, format_time
from civ_database import CIV_DATABASE, get_civ_by_id, get_counter_tips


# EAPM benchmarks by skill level
EAPM_BENCHMARKS = {
    "pro": 70,        # 70+ EAPM = pro level
    "advanced": 50,   # 50-70 = advanced
    "intermediate": 30,  # 30-50 = intermediate
    "beginner": 15,   # 15-30 = beginner
}

# ELO tier labels
def elo_tier(elo: int) -> str:
    if elo >= 2000: return "Pro"
    if elo >= 1600: return "Expert"
    if elo >= 1300: return "Advanced"
    if elo >= 1000: return "Intermediate"
    if elo >= 700: return "Beginner"
    return "New Player"


def get_civ_info(civ_name: str) -> dict:
    """Get civ info from wiki-sourced database. Returns dict with type, tip, bonuses, etc."""
    if civ_name in CIV_DATABASE:
        db = CIV_DATABASE[civ_name]
        return {
            "type": db["type"],
            "tip": db["tip"],
            "bonuses": db.get("bonuses", []),
            "unique_units": db.get("unique_units", []),
            "team_bonus": db.get("team_bonus", ""),
            "meta_tier": db.get("meta_tier", "B"),
        }
    return None


# Legacy CIV_INFO kept for reference but no longer used
_LEGACY_CIV_INFO = {
    "Franks": {"type": "Cavalry", "strength": "Cheap castles, strong knights, berry bonus", "tip": "Power spike in Castle Age with knights. Get 3 TCs and mass knights. Cheap castles = map control."},
    "Britons": {"type": "Archer", "strength": "Extra range, cheap TCs, shepherd bonus", "tip": "Mass crossbows in Castle, transition to longbows in Imp. Keep distance, never let cavalry close."},
    "Goths": {"type": "Infantry Spam", "strength": "Cheap infantry, instant barracks in Imp", "tip": "Survive to Imperial and flood with huskarls + champions. You outproduce everyone late game."},
    "Mayans": {"type": "Archer", "strength": "Longer lasting resources, strong eagles", "tip": "Plume archers are your power unit. Extra resources early = faster uptime. Eagles raid gold."},
    "Aztecs": {"type": "Infantry/Monk", "strength": "Military creation speed, relic gold bonus", "tip": "Fast monks + eagles in Castle Age. Grab relics ASAP for gold income. Jaguar Warriors counter infantry."},
    "Mongols": {"type": "Cavalry Archer", "strength": "Faster hunting, Mangudai", "tip": "Mangudai are game-ending. Fast hunt bonus = faster uptime. Drill siege rams are devastating."},
    "Chinese": {"type": "Flexible", "strength": "Extra villagers start, strong tech tree", "tip": "Tough first 30 seconds (fewer resources). Once stable, you have the best tech tree. Chu Ko Nu shreds."},
    "Vikings": {"type": "Infantry/Water", "strength": "Free wheelbarrow + hand cart", "tip": "Massive eco advantage from free eco upgrades. Berserks are tanky. Dominant on water maps."},
    "Huns": {"type": "Cavalry", "strength": "No houses needed, cheap cavalry archers", "tip": "No houses = perfect build order every time. Scouts into CA is the classic play. Very aggressive civ."},
    "Teutons": {"type": "Infantry/Siege", "strength": "Extra melee armor, cheap farms", "tip": "Slow but powerful. Wall up, boom, and push with Teutonic Knights + siege. Your farms are dirt cheap."},
    "Persians": {"type": "Cavalry", "strength": "Faster TC/dock work rate, War Elephants", "tip": "Your TC works 10/15/20% faster per age - huge eco advantage. Knights in Castle, War Elephants to close out games."},
    "Japanese": {"type": "Infantry", "strength": "Faster attacking infantry, strong water", "tip": "Your infantry attack 33% faster. Samurai counter unique units. Trebuchets pack faster for mobility."},
    "Koreans": {"type": "Tower/Siege", "strength": "Free armor upgrades, War Wagons", "tip": "War Wagons are mobile tanks with range. Tower rush is a classic Korean strategy. Strong on water."},
    "Spanish": {"type": "Gunpowder/Monk", "strength": "Trade bonus, Conquistadors", "tip": "Conquistadors are mobile gunpowder cavalry. Trade bonus is huge in team games. Missionaries are fast monks."},
    "Turks": {"type": "Gunpowder", "strength": "Free chemistry, Janissaries", "tip": "Free chemistry saves 300 food 200 gold. Janissaries + Bombard Cannons push is devastating. Gold-heavy though."},
    "Italians": {"type": "Archer/Water", "strength": "Cheaper age-ups, Genoese Crossbowmen", "tip": "Genoese Crossbowmen shred cavalry. Cheaper age-ups give timing advantage. Condottiero counters gunpowder."},
    "Lithuanians": {"type": "Cavalry", "strength": "Relic-boosted knights, Leitis", "tip": "COLLECT RELICS! Each relic adds +1 attack to your knights (up to +4). Leitis ignore armor entirely."},
    "Burgundians": {"type": "Cavalry", "strength": "Early eco techs, Flemish Revolution", "tip": "Get eco techs one age earlier = huge timing advantage. Flemish Revolution is all-in but devastating."},
    "Poles": {"type": "Cavalry", "strength": "Folwark food bonus, Obuch", "tip": "Folwark grants 10% of a farm's food instantly. Obuch strips armor - pair them with archers for melting anything."},
    "Bohemians": {"type": "Gunpowder/Monk", "strength": "Chemistry in Castle Age, Houfnice", "tip": "Chemistry in CASTLE AGE is unique. Hand cannoneers early dominate. Houfnice (BBC upgrade) in Imp destroys everything."},
    "Khmer": {"type": "Siege/Elephant", "strength": "No building requirements, Ballista Elephants", "tip": "No building requirements = flexible builds (skip barracks!). Scorpions are deadly. Ballista Elephants are unique."},
    "Berbers": {"type": "Cavalry", "strength": "Cheap cavalry, Camel Archers", "tip": "Cheaper stable units (15/20% discount). Camel Archers are excellent vs. other archer civs. Strong on open maps."},
    "Ethiopians": {"type": "Archer", "strength": "Free pike/sword upgrades, Shotel Warriors", "tip": "Free barracks upgrades save resources. Royal Heirs means fast Shotel production. Strong archer civ overall."},
    "Malians": {"type": "Infantry", "strength": "Extra pierce armor on infantry, Gbeto", "tip": "Infantry with +3 pierce armor shrug off arrows. Gbeto are ranged infantry raiders. Wood savings from buildings."},
    "Malay": {"type": "Infantry/Water", "strength": "Fastest age-ups, Karambit Warriors", "tip": "Age up 66% faster! Rush to Castle/Imperial before your opponent. Forced Levy = free trash two-handed swordsmen."},
    "Burmese": {"type": "Infantry/Monk", "strength": "Free lumber upgrades, Arambai", "tip": "Free lumber camp techs boost early eco. Arambai hit hard but inaccurately. Monks with extra range from relics."},
    "Vietnamese": {"type": "Archer", "strength": "See enemy TC, extra HP archers", "tip": "You see enemy TC at game start - scout is less critical. Rattan Archers tank arrow fire. Paper Money helps allies."},
    "Bulgarians": {"type": "Infantry/Cavalry", "strength": "Free militia upgrades, Konniks", "tip": "Free militia line upgrades save big. Konniks fight on foot when unhorsed. Krepost is a cheaper castle alternative."},
    "Tatars": {"type": "Cavalry Archer", "strength": "Free thumb ring, Keshik", "tip": "Free Thumb Ring + hill bonus = deadly archers. Keshiks generate gold when fighting. Flaming Camels are siege surprise."},
    "Cumans": {"type": "Cavalry", "strength": "Feudal TC, faster Feudal", "tip": "Build a SECOND TC in Feudal Age! Massive eco boom potential. Kipchaks fire multiple arrows. Speed bonus helps raiding."},
    "Dravidians": {"type": "Infantry/Naval", "strength": "200 extra wood, Urumi Swordsmen", "tip": "200 bonus wood helps Dark Age. Urumi charge attack devastates groups. Medical Corps heals elephants. Naval powerhouse."},
    "Bengalis": {"type": "Elephant/Naval", "strength": "Ratha (ranged/melee switch), extra vils", "tip": "Ratha switches between ranged and melee mode. Resistance vs. conversion for elephants. Paiks makes elephants attack faster."},
    "Gurjaras": {"type": "Cavalry", "strength": "Camel + mounted units, Shrivamsha Rider", "tip": "Shrivamsha Riders dodge projectiles! Chakram Throwers are ranged infantry. Mill bonus with garrisoning livestock."},
    "Romans": {"type": "Infantry", "strength": "Centurion aura, cheaper militia", "tip": "Centurion boosts nearby infantry. Legionary has scorpion attack bonus. Ballista unique building provides area damage."},
    "Armenians": {"type": "Infantry/Cavalry", "strength": "Fortified Church, Composite Bowman", "tip": "Fortified Church stores relics AND heals. Composite Bowmen fire fast. Warrior Monks fight and convert."},
    "Georgians": {"type": "Cavalry", "strength": "Hill regeneration, Monaspa", "tip": "Units regenerate on hills. Monaspa gets attack bonus per nearby cavalry. Fortified churches are cheap, strong defenses."},
}  # End of legacy CIV_INFO


def generate_coaching(analysis: GameAnalysis, focus_player: str = None) -> dict:
    """Generate coaching advice from game analysis."""

    coaching = {
        "overall_grade": "B",
        "game_summary": "",
        "player_reports": [],
        "tips": [],
        "focus_areas": [],
    }

    if not analysis.players:
        coaching["game_summary"] = "Could not extract player data from this replay."
        coaching["tips"].append({"category": "Error", "tip": "The file may be corrupted or from an unsupported version."})
        return coaching

    # Game summary
    duration_min = analysis.duration_seconds / 60 if analysis.duration_seconds else 0
    game_pace = "short" if duration_min < 20 else "medium" if duration_min < 40 else "long"

    coaching["game_summary"] = (
        f"{analysis.game_type} on {analysis.map_name} - "
        f"{analysis.duration_display} ({game_pace} game)"
    )

    # Analyze each player
    for player in analysis.players:
        report = _analyze_player(player, analysis, game_pace, duration_min)
        coaching["player_reports"].append(report)

    # Focus on the target player
    if focus_player:
        for report in coaching["player_reports"]:
            if focus_player.lower() in report["name"].lower():
                coaching["focus_areas"] = report.get("improvements", [])
                coaching["overall_grade"] = report.get("grade", "B")
                break

    coaching["tips"].extend(_get_general_tips(analysis, game_pace))
    return coaching


def _analyze_player(player: PlayerStats, analysis: GameAnalysis, game_pace: str, duration_min: float) -> dict:
    """Analyze a single player's performance."""
    report = {
        "name": player.name,
        "civilization": player.civilization,
        "civ_type": "",
        "winner": player.winner,
        "elo": player.elo,
        "elo_tier": elo_tier(player.elo) if player.elo else "Unranked",
        "eapm": player.eapm,
        "team": player.team,
        "resigned": player.resigned,
        "grade": "B",
        "strengths": [],
        "improvements": [],
        "civ_advice": "",
    }

    scores = []

    # Civ info from wiki-sourced database
    civ_info = get_civ_info(player.civilization)
    if civ_info:
        report["civ_type"] = civ_info["type"]
        report["civ_advice"] = civ_info["tip"]
        # Add bonuses summary for richer coaching
        if civ_info.get("bonuses"):
            report["civ_bonuses"] = civ_info["bonuses"][:4]  # Top 4 bonuses
        if civ_info.get("unique_units"):
            report["unique_units"] = civ_info["unique_units"]
        report["meta_tier"] = civ_info.get("meta_tier", "B")

    # --- EAPM Analysis ---
    if player.eapm:
        eapm = player.eapm
        if eapm >= EAPM_BENCHMARKS["pro"]:
            report["strengths"].append(f"Exceptional EAPM ({eapm}) - pro-level multitasking!")
            scores.append(95)
        elif eapm >= EAPM_BENCHMARKS["advanced"]:
            report["strengths"].append(f"Strong EAPM ({eapm}) - good multitasking")
            scores.append(80)
        elif eapm >= EAPM_BENCHMARKS["intermediate"]:
            report["strengths"].append(f"Decent EAPM ({eapm})")
            scores.append(65)
            report["improvements"].append({
                "area": "Actions Per Minute",
                "severity": "medium",
                "message": f"Your EAPM of {eapm} is in the intermediate range. Higher EAPM means better multitasking.",
                "advice": [
                    "Practice cycling through TCs with hotkeys (H key by default)",
                    "Use control groups for military (Ctrl+1, Ctrl+2, etc.)",
                    "Queue villagers while managing military - never let TC idle",
                    "Set rally points and use gather points efficiently",
                ]
            })
        else:
            scores.append(40)
            report["improvements"].append({
                "area": "Actions Per Minute (Critical)",
                "severity": "high",
                "message": f"Your EAPM of {eapm} is quite low. This means you're not giving enough commands, leading to idle units and idle economy.",
                "advice": [
                    "Learn and drill hotkeys: Q/W/E for military buildings, H for TC",
                    "Practice the 'TC check loop': every few seconds, tap H to check your TC",
                    "Use control groups: select army, press Ctrl+1. Now press 1 to select them anytime",
                    "Play against the AI to practice multitasking without pressure",
                    "Watch T90's 'Low ELO Legends' for common mistakes to avoid",
                ]
            })

    # --- ELO-based Advice ---
    if player.elo:
        tier = elo_tier(player.elo)
        if tier == "Intermediate":
            report["improvements"].append({
                "area": f"Climbing from {player.elo} ELO",
                "severity": "medium",
                "message": f"At {player.elo} ELO ({tier}), the biggest gains come from economy fundamentals.",
                "advice": [
                    "Zero idle TC time is the #1 skill - always be making villagers until 120+ pop",
                    "Learn 2-3 build orders by heart (scouts, archers, fast castle)",
                    "Don't forget eco upgrades: Double-Bit Axe, Horse Collar, etc. on time",
                    "Scout your opponent in Feudal to know if you need to defend or attack",
                ]
            })
        elif tier == "Beginner":
            report["improvements"].append({
                "area": f"Beginner Fundamentals ({player.elo} ELO)",
                "severity": "high",
                "message": f"At {player.elo} ELO, focus on the basics before strategy.",
                "advice": [
                    "Learn ONE build order and practice it vs AI until you can do it from memory",
                    "Never stop making villagers - aim for 0 idle TC time in Dark Age",
                    "Use sheep efficiently: only kill one at a time, garrison scout",
                    "Watch Hera's 'Guide to 2000 ELO' series - best learning resource",
                    "Play ranked 1v1 to improve faster - team games mask individual mistakes",
                ]
            })

    # --- Game Outcome Analysis ---
    if player.winner:
        report["strengths"].append("Won the game!")
        if duration_min > 40:
            report["strengths"].append("Survived a long game - good late-game endurance")
        scores.append(75)
    else:
        if player.resigned:
            if duration_min < 15:
                report["improvements"].append({
                    "area": "Early Game Survival",
                    "severity": "high",
                    "message": "Resigned early - you may have been overwhelmed by early aggression or fell behind economically.",
                    "advice": [
                        "Scout your opponent: if you see barracks + range, expect archers. If stables, expect scouts",
                        "Quick-wall with houses and palisades to buy time",
                        "Build 1-2 defensive towers if you're being tower rushed",
                        "Keep making villagers even while under attack - economy wins games",
                        "Don't resign too early! Many games are recoverable, especially in team games",
                    ]
                })
                scores.append(30)
            elif duration_min < 30:
                report["improvements"].append({
                    "area": "Mid-Game Execution",
                    "severity": "medium",
                    "message": "Resigned in the mid-game. The transition from Feudal to Castle Age is often where games are decided.",
                    "advice": [
                        "Get 2-3 TCs immediately after hitting Castle Age",
                        "Balance military production with eco growth",
                        "Don't over-commit to one unit type - adapt to what your opponent makes",
                        "Control key resources: gold and stone on the map",
                    ]
                })
                scores.append(45)
            else:
                report["improvements"].append({
                    "area": "Late Game Decision Making",
                    "severity": "low",
                    "message": "Resigned in a long game. Late game is about trade, map control, and composition switches.",
                    "advice": [
                        "Set up trade early (by 35 minutes) - gold wins late games",
                        "Learn trash unit transitions: halberdiers + skirmishers when gold runs out",
                        "Control relics for trickle gold income",
                        "Don't forget trebuchets - you need siege to close out games",
                    ]
                })
                scores.append(55)

    # --- Team Contribution ---
    if analysis.game_type != "1v1":
        team_members = [p for p in analysis.players if p.team == player.team]
        team_eapms = [p.eapm for p in team_members if p.eapm]
        if team_eapms and player.eapm:
            avg_team_eapm = sum(team_eapms) / len(team_eapms)
            if player.eapm >= avg_team_eapm * 1.2:
                report["strengths"].append(f"Highest activity on your team (EAPM: {player.eapm} vs team avg: {int(avg_team_eapm)})")
            elif player.eapm < avg_team_eapm * 0.7:
                report["improvements"].append({
                    "area": "Team Contribution",
                    "severity": "medium",
                    "message": f"Your EAPM ({player.eapm}) was significantly lower than your team average ({int(avg_team_eapm)}).",
                    "advice": [
                        "In team games, try to match your teammates' activity level",
                        "Help with rushes or defense coordination",
                        "Use flares (Alt+click minimap) to communicate with teammates",
                        "Pocket player? Focus on booming. Flank? Focus on defending and pressuring",
                    ]
                })

    # --- Civ-Specific Advice for Losers ---
    if not player.winner and civ_info:
        advice_list = [
            civ_info["tip"],
            f"Study pro replays of {player.civilization} on YouTube",
        ]
        # Add unique unit advice
        if civ_info.get("unique_units"):
            uu_names = ", ".join(civ_info["unique_units"])
            advice_list.append(f"Master your unique units: {uu_names}")
        # Add key bonuses as reminders
        if civ_info.get("bonuses"):
            advice_list.append(f"Key bonus: {civ_info['bonuses'][0]}")

        report["improvements"].append({
            "area": f"Playing {player.civilization} ({civ_info['type']})",
            "severity": "low",
            "message": f"As {player.civilization}, leverage your unique strengths.",
            "advice": advice_list,
        })

    # Calculate overall grade
    if scores:
        avg_score = sum(scores) / len(scores)
        if avg_score >= 90: report["grade"] = "A+"
        elif avg_score >= 80: report["grade"] = "A"
        elif avg_score >= 70: report["grade"] = "B+"
        elif avg_score >= 60: report["grade"] = "B"
        elif avg_score >= 50: report["grade"] = "C+"
        elif avg_score >= 40: report["grade"] = "C"
        else: report["grade"] = "D"
    else:
        report["grade"] = "?"

    return report


def _get_general_tips(analysis: GameAnalysis, game_pace: str) -> list:
    """Get general tips based on game context."""
    tips = []

    if game_pace == "short":
        tips.append({
            "category": "Game Tempo",
            "tip": "Short game (<20 min). Focus on build order execution and early defense."
        })
    elif game_pace == "long":
        tips.append({
            "category": "Late Game",
            "tip": "60+ minute game. Set up trade by 35 min. Learn trash transitions (halbs + skirms). Control relics."
        })

    # Civ matchup tips
    civs = [p.civilization for p in analysis.players]
    if "Goths" in civs:
        tips.append({"category": "Matchup Alert", "tip": "Goths detected! End the game before Imperial - Goth infantry flood is near-impossible to stop in late game."})
    if "Lithuanians" in civs:
        tips.append({"category": "Matchup Alert", "tip": "Lithuanians in game! Contest relics aggressively - each relic gives their knights +1 attack (up to +4)."})
    if "Cumans" in civs:
        tips.append({"category": "Matchup Alert", "tip": "Cumans can build a 2nd TC in Feudal Age! Expect either a massive boom or a fast Castle. Scout early."})

    # ELO distribution tip
    elos = [p.elo for p in analysis.players if p.elo > 0]
    if elos:
        avg_elo = sum(elos) / len(elos)
        tips.append({
            "category": "Lobby",
            "tip": f"Average ELO in this game: {int(avg_elo)} ({elo_tier(int(avg_elo))} level)"
        })

    # Always include fundamental tip
    tips.append({
        "category": "Golden Rule",
        "tip": "The #1 skill at EVERY ELO: keep your TC producing villagers. Zero idle TC time wins more games than any strategy."
    })

    return tips
