"""Deep game statistics extractor — processes replay operations for pro-level analysis."""

from collections import defaultdict

# Verified unit IDs → names (source: AoE2ScenarioParser github.com/KSneijders)
UNIT_NAMES = {
    4: "Archer", 5: "Hand Cannoneer", 6: "Elite Skirmisher", 7: "Skirmisher",
    8: "Longbowman", 11: "Mangudai", 13: "Fishing Ship", 15: "Junk",
    16: "Imperial Camel Rider", 17: "Trade Cog",
    21: "War Galley", 24: "Crossbowman", 25: "Teutonic Knight",
    27: "Cataphract", 28: "Chu Ko Nu", 29: "Mangonel",
    30: "Bombard Cannon", 33: "Monk", 34: "Cavalry Archer",
    36: "Bombard Cannon", 38: "Knight", 39: "Cavalry Archer",
    40: "Cataphract", 41: "Huskarl", 42: "Trebuchet",
    43: "War Elephant", 44: "Mameluke", 46: "Janissary",
    47: "Woad Raider", 50: "Berserk", 73: "Chu Ko Nu",
    74: "Militia", 75: "Man-at-Arms", 76: "Heavy Swordsman",
    77: "Long Swordsman", 78: "Camel Rider", 79: "Heavy Camel Rider",
    80: "Scorpion", 83: "Villager", 84: "Villager",
    85: "Fire Ship", 87: "Galley", 90: "Arbalester",
    91: "Light Cavalry", 93: "Spearman", 95: "Transport Ship",
    98: "Hand Cannoneer", 101: "Onager", 102: "Siege Onager",
    103: "Hussar", 104: "Halberdier", 105: "Tarkan",
    106: "Conquistador", 107: "Janissary", 108: "Plumed Archer",
    109: "Eagle Scout", 110: "Jaguar Warrior", 114: "Boyar",
    116: "Turtle Ship", 117: "War Wagon", 125: "Monk",
    128: "Trade Cart", 133: "Genoese Crossbowman", 134: "Condottiero",
    143: "Slinger", 149: "Elite Eagle Warrior", 151: "Champion",
    185: "Slinger", 190: "Organ Gun", 191: "Camel Archer",
    195: "Shotel Warrior", 197: "Gbeto", 198: "Caravel",
    201: "Genitour", 203: "Fire Galley", 209: "Demolition Ship",
    232: "Woad Raider", 239: "War Elephant", 250: "Longboat",
    258: "Khan", 270: "Flaming Camel", 273: "Steppe Lancer",
    274: "Elite Steppe Lancer", 279: "Scorpion", 280: "Mangonel",
    281: "Throwing Axeman", 282: "Mameluke", 283: "Cavalier",
    291: "Samurai", 329: "Camel Rider", 330: "Heavy Camel Rider",
    331: "Trebuchet", 358: "Pikeman", 359: "Halberdier",
    420: "Cannon Galleon", 422: "Capped Ram", 440: "Petard",
    441: "Hussar", 442: "Galleon", 448: "Scout Cavalry",
    473: "Two-Handed Swordsman", 474: "Heavy Cavalry Archer",
    475: "Elite Woad Raider", 476: "Elite Cataphract",
    477: "Elite Teutonic Knight", 478: "Elite Huskarl",
    479: "Elite Mameluke", 480: "Hussar", 481: "Elite War Elephant",
    482: "Elite Chu Ko Nu", 483: "Elite Samurai",
    484: "Elite Mangudai", 485: "Elite Berserk",
    487: "Elite Tarkan", 488: "Elite Plumed Archer",
    490: "Elite War Wagon", 491: "Elite Turtle Ship",
    492: "Arbalester", 494: "Elite Boyar",
    527: "Heavy Demolition Ship", 529: "Fire Ship",
    530: "Elite Longbowman", 531: "Elite Throwing Axeman",
    539: "Galley", 542: "Heavy Scorpion",
    546: "Light Cavalry", 548: "Siege Ram",
    550: "Onager", 553: "Elite Cataphract",
    554: "Elite Teutonic Knight", 555: "Elite Huskarl",
    556: "Elite Mameluke", 557: "Elite Janissary",
    558: "Elite War Elephant", 559: "Elite Chu Ko Nu",
    567: "Champion", 569: "Paladin",
    588: "Siege Onager", 691: "Elite Cannon Galleon",
    726: "Elite Jaguar Warrior", 751: "Eagle Scout",
    752: "Elite Eagle Warrior", 753: "Eagle Warrior",
    755: "Tarkan", 757: "Elite Tarkan",
    759: "Huskarl", 761: "Elite Huskarl",
    763: "Plumed Archer", 765: "Elite Plumed Archer",
    771: "Conquistador", 773: "Elite Conquistador",
    775: "Missionary", 827: "War Wagon",
    829: "Elite War Wagon", 831: "Turtle Ship",
    832: "Elite Turtle Ship",
    866: "Genoese Crossbowman", 868: "Elite Genoese Crossbowman",
    869: "Magyar Huszar", 871: "Elite Magyar Huszar",
    873: "Elephant Archer", 875: "Elite Elephant Archer",
    876: "Boyar", 878: "Elite Boyar",
    879: "Kamayuk", 881: "Elite Kamayuk",
    882: "Condottiero",
    1001: "Organ Gun", 1003: "Elite Organ Gun",
    1004: "Caravel", 1006: "Elite Caravel",
    1007: "Camel Archer", 1009: "Elite Camel Archer",
    1010: "Genitour", 1012: "Elite Genitour",
    1013: "Gbeto", 1015: "Elite Gbeto",
    1016: "Shotel Warrior", 1018: "Elite Shotel Warrior",
    1103: "Fire Galley", 1104: "Demolition Raft",
    1105: "Siege Tower", 1116: "Eagle Warrior",
    1117: "Elite Eagle Warrior",
    1120: "Ballista Elephant", 1122: "Elite Ballista Elephant",
    1123: "Karambit Warrior", 1125: "Elite Karambit Warrior",
    1126: "Arambai", 1128: "Elite Arambai",
    1129: "Rattan Archer", 1131: "Elite Rattan Archer",
    1132: "Battle Elephant", 1134: "Elite Battle Elephant",
    1155: "Imperial Skirmisher",
    1225: "Dromon",
    1370: "Steppe Lancer", 1372: "Elite Steppe Lancer",
    1570: "Xolotl Warrior",
    1655: "Coustillier", 1657: "Elite Coustillier",
    1658: "Serjeant", 1659: "Elite Serjeant",
    1663: "Flemish Militia", 1668: "Camel Scout",
    1699: "Flemish Militia",
    1701: "Obuch", 1703: "Elite Obuch",
    1704: "Hussite Wagon", 1706: "Elite Hussite Wagon",
    1707: "Winged Hussar", 1709: "Houfnice",
    1735: "Urumi Swordsman", 1737: "Elite Urumi Swordsman",
    1738: "Ratha", 1740: "Elite Ratha",
    1741: "Chakram Thrower", 1743: "Elite Chakram Thrower",
    1744: "Armored Elephant", 1746: "Siege Elephant",
    1747: "Ghulam", 1749: "Elite Ghulam",
    1750: "Thirisadai",
    1751: "Shrivamsha Rider", 1753: "Elite Shrivamsha Rider",
    1755: "Camel Scout",
    1759: "Ratha Ranged", 1761: "Elite Ratha Ranged",
    1790: "Centurion", 1792: "Elite Centurion",
    1793: "Legionary", 1795: "Dromon",
    1800: "Composite Bowman", 1802: "Elite Composite Bowman",
    1803: "Monaspa", 1805: "Elite Monaspa",
    1811: "Warrior Priest", 1813: "Savar",
    1908: "Iron Pagoda", 1910: "Elite Iron Pagoda",
    1911: "Grenadier", 1920: "Liao Dao", 1922: "Elite Liao Dao",
    1923: "Mounted Trebuchet",
    1948: "Lou Chuan", 1949: "Tiger Cavalry", 1951: "Elite Tiger Cavalry",
    1952: "Xianbei Raider",
    1959: "White Feather Guard", 1961: "Elite White Feather Guard",
    2566: "Kona", 2568: "Elite Kona",
    2569: "Bolas Rider", 2571: "Elite Bolas Rider",
    2562: "Guecha Warrior", 2564: "Elite Guecha Warrior",
    2579: "Blackwood Archer", 2581: "Elite Blackwood Archer",
    2582: "Ibirapema Warrior", 2584: "Elite Ibirapema Warrior",
    2586: "Temple Guard", 2587: "Elite Temple Guard",
    2626: "Hulk", 2627: "War Hulk", 2628: "Carrack",
    2633: "Catapult Galleon",
}

