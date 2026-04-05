"""
AOE2:DE Knowledge Base for LLM Coaching System
================================================
Compact reference (~3500 tokens) covering unit counters, timings,
build orders, economy benchmarks, common mistakes, map tips, and team roles.
Injected into the LLM system prompt for game-specific coaching.
"""

from civ_database import CIV_DATABASE

AOE2_KNOWLEDGE_BASE = """
=== AOE2:DE COACHING KNOWLEDGE BASE ===

== UNIT COUNTER CHART ==
Format: Unit -> [Counters] | Soft counters in ()

Archers (Crossbow/Arbalester):
  Hard: Skirmishers, Huskarls, Eagle Warriors, Rattan Archers
  Soft: Mangonels/Onagers, Cavalry (close gap), Siege Ram (absorb)

Knights (Cavalier/Paladin):
  Hard: Pikemen/Halberdiers, Camels, Genoese Crossbow
  Soft: Monks (conversion), Mamelukes, Heavy Scorpions

Infantry (Militia/Champion line):
  Hard: Archers (kite), Hand Cannoneers, Scorpions, Cataphracts
  Soft: Knights (mobility), Jaguar Warriors, Slingers

Cavalry Archers (HCA):
  Hard: Elite Skirmishers, Eagle Warriors, Genitours
  Soft: Camels (close), Huskarls, Heavy Cavalry (corner)

Siege (Mangonels/Rams/Scorps):
  Hard: Cavalry (melee), Bombard Cannons
  Soft: Monks (convert siege), Infantry rush, opposing Mangonels

Eagles (Eagle Scout/Warrior):
  Hard: Militia line (Champion), Hand Cannoneers, Longswords+
  Soft: Heavy Cavalry, Cataphracts, Boyars

Monks:
  Hard: Light Cavalry/Hussar, Eagles, Scouts
  Soft: Archers (range), massed anything (outnumber)

Camels:
  Hard: Pikemen/Halbs, Archers, Monks
  Soft: Infantry, Militia line

Light Cavalry/Hussar:
  Hard: Pikemen/Halbs, Camels, Knights
  Soft: Town Centers, Castles

War Elephants/Battle Elephants:
  Hard: Pikemen/Halbs (x bonus), Monks (convert)
  Soft: Heavy Scorpions, Camels

Gunpowder (HC/Janissary/Conq):
  Hard: Skirmishers, Onagers (splash), Huskarls
  Soft: Cavalry (close gap), Eagles

Bombard Cannon:
  Hard: Cavalry raid, BBC counter-fire
  Soft: Onagers (close), Siege Ram

Trebuchet:
  Hard: Cavalry raid, Bombard Cannon
  Soft: Trebuchet war, Onager cut

KEY RULE: Always look at what opponent makes -> build counter. Don't commit to one comp.

== TIMING BENCHMARKS BY ELO ==

              <800 ELO    800-1100    1100-1400    1400+
Feudal click: 11:00+      9:30-10:30  8:30-9:30    7:30-8:30
  Pop count:  28+          24-26       22-24        21-23
Castle click: 20:00+      17:00-19:00 15:30-17:00  14:30-16:00
  Pop count:  40+          35-38       30-35        28-33
Imp click:    35:00+      30:00-33:00 27:00-30:00  25:00-28:00

Dark Age: 6 on sheep -> 4 on wood -> 1 lure boar -> 3-4 on berries -> lure 2nd boar
Feudal: Research loom before clicking up. Always queue vills during transition.
Castle: Have 2 TCs running ASAP. Add 3rd TC when safe.

== STANDARD BUILD ORDERS (CONDENSED) ==

22 POP SCOUTS (Feudal aggression):
  6 sheep->4 wood->1 boar->4 berries->1 boar->3 food->2 wood->click Feudal@21+loom
  Feudal: Stable->Scouts, add farms. 2nd lumber camp. Scout opponent.

22 POP ARCHERS (Feudal aggression):
  6 sheep->4 wood->1 boar->4 berries->1 boar->1 food->3 gold->2 wood->Feudal@21+loom
  Feudal: Barracks->Range->Range. Constant Archer production. Add farms.

FAST CASTLE (27+2 boom):
  6 sheep->4 wood->1 boar->4 berries->1 boar->3 food->3 gold->2 wood->Feudal@27+loom
  Feudal: Blacksmith+Market/Stable->Castle. Make Knights or boom with TCs.

TOWER RUSH (Trush):
  Same as archers start. Send 2-3 vills forward with stone at 8:00.
  Feudal: Tower enemy gold/berries/woodline. Deny resources.

DRUSH -> FC:
  6 sheep->4 wood->1 boar->1 berries->loom->Barracks@pop16
  3 Militia rush at 6:30-7:00. Then transition into FC build.

== ECONOMY BENCHMARKS ==

Villager targets:
  Feudal: 22-27 vills (depends on strategy)
  Castle: 35-50 vills (boom), 30-35 (aggression)
  Imperial: 100-120 vills (1v1), 120-140 (team)
  Stop making vills: 120-130 in 1v1, earlier if pop-capped

Farm transitions:
  Start farms at Feudal (after sheep/boar gone). 8-10 farms by mid-Feudal.
  Reseed farms before they expire. Horse Collar before heavy farming.
  Castle: Heavy Bow Saw. Imperial: Crop Rotation last.

Trade setup (team games):
  Start trade in early Imp or late Castle if safe. 20-30 trade carts.
  Pocket player sets up trade. Longest route = more gold.
  Trade replaces gold mining entirely in late game.

Resource ratios (approx):
  Archers: 40% food, 40% gold, 20% wood
  Knights: 50% food, 30% gold, 20% wood
  Boom: 60% food, 30% wood, 10% gold

== COMMON MISTAKES BY ELO ==

<800 ELO:
  - Idle TC (biggest issue - always make villagers!)
  - No build order (practice 1 BO until automatic)
  - No scouting (find sheep, boar, opponent base)
  - Floating resources (if >500, spend it or make more production)
  - Not enough military buildings (need 3+ production buildings)
  - Forgetting Loom, eco upgrades

800-1100 ELO:
  - Bad transitions (archers->xbow upgrade, scouts->knights)
  - Over-committing to failing strategy
  - Late eco upgrades (Double-Bit Axe, Horse Collar)
  - Not walling or walling too late
  - Single TC in Castle Age
  - Poor villager distribution

1100-1400 ELO:
  - Not adapting to opponent's strategy
  - Predictable play (same BO every game)
  - Weak late-game macro (trade, relics, army comp)
  - Bad engagements (fighting under TC, uphill, in choke)
  - Not using unique units when strong
  - Idle military (always be raiding or pressuring)

1400+ ELO:
  - Micro over macro (APM on 5 units while TC idles)
  - Bad trade timing (too late or too early)
  - Not reading the meta/map correctly
  - Overthinking instead of executing clean BO
  - Not punishing opponent's greed
  - Weak siege play in Imperial

== MAP-SPECIFIC TIPS ==

ARABIA (open land map):
  Scout early, wall reactive. Feudal aggression standard.
  Control hills. Watch for Tower rushes. Aggression > boom.
  Best strats: Scouts, Archers, Drush->FC, M@A->Archers

ARENA (fully walled):
  FC is standard. Boom behind walls. Castle drop/push common.
  Monk+Siege or fast Imp strats viable. Relics crucial.
  Best strats: FC->Boom, FC->Monks, Smush, Fast Imp

BLACK FOREST (chokepoint):
  Wall chokes early. Boom to Imp. Onager/SO cuts key.
  Trade is critical. Trash wars late. Control chokepoints.
  Best strats: Boom->Imp push, Onager cut, Trade boom

ISLANDS (water map):
  Dock first. Fire Galleys->War Galleys critical. Fish boom.
  Control water = win. Transport raids. Demo ships vs grouped.
  Best strats: Galley rush, Fish boom, Transport raid

NOMAD (no TC start):
  Find safe TC spot (fish + wood). Scout for resources.
  Dock ASAP for fish. Flexible BO. Expect chaos.
  Best strats: Dock first, TC near fish, adapt

== TEAM GAME ROLES ==

FLANK (positions 1 & 4 in 2v2, outer in 3v3/4v4):
  - Face direct enemy aggression first
  - Play aggressive Feudal (Archers, M@A, Scouts)
  - Wall toward pocket side
  - Communicate with flares when under pressure
  - Best civs: Archer civs (Britons, Mayans, Ethiopians, Vietnamese)

POCKET (positions 2 & 3 in 2v2, inner in 3v3/4v4):
  - Boom safely, reach Castle Age faster
  - Make Knights to help flanks
  - Set up trade route (longest diagonal)
  - Send Knights to whichever flank needs help
  - Best civs: Knight civs (Franks, Lithuanians, Burgundians, Teutons)

COMMUNICATION:
  - Flare your base when attacked (signals "help me")
  - Flare enemy base to coordinate pushes
  - Flare resources to claim them
  - Double-flare = urgent help needed
  - Market tribute if ally is struggling

TRADE:
  - Pocket sets up trade between allied markets
  - Longer route = more gold per trip
  - 20-30 trade carts sustains gold production
  - Protect trade route with walls/castles
  - Trade replaces gold mining in late Imp
"""


