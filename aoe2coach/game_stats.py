"""Deep game statistics extractor — processes replay operations for pro-level analysis."""

from collections import defaultdict

# Known unit IDs → names (AOE2:DE)
UNIT_NAMES = {
    4: "Archer", 5: "Hand Cannoneer", 6: "Elite Skirmisher", 7: "Skirmisher",
    8: "Longbowman", 11: "Fishing Ship", 13: "Trade Cart", 17: "Trade Cog",
    21: "Galley", 24: "Crossbowman", 35: "Battering Ram", 36: "Bombard Cannon",
    38: "Knight", 39: "Cavalry Archer", 40: "Cataphract", 41: "Huskarl",
    42: "Trebuchet (Packed)", 46: "Janissary", 73: "Chu Ko Nu", 74: "Militia",
    75: "Man-at-Arms", 76: "Heavy Swordsman", 77: "Long Swordsman",
    83: "Villager", 93: "Spearman", 125: "Monk", 128: "Trade Cart",
    185: "Slinger", 204: "Plumed Archer", 223: "War Elephant",
    232: "Woad Raider", 239: "War Wagon", 250: "Longboat",
    279: "Scorpion", 280: "Onager", 281: "Mangonel", 282: "Heavy Scorpion",
    283: "Transport Ship", 329: "Camel Rider", 331: "Trebuchet",
    358: "Pikeman", 359: "Halberdier", 420: "Cannon Galleon",
    440: "Petard", 441: "Hussar", 442: "Steppe Lancer",
    448: "Scout Cavalry", 473: "Two-Handed Swordsman", 474: "Heavy Camel Rider",
    492: "Arbalester", 527: "Demolition Ship", 529: "Fire Ship",
    531: "Fire Galley", 532: "Elite Longbowman", 534: "Fast Fire Ship",
    539: "Cavalier", 546: "War Galley", 548: "Galleon",
    550: "Capped Ram", 553: "Elite Cataphract", 554: "Elite Huskarl",
    555: "Elite Janissary", 557: "Elite Chu Ko Nu",
    567: "Elite Mangudai", 569: "Champion", 588: "Siege Ram",
    691: "Elite War Elephant", 725: "Paladin", 751: "Eagle Warrior",
    753: "Elite Eagle Warrior", 755: "Elite Plumed Archer",
    763: "Elite Woad Raider", 771: "Elite War Wagon",
    827: "Ballista Elephant", 831: "Karambit Warrior",
    866: "Condottiero", 873: "Imperial Skirmisher",
    879: "Elite Ballista Elephant", 886: "Elite Steppe Lancer",
    1007: "Coustillier", 1013: "Serjeant", 1016: "Flemish Militia",
    1120: "Elite Ballista Elephant", 1225: "Dromon",
    1228: "Savar", 1231: "Composite Bowman", 1233: "Monaspa",
    1258: "Ghulam", 1263: "Shrivamsha Rider", 1755: "Camel Scout",
}

# Key tech IDs → names
TECH_NAMES = {
    22: "Loom", 65: "Wheelbarrow", 219: "Hand Cart",
    # Ages
    100: "Feudal Age", 101: "Castle Age", 102: "Imperial Age",
    # Eco
    199: "Double-Bit Axe", 200: "Bow Saw", 201: "Two-Man Saw",
    202: "Horse Collar", 203: "Heavy Plow", 204: "Crop Rotation",
    182: "Gold Mining", 213: "Gold Shaft Mining",
    8: "Town Watch", 254: "Town Patrol",
    # Blacksmith - Melee
    14: "Forging", 15: "Iron Casting", 76: "Blast Furnace",
    # Blacksmith - Melee Armor
    17: "Scale Mail Armor", 83: "Chain Mail Armor", 82: "Plate Mail Armor",
    # Blacksmith - Cavalry Armor
    80: "Chain Barding Armor", 81: "Plate Barding Armor",
    # Blacksmith - Archer
    13: "Fletching", 23: "Bodkin Arrow",
    54: "Padded Archer Armor", 55: "Leather Archer Armor", 68: "Ring Archer Armor",
    # Military upgrades
    67: "Squires", 39: "Husbandry", 315: "Bloodlines", 316: "Parthian Tactics",
    319: "Thumb Ring", 48: "Ballistics", 47: "Chemistry",
    50: "Siege Engineers", 252: "Conscription",
    # Unit upgrades
    74: "Long Swordsman", 75: "Cavalier", 209: "Halberdier",
    211: "Champion", 212: "Paladin", 215: "Arbalester",
    217: "Heavy Cavalry Archer", 236: "Onager", 237: "Siege Ram",
    239: "Heavy Scorpion",
    # Monk
    231: "Sanctity", 230: "Block Printing", 221: "Fervor",
    232: "Illumination", 45: "Faith", 321: "Theocracy", 322: "Heresy",
    # Other
    360: "Arson", 373: "Supplies", 428: "Gambesons",
    380: "Steppe Husbandry", 188: "Coinage", 194: "Caravan",
    249: "Sappers", 12: "Masonry",
}

# Unit categories for analysis
UNIT_CATEGORIES = {
    "Villager": [83],
    "Infantry": [74, 75, 76, 77, 93, 358, 359, 473, 569, 751, 753, 866],
    "Archer": [4, 7, 6, 24, 492, 5, 873],
    "Cavalry": [38, 448, 539, 725, 441, 442, 886],
    "Cavalry Archer": [39, 217],
    "Camel": [329, 474, 1755],
    "Siege": [35, 279, 280, 281, 282, 36, 331, 42, 440, 550, 588],
    "Monk": [125],
    "Naval": [11, 17, 21, 283, 420, 527, 529, 531, 534, 546, 548],
    "Trade": [13, 128, 17],
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