# Verified tech IDs → names (source: AoE2ScenarioParser github.com/KSneijders)
TECH_NAMES = {
    # Ages
    100: "Feudal Age", 101: "Castle Age", 102: "Imperial Age", 103: "Imperial Age",
    # Eco - Lumberjack
    199: "Double-Bit Axe", 200: "Bow Saw", 201: "Two-Man Saw",
    # Eco - Farm
    202: "Horse Collar", 203: "Heavy Plow", 204: "Crop Rotation",
    # Eco - Mining
    182: "Gold Mining", 213: "Gold Shaft Mining", 278: "Stone Mining", 279: "Stone Shaft Mining",
    # Eco - Other
    22: "Loom", 65: "Wheelbarrow", 219: "Hand Cart",
    8: "Town Watch", 254: "Town Patrol",
    12: "Masonry", 188: "Coinage", 194: "Caravan",
    # Blacksmith - Attack
    13: "Fletching", 23: "Bodkin Arrow", 14: "Forging",
    15: "Iron Casting", 76: "Blast Furnace",
    # Blacksmith - Armor
    17: "Scale Mail Armor", 83: "Chain Mail Armor", 77: "Plate Mail Armor",
    80: "Chain Barding Armor", 81: "Plate Barding Armor", 82: "Plate Mail Armor",
    54: "Padded Archer Armor", 55: "Leather Archer Armor", 68: "Ring Archer Armor",
    # Military upgrades
    67: "Squires", 39: "Husbandry", 93: "Ballistics", 47: "Chemistry",
    50: "Siege Engineers", 252: "Conscription",
    315: "Bloodlines", 316: "Parthian Tactics", 319: "Thumb Ring",
    435: "Bloodlines", 437: "Thumb Ring",
    # Unit line upgrades
    197: "Pikeman", 209: "Halberdier", 429: "Halberdier",
    222: "Man-at-Arms", 74: "Long Swordsman", 211: "Champion",
    75: "Cavalier", 265: "Paladin", 212: "Paladin",
    215: "Arbalester", 217: "Heavy Cavalry Archer",
    236: "Onager", 237: "Siege Ram", 239: "Heavy Scorpion",
    # Monk
    231: "Sanctity", 230: "Block Printing", 221: "Fervor",
    232: "Illumination", 45: "Faith", 321: "Theocracy", 322: "Heresy",
    # Other
    249: "Sappers", 360: "Arson", 373: "Supplies", 428: "Gambesons",
    380: "Steppe Husbandry",
    # Unique techs (common ones)
    492: "Inquisition", 569: "Elite Shotel Warrior", 574: "Royal Heirs",
}