# ---------------------------------------------------------------------------
# Civilization matchup data (strengths / weaknesses / key matchup advice)
# ---------------------------------------------------------------------------

# Common alternate names -> canonical CIV_DATABASE keys
_CIV_ALIASES = {
    "Mayans": "Maya",
    "Indians": "Hindustanis",
    "Incas": "Inca",
}


def _normalize_civ(name: str) -> str:
    """Resolve common civ name aliases to canonical CIV_DATABASE keys."""
    return _CIV_ALIASES.get(name, name)


# Compact civ archetype mapping for matchup logic
_CIV_ARCHETYPE = {
    # Archer civs
    "Britons": "archer", "Mayans": "archer", "Vietnamese": "archer",
    "Ethiopians": "archer", "Chinese": "archer", "Maya": "archer",
    "Dravidians": "archer", "Italians": "archer",
    # Cavalry civs
    "Franks": "cavalry", "Lithuanians": "cavalry", "Huns": "cavalry",
    "Burgundians": "cavalry", "Persians": "cavalry", "Magyars": "cavalry",
    "Tatars": "cavalry", "Cumans": "cavalry", "Berbers": "cavalry",
    "Poles": "cavalry",
    # Infantry civs
    "Goths": "infantry", "Japanese": "infantry", "Aztecs": "infantry",
    "Burmese": "infantry", "Vikings": "infantry", "Teutons": "infantry",
    "Celts": "infantry", "Slavs": "infantry", "Bulgarians": "infantry",
    "Romans": "infantry",
    # Camel/anti-cav civs
    "Saracens": "camel", "Hindustanis": "camel", "Gurjaras": "camel",
    "Malians": "camel", "Bengalis": "camel",
    # Unique playstyle civs
    "Mongols": "cavalry_archer", "Turks": "gunpowder", "Spanish": "gunpowder",
    "Koreans": "defensive", "Byzantines": "defensive", "Bohemians": "gunpowder",
    "Khmer": "elephant", "Malay": "elephant",
    "Inca": "infantry", "Sicilians": "infantry",
    "Armenians": "defensive", "Georgians": "cavalry",
    "Jurchens": "cavalry", "Khitans": "cavalry_archer",
    "Shu": "infantry", "Wei": "cavalry", "Wu": "archer",
    "Mapuche": "infantry", "Muisca": "infantry", "Tupi": "archer",
    "Portuguese": "gunpowder",
}