# Unit categories for analysis (verified IDs from AoE2ScenarioParser)
UNIT_CATEGORIES = {
    "Villager": [83, 84],
    "Infantry": [74, 75, 76, 77, 93, 104, 151, 358, 359, 473, 567, 753, 1116, 1663, 1699, 1701, 1793],
    "Archer": [4, 5, 6, 7, 24, 90, 98, 143, 185, 492, 1155],
    "Cavalry": [38, 91, 103, 283, 441, 448, 480, 569, 546, 1707],
    "Cavalry Archer": [39, 34, 474],
    "Camel": [78, 79, 329, 330, 16, 1668, 1755],
    "Elephant": [43, 239, 1132, 1134, 1120, 1122, 1744, 1746, 873, 875],
    "Siege": [29, 80, 101, 102, 280, 279, 542, 550, 36, 30, 331, 42, 440, 422, 548, 588],
    "Monk": [33, 125, 1811],
    "Naval": [13, 15, 17, 21, 85, 87, 95, 203, 209, 420, 442, 527, 529, 539, 1103, 1104, 1225, 1795, 1948, 2626, 2627, 2628, 2633],
    "Trade": [128, 204],
    "Unique Unit": [],  # Catch-all for unknowns
}


def _categorize_unit(uid):
    """Return the category name for a unit ID."""
    for cat, ids in UNIT_CATEGORIES.items():
        if uid in ids:
            return cat
    return "Unique Unit"


def extract_game_stats(raw_operations: list) -> dict:
    """Extract detailed per-player stats from raw replay operations.

    Returns dict with per-player stats including:
    - units_trained: {unit_name: count}
    - unit_categories: {category: count}
    - research_timeline: [(minute, tech_name)]
    - age_times: {feudal: min, castle: min, imperial: min}
    - buildings_placed: count
    - town_bells: count
    - flares: count
    - market_actions: count
    - resign_time: minute or None
    - total_actions: count
    - villager_count: int
    - military_count: int
    """
    stats = {}

    unit_production = defaultdict(lambda: defaultdict(int))
    research_timeline = defaultdict(list)
    build_count = defaultdict(int)
    town_bells = defaultdict(int)
    flares = defaultdict(int)
    market_actions = defaultdict(int)
    resign_times = {}
    action_count = defaultdict(int)
    wall_count = defaultdict(int)

    for op in raw_operations:
        if 'Action' not in op:
            continue
        act = op['Action']
        time_ms = act.get('world_time', 0)
        t_min = time_ms / 1000 / 60
        ad = act.get('action_data', {})

        for atype, adata in ad.items():
            if atype == 'Game':
                pid = adata.get('player_id', 0)
                action_count[pid] += 1
                continue

            pid = adata.get('player_id', 0)
            action_count[pid] += 1

            if atype == 'DeQueue':
                uid = adata.get('unit_id', 0)
                amt = adata.get('amount', 1)
                unit_production[pid][uid] += amt
            elif atype == 'Research':
                tech = adata.get('technology_type', 0)
                research_timeline[pid].append((t_min, tech))
            elif atype == 'Build':
                build_count[pid] += 1
            elif atype == 'Wall':
                wall_count[pid] += 1
            elif atype == 'TownBell':
                town_bells[pid] += 1
            elif atype == 'Flare':
                flares[pid] += 1
            elif atype in ('Buy', 'Sell'):
                market_actions[pid] += 1
            elif atype == 'Resign':
                resign_times[pid] = t_min

    # Build per-player stats
    all_players = set(list(unit_production.keys()) + list(research_timeline.keys()) +
                      list(build_count.keys()) + list(action_count.keys()))

    for pid in sorted(all_players):
        # Units
        units_trained = {}
        unit_cats = defaultdict(int)
        villager_count = 0
        military_count = 0

        for uid, count in sorted(unit_production[pid].items(), key=lambda x: -x[1]):
            uname = UNIT_NAMES.get(uid, f"Unit#{uid}")
            units_trained[uname] = count
            cat = _categorize_unit(uid)
            unit_cats[cat] += count
            if uid == 83:
                villager_count = count
            elif cat not in ("Villager", "Trade", "Naval"):
                military_count += count

        # Research — extract age-up times
        age_times = {}
        research_list = []
        for t_min, tech in research_timeline.get(pid, []):
            tname = TECH_NAMES.get(tech, f"Tech#{tech}")
            research_list.append({"time": round(t_min, 1), "name": tname})
            if tech == 100:
                age_times["feudal"] = round(t_min, 1)
            elif tech == 101:
                age_times["castle"] = round(t_min, 1)
            elif tech == 102:
                age_times["imperial"] = round(t_min, 1)

        # Find key eco upgrade times
        eco_upgrades = {}
        for t_min, tech in research_timeline.get(pid, []):
            if tech == 22:
                eco_upgrades["loom"] = round(t_min, 1)
            elif tech == 199:
                eco_upgrades["double_bit_axe"] = round(t_min, 1)
            elif tech == 202:
                eco_upgrades["horse_collar"] = round(t_min, 1)
            elif tech == 65:
                eco_upgrades["wheelbarrow"] = round(t_min, 1)
            elif tech == 219:
                eco_upgrades["hand_cart"] = round(t_min, 1)

        stats[pid] = {
            "units_trained": units_trained,
            "unit_categories": dict(unit_cats),
            "research_timeline": research_list,
            "age_times": age_times,
            "eco_upgrades": eco_upgrades,
            "buildings_placed": build_count.get(pid, 0),
            "walls_built": wall_count.get(pid, 0),
            "town_bells": town_bells.get(pid, 0),
            "flares": flares.get(pid, 0),
            "market_actions": market_actions.get(pid, 0),
            "resign_time": round(resign_times[pid], 1) if pid in resign_times else None,
            "total_actions": action_count.get(pid, 0),
            "villager_count": villager_count,
            "military_count": military_count,
        }

    return stats