_ARCHETYPE_COUNTERS = {
    "archer":         ("skirmishers, siege, eagle warriors, huskarls",
                       "knights, cavalry archers"),
    "cavalry":        ("pikemen/halbs, camels, monks",
                       "massed archers, heavy scorpions"),
    "infantry":       ("archers, hand cannoneers, scorpions",
                       "knights, cavalry archers"),
    "camel":          ("pikemen/halbs, archers, monks",
                       "massed infantry, heavy cavalry with support"),
    "cavalry_archer": ("elite skirmishers, eagle warriors",
                       "camels, heavy cavalry in tight spaces"),
    "gunpowder":      ("skirmishers, onagers, huskarls",
                       "cavalry raids, eagle warriors"),
    "defensive":      ("siege push, trebuchet, fast imp",
                       "aggressive feudal pressure"),
    "elephant":       ("pikemen/halbs, monks, heavy scorpions",
                       "mass archers, cavalry hit-and-run"),
}


def get_civ_matchup_context(civ1_name: str, civ2_name: str) -> str:
    """Return matchup-specific advice for civ1 vs civ2.

    Returns a compact text block suitable for injection into an LLM prompt.
    civ1 is the player being coached; civ2 is the opponent.
    """
    civ1_name = _normalize_civ(civ1_name)
    civ2_name = _normalize_civ(civ2_name)
    c1 = CIV_DATABASE.get(civ1_name, {})
    c2 = CIV_DATABASE.get(civ2_name, {})

    if not c1 or not c2:
        return f"Matchup data unavailable for {civ1_name} vs {civ2_name}."

    arch1 = _CIV_ARCHETYPE.get(civ1_name, "unknown")
    arch2 = _CIV_ARCHETYPE.get(civ2_name, "unknown")

    lines = [f"=== MATCHUP: {civ1_name} ({c1.get('type','?')}) vs {civ2_name} ({c2.get('type','?')}) ==="]

    # Player civ strengths
    bonuses = c1.get("bonuses", [])
    uu = c1.get("unique_units", [])
    if bonuses:
        lines.append(f"Your bonuses: {'; '.join(bonuses[:3])}")
    if uu:
        lines.append(f"Your unique units: {', '.join(uu)}")

    # Opponent strengths to watch
    opp_bonuses = c2.get("bonuses", [])
    opp_uu = c2.get("unique_units", [])
    if opp_bonuses:
        lines.append(f"Opponent bonuses: {'; '.join(opp_bonuses[:3])}")
    if opp_uu:
        lines.append(f"Opponent unique units: {', '.join(opp_uu)}")

    # Counter advice based on opponent archetype
    if arch2 in _ARCHETYPE_COUNTERS:
        hard, soft = _ARCHETYPE_COUNTERS[arch2]
        lines.append(f"Counter opponent ({arch2} civ): {hard}")
        lines.append(f"Soft counters: {soft}")

    # Tech tree gaps
    missing1 = c1.get("missing_techs", [])
    missing2 = c2.get("missing_techs", [])
    if missing1:
        key_missing = [t for t in missing1 if t in (
            "Halberdier", "Paladin", "Arbalester", "Siege Ram",
            "Bombard Cannon", "Heavy Camel Rider", "Champion",
            "Hussar", "Siege Onager", "Heavy Scorpion"
        )]
        if key_missing:
            lines.append(f"You lack: {', '.join(key_missing[:5])}")
    if missing2:
        key_missing2 = [t for t in missing2 if t in (
            "Halberdier", "Paladin", "Arbalester", "Siege Ram",
            "Bombard Cannon", "Heavy Camel Rider", "Champion",
            "Hussar", "Siege Onager", "Heavy Scorpion"
        )]
        if key_missing2:
            lines.append(f"Opponent lacks: {', '.join(key_missing2[:5])}")

    # Archetype-specific strategy tips
    strategy_tips = {
        ("archer", "cavalry"):  "Wall and mass archers. Add pikes as meatshield. Avoid open engagements.",
        ("archer", "infantry"): "Kite infantry with archers. Keep distance. Avoid melee.",
        ("archer", "camel"):    "Archers are good vs camels. Add pikes if they switch to cavalry.",
        ("cavalry", "archer"):  "Close the gap fast. Raid eco. Don't let archers mass.",
        ("cavalry", "infantry"):"Mobility advantage. Raid and avoid head-on against halbs.",
        ("cavalry", "camel"):   "Avoid direct camel fights. Go archers or infantry switch.",
        ("infantry", "archer"): "Close distance. Use siege/rams to push. Eagles if meso.",
        ("infantry", "cavalry"):"Pikes + siege. Don't chase cavalry. Defend and push.",
        ("cavalry_archer", "archer"): "Outrange and kite. Avoid grouped skirm balls.",
        ("cavalry_archer", "cavalry"): "Hit and run. Don't let them engage. Raid eco.",
        ("gunpowder", "cavalry"): "Mass gunpowder behind walls. Add halbs as meatshield.",
        ("elephant", "archer"):  "Push with siege support. Don't let them kite forever.",
        ("elephant", "cavalry"): "Elephants beat cavalry head-on. Watch for monk conversions.",
    }

    tip = strategy_tips.get((arch1, arch2))
    if tip:
        lines.append(f"Strategy: {tip}")
    else:
        lines.append("Strategy: Scout opponent comp and adapt. Play to your civ strengths.")

    return "\n".join(lines)