def format_player_stats_for_ai(player_name: str, player_stats: dict, duration_min: float) -> str:
    """Format one player's stats into a compact text block for the AI prompt."""
    s = player_stats
    lines = [f"=== DETAILED STATS: {player_name} ==="]

    # Age times
    at = s.get("age_times", {})
    if at:
        parts = []
        if "feudal" in at: parts.append(f"Feudal @{at['feudal']}min")
        if "castle" in at: parts.append(f"Castle @{at['castle']}min")
        if "imperial" in at: parts.append(f"Imperial @{at['imperial']}min")
        lines.append(f"Age-ups: {', '.join(parts)}")

    # Eco upgrades
    eco = s.get("eco_upgrades", {})
    if eco:
        parts = [f"{k.replace('_',' ').title()}@{v}min" for k, v in eco.items()]
        lines.append(f"Eco upgrades: {', '.join(parts)}")

    # Units
    lines.append(f"Villagers trained: {s.get('villager_count', 0)} | Military trained: {s.get('military_count', 0)}")
    cats = s.get("unit_categories", {})
    if cats:
        cat_parts = [f"{k}:{v}" for k, v in sorted(cats.items(), key=lambda x: -x[1]) if k != "Villager"]
        lines.append(f"Army composition: {', '.join(cat_parts)}")

    units = s.get("units_trained", {})
    if units:
        top_units = [(n, c) for n, c in sorted(units.items(), key=lambda x: -x[1]) if n != "Villager"][:6]
        lines.append(f"Top units: {', '.join(f'{n}({c})' for n, c in top_units)}")

    # Research timeline (key techs only)
    research = s.get("research_timeline", [])
    if research:
        key_techs = [r for r in research if not r["name"].startswith("Tech#")]
        if key_techs:
            lines.append(f"Research order ({len(key_techs)} techs): " +
                         ", ".join(f"{r['name']}@{r['time']}m" for r in key_techs[:12]))

    # Activity
    lines.append(f"Buildings placed: {s.get('buildings_placed', 0)} | "
                 f"Walls built: {s.get('walls_built', 0)} | "
                 f"Total actions: {s.get('total_actions', 0)}")

    # Events
    events = []
    if s.get("town_bells", 0) > 0:
        events.append(f"Town bell rang {s['town_bells']}x (raided!)")
    if s.get("flares", 0) > 0:
        events.append(f"Flared teammates {s['flares']}x")
    if s.get("market_actions", 0) > 0:
        events.append(f"Market transactions: {s['market_actions']}")
    if s.get("resign_time"):
        events.append(f"Resigned at {s['resign_time']}min")
    if events:
        lines.append(f"Events: {' | '.join(events)}")

    return "\n".join(lines)


# Unit counter recommendations: what to build against each unit type
COUNTER_ADVICE = {
    "Knight": {"counter": "Pikeman/Halberdier", "also": "Camel Rider, Monk (small groups)", "avoid": "Archers alone"},
    "Cavalier": {"counter": "Halberdier", "also": "Heavy Camel, Monk", "avoid": "Light infantry"},
    "Paladin": {"counter": "Halberdier (massed)", "also": "Heavy Camel, Kamayuk", "avoid": "Anything not anti-cav"},
    "Crossbowman": {"counter": "Skirmisher, Mangonel", "also": "Eagle Warrior, Huskarl, Cavalry charge", "avoid": "Infantry without shields"},
    "Arbalester": {"counter": "Elite Skirmisher, Onager", "also": "Huskarl, Eagle, Ram to tank", "avoid": "Slow infantry"},
    "Archer": {"counter": "Skirmisher", "also": "Scout rush", "avoid": "Slow melee units"},
    "Spearman": {"counter": "Archer, Skirmisher", "also": "Man-at-Arms, Militia", "avoid": "Cavalry into spears"},
    "Pikeman": {"counter": "Archer, Hand Cannoneer", "also": "Scorpion, Mangonel", "avoid": "Knights into pikes"},
    "Halberdier": {"counter": "Arbalester, Hand Cannoneer", "also": "Champion, Scorpion", "avoid": "Any cavalry"},
    "Militia": {"counter": "Archer", "also": "Any ranged unit", "avoid": "Nothing — militia is weak"},
    "Man-at-Arms": {"counter": "Archer (kite)", "also": "Skirmisher + wall", "avoid": "Engaging in melee early"},
    "Champion": {"counter": "Arbalester, Hand Cannoneer", "also": "Cataphract, Jaguar Warrior", "avoid": "Other infantry"},
    "Scout Cavalry": {"counter": "Spearman, Walls", "also": "Quick-wall, garrison in TC", "avoid": "Open eco with no military"},
    "Light Cavalry": {"counter": "Pikeman", "also": "Camel Rider, Knight", "avoid": "Using them vs pikes"},
    "Hussar": {"counter": "Halberdier", "also": "Camel, heavy cavalry", "avoid": "Chasing hussars with slow units"},
    "Camel Scout": {"counter": "Pikeman, Archer", "also": "Monk", "avoid": "Knights into camels"},
    "War Elephant": {"counter": "Halberdier (mass)", "also": "Monk (convert!), Heavy Scorpion", "avoid": "Small melee groups"},
    "Ballista Elephant": {"counter": "Cavalry charge, Bombard Cannon", "also": "Onager, Monks", "avoid": "Massed infantry in a line"},
    "Shotel Warrior": {"counter": "Archer, Hand Cannoneer", "also": "Knight charge", "avoid": "Slow infantry 1v1"},
    "Conquistador": {"counter": "Skirmisher, Camel Archer", "also": "Pikeman if close", "avoid": "Chasing with slow units"},
    "Mangonel": {"counter": "Cavalry charge, Bombard Cannon", "also": "Spread units, dodge shots", "avoid": "Clumping archers"},
    "Scorpion": {"counter": "Cavalry, Bombard Cannon", "also": "Mangonel, spread out", "avoid": "Lines of infantry"},
    "Trebuchet": {"counter": "Cavalry raid, Bombard Cannon", "also": "Trebuchet war (more trebs)", "avoid": "Ignoring enemy trebs"},
    "Monk": {"counter": "Light Cavalry, Eagle Warrior", "also": "Kill monks first in fights", "avoid": "Sending 1-2 expensive units"},
    "Trade Cart": {"counter": "Light Cavalry raid", "also": "Hussar raid trade route", "avoid": "Ignoring enemy trade"},
    "Bombard Cannon": {"counter": "Cavalry charge", "also": "Onager, your own BBC", "avoid": "Slow approach from range"},
}