def get_player_specific_context(
    civ_name: str,
    elo: int,
    eapm: int,
    game_duration_min: float,
    won: bool,
) -> str:
    """Return ELO-appropriate advice for a player's specific situation.

    Returns a compact text block suitable for injection into an LLM prompt.
    """
    civ_name = _normalize_civ(civ_name)
    lines = []

    # Determine ELO bracket
    if elo < 800:
        bracket = "beginner"
        bracket_label = "<800"
    elif elo < 1100:
        bracket = "intermediate"
        bracket_label = "800-1100"
    elif elo < 1400:
        bracket = "advanced"
        bracket_label = "1100-1400"
    else:
        bracket = "expert"
        bracket_label = "1400+"

    lines.append(f"=== PLAYER CONTEXT: {civ_name} | ELO {elo} ({bracket_label}) | EAPM {eapm} ===")

    # EAPM analysis
    eapm_targets = {
        "beginner": (15, 25),
        "intermediate": (25, 40),
        "advanced": (40, 60),
        "expert": (60, 100),
    }
    low, high = eapm_targets[bracket]
    if eapm < low:
        lines.append(f"EAPM {eapm} is LOW for {bracket_label}. Focus on staying active - "
                      "always be doing something (making vills, scouting, micro).")
    elif eapm > high:
        lines.append(f"EAPM {eapm} is HIGH for {bracket_label}. Good activity, "
                      "but make sure actions are efficient, not spam.")
    else:
        lines.append(f"EAPM {eapm} is appropriate for {bracket_label}.")

    # Game duration analysis
    if game_duration_min < 15:
        lines.append("Short game (<15min). Likely ended in Feudal/early Castle. "
                      "Check if early aggression was decisive or if someone got overwhelmed.")
    elif game_duration_min < 30:
        lines.append("Medium game (15-30min). Standard Castle Age game. "
                      "Check transitions and army composition choices.")
    elif game_duration_min < 45:
        lines.append("Long game (30-45min). Went to Imp. Check trade setup, "
                      "composition switches, and late-game macro.")
    else:
        lines.append("Very long game (45min+). Late Imp trash wars likely. "
                      "Check gold control, relic count, trade, and pop efficiency.")

    # ELO-specific coaching priorities
    priorities = {
        "beginner": [
            "PRIORITY 1: Keep TC producing villagers non-stop",
            "PRIORITY 2: Learn 1 build order (22 pop scouts or archers)",
            "PRIORITY 3: Scout - find your sheep, boar, and opponent",
            "Spend resources - never float above 500 food/wood/gold",
        ],
        "intermediate": [
            "PRIORITY 1: Clean up build order execution (hit timing benchmarks)",
            "PRIORITY 2: Transition smoothly (Feudal->Castle, scouts->knights)",
            "PRIORITY 3: Add TCs in Castle Age and keep all producing",
            "Wall appropriately and get eco upgrades on time",
        ],
        "advanced": [
            "PRIORITY 1: Adapt strategy to opponent's composition",
            "PRIORITY 2: Improve late-game macro (trade, relics, army comp)",
            "PRIORITY 3: Better engagements - fight with advantages (hill, numbers)",
            "Use unique units when your civ is strong with them",
        ],
        "expert": [
            "PRIORITY 1: Optimize execution - tighter build, fewer idle moments",
            "PRIORITY 2: Read the game better - punish greed, adapt faster",
            "PRIORITY 3: Master siege play and late-game army composition",
            "Focus on decision-making, not just mechanics",
        ],
    }

    for p in priorities[bracket]:
        lines.append(p)

    # Win/loss-specific framing
    if won:
        lines.append("RESULT: Won. Identify what went right and how to replicate it. "
                      "Also note any inefficiencies that could be punished at higher ELO.")
    else:
        lines.append("RESULT: Lost. Identify the turning point. Was it eco, military, "
                      "or a strategic mistake? Focus on the earliest fixable error.")

    # Civ-specific tips
    civ_data = CIV_DATABASE.get(civ_name, {})
    civ_type = civ_data.get("type", "")
    if civ_type:
        lines.append(f"Civ type: {civ_type}. Play to this strength in your game plan.")

    return "\n".join(lines)