def get_battle_advice(player_name: str, player_civ: str, player_units: dict,
                      engagements: list, players: list, game_stats: dict) -> list:
    """Generate battle-specific counter advice for a player.

    Returns list of dicts: [{opponent, their_units, your_units, advice}]
    """
    if not engagements or not players:
        return []

    # Build player index maps
    pid_by_name = {}
    name_by_pid = {}
    civ_by_pid = {}
    for i, p in enumerate(players):
        pid = i + 1
        pid_by_name[p["name"]] = pid
        name_by_pid[pid] = p["name"]
        civ_by_pid[pid] = p["civilization"]

    my_pid = pid_by_name.get(player_name)
    if not my_pid:
        return []

    # Find who this player fought
    opponent_pids = set()
    for e in engagements:
        if e.get("p1") == my_pid:
            opponent_pids.add(e["p2"])
        elif e.get("p2") == my_pid:
            opponent_pids.add(e["p1"])

    results = []
    for opp_pid in sorted(opponent_pids):
        opp_name = name_by_pid.get(opp_pid, "?")
        opp_civ = civ_by_pid.get(opp_pid, "?")
        opp_pid_str = str(opp_pid)

        # Get opponent's units
        opp_stats = game_stats.get(opp_pid_str, {})
        opp_units = opp_stats.get("units_trained", {})
        opp_top = [(n, c) for n, c in sorted(opp_units.items(), key=lambda x: -x[1])
                   if n != "Villager"][:4]

        if not opp_top:
            continue

        # Generate counter advice for each opponent unit
        counters = []
        for unit_name, count in opp_top:
            if unit_name in COUNTER_ADVICE:
                ca = COUNTER_ADVICE[unit_name]
                counters.append({
                    "enemy_unit": unit_name,
                    "enemy_count": count,
                    "counter": ca["counter"],
                    "also": ca.get("also", ""),
                    "avoid": ca.get("avoid", ""),
                })

        # Count engagements with this opponent
        fight_count = sum(1 for e in engagements
                         if (e.get("p1") == my_pid and e.get("p2") == opp_pid) or
                            (e.get("p2") == my_pid and e.get("p1") == opp_pid))

        results.append({
            "opponent": opp_name,
            "opponent_civ": opp_civ,
            "fight_count": fight_count,
            "their_top_units": opp_top,
            "counters": counters,
        })

    return results


def format_engagements_for_ai(engagements: list, players: list) -> str:
    """Format engagement data for the AI prompt."""
    if not engagements:
        return ""

    # Build pid -> name map
    pid_name = {}
    for i, p in enumerate(players):
        pid_name[i + 1] = p.get("name", f"Player {i+1}")

    lines = ["=== BATTLE TIMELINE (who fought who) ==="]
    for e in engagements:
        t = e.get("time", 0)
        n1 = pid_name.get(e.get("p1", 0), "?")
        n2 = pid_name.get(e.get("p2", 0), "?")
        lines.append(f"  [{t}-{t+3}min] {n1} vs {n2}")

    # Summarize matchups
    from collections import Counter
    matchup_counts = Counter()
    for e in engagements:
        key = (min(e["p1"], e["p2"]), max(e["p1"], e["p2"]))
        matchup_counts[key] += 1

    lines.append("\nMatchup frequency:")
    for (p1, p2), count in matchup_counts.most_common():
        n1, n2 = pid_name.get(p1, "?"), pid_name.get(p2, "?")
        lines.append(f"  {n1} vs {n2}: {count} engagements")

    return "\n".join(lines)
