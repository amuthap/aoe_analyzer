"""
Complete AOE2:DE Civilization Database
======================================
Scraped from the Age of Empires Series Wiki (ageofempires.fandom.com).
All civilizations as of April 2026, including:
  - Battle for Greece DLC (Nov 2024): Achaemenids, Athenians, Spartans
  - Three Kingdoms DLC (May 2025): Wu, Wei, Jurchens, Khitans, Shu
  - Alexander the Great DLC (Oct 2025): Macedonians, Thracians, Puru
  - The Last Chieftains DLC (Feb 2026): Mapuche, Muisca, Tupi
  - Chinese rework (Feb 2026), Inca rework (Feb 2026)

Civilization IDs verified against aoe2companion API (April 2026).
IDs 46-49 and 55-57 are reserved for Chronicles/campaign-only civs
and do not appear in standard multiplayer replays.
"""

# Internal civilization IDs (used in replay files and scenario editor)
# Verified by cross-referencing parsed replays against aoe2companion API
CIV_IDS = {
    1: "Britons",
    2: "Franks",
    3: "Goths",
    4: "Teutons",
    5: "Japanese",
    6: "Chinese",
    7: "Byzantines",
    8: "Persians",
    9: "Saracens",
    10: "Turks",
    11: "Vikings",
    12: "Mongols",
    13: "Celts",
    14: "Spanish",
    15: "Aztecs",
    16: "Maya",
    17: "Huns",
    18: "Koreans",
    19: "Italians",
    20: "Hindustanis",  # formerly Indians
    21: "Inca",
    22: "Magyars",
    23: "Slavs",
    24: "Portuguese",
    25: "Ethiopians",
    26: "Malians",
    27: "Berbers",
    28: "Khmer",
    29: "Malay",
    30: "Burmese",      # swapped with Vietnamese in recent patch
    31: "Vietnamese",   # verified via aoe2companion API
    32: "Lithuanians",
    33: "Bulgarians",
    34: "Cumans",
    35: "Tatars",
    36: "Burgundians",
    37: "Sicilians",
    38: "Poles",         # swapped with Bohemians; verified via API + Obuch UU
    39: "Bohemians",    # verified via API (KING STEVE plays Bohemians at id 39)
    40: "Dravidians",
    41: "Bengalis",
    42: "Gurjaras",
    43: "Romans",
    44: "Armenians",
    45: "Georgians",
    # 46-49: Reserved for Chronicles/campaign civs (Battle for Greece, etc.)
    50: "Wu",           # Three Kingdoms DLC - verified
    51: "Wei",          # Three Kingdoms DLC - verified via API (3 games)
    52: "Jurchens",     # Three Kingdoms DLC - verified via API (2 games)
    53: "Khitans",      # Three Kingdoms DLC - inferred from DLC order
    54: "Shu",          # Three Kingdoms DLC - inferred from DLC order
    # 55-57: Reserved for Chronicles/campaign civs (Alexander the Great, etc.)
    58: "Mapuche",      # Last Chieftains DLC - verified via API
    59: "Tupi",         # Last Chieftains DLC - verified via API (2 games)
    60: "Muisca",       # Last Chieftains DLC - inferred from DLC order
}

# Reverse lookup: name -> ID
CIV_NAME_TO_ID = {v: k for k, v in CIV_IDS.items()}

# Expansion / DLC each civilization was introduced in
CIV_EXPANSION = {
    "Britons": "The Age of Kings",
    "Franks": "The Age of Kings",
    "Goths": "The Age of Kings",
    "Teutons": "The Age of Kings",
    "Japanese": "The Age of Kings",
    "Chinese": "The Age of Kings",
    "Byzantines": "The Age of Kings",
    "Persians": "The Age of Kings",
    "Saracens": "The Age of Kings",
    "Turks": "The Age of Kings",
    "Vikings": "The Age of Kings",
    "Mongols": "The Age of Kings",
    "Celts": "The Age of Kings",
    "Spanish": "The Conquerors",
    "Aztecs": "The Conquerors",
    "Maya": "The Conquerors",
    "Huns": "The Conquerors",
    "Koreans": "The Conquerors",
    "Italians": "The Forgotten",
    "Hindustanis": "The Forgotten",  # originally Indians, renamed in Dynasties of India
    "Inca": "The Forgotten",
    "Magyars": "The Forgotten",
    "Slavs": "The Forgotten",
    "Portuguese": "The African Kingdoms",
    "Ethiopians": "The African Kingdoms",
    "Malians": "The African Kingdoms",
    "Berbers": "The African Kingdoms",
    "Khmer": "Rise of the Rajas",
    "Malay": "Rise of the Rajas",
    "Vietnamese": "Rise of the Rajas",
    "Burmese": "Rise of the Rajas",
    "Lithuanians": "The Last Khans",
    "Bulgarians": "The Last Khans",
    "Cumans": "The Last Khans",
    "Tatars": "The Last Khans",
    "Burgundians": "Lords of the West",
    "Sicilians": "Lords of the West",
    "Bohemians": "Dawn of the Dukes",
    "Poles": "Dawn of the Dukes",
    "Dravidians": "Dynasties of India",
    "Bengalis": "Dynasties of India",
    "Gurjaras": "Dynasties of India",
    "Romans": "Return of Rome",
    "Armenians": "The Mountain Royals",
    "Georgians": "The Mountain Royals",
    "Jurchens": "The Three Kingdoms",
    "Khitans": "The Three Kingdoms",
    "Shu": "The Three Kingdoms",
    "Wei": "The Three Kingdoms",
    "Wu": "The Three Kingdoms",
    "Mapuche": "The Last Chieftains",
    "Muisca": "The Last Chieftains",
    "Tupi": "The Last Chieftains",
}

# ──────────────────────────────────────────────────────────────────────
# Full civilization database
# ──────────────────────────────────────────────────────────────────────

CIV_DATABASE = {
    # ── The Age of Kings (base game) ──────────────────────────────────

    "Britons": {
        "id": 1,
        "type": "Foot Archer",
        "expansion": "The Age of Kings",
        "unique_units": ["Longbowman"],
        "unique_techs": [
            "Yeomen: Foot archers +1 range; towers +2 attack.",
            "Warwolf: Trebuchets do blast damage."
        ],
        "bonuses": [
            "Town Centers cost -50% wood upon reaching the Castle Age.",
            "Archery Ranges work 20% faster (except Bohemians' Archery Range).",
            "Shepherds work 25% faster.",
            "Foot archers (except Skirmishers) +1/+2 range in Castle/Imperial Age."
        ],
        "team_bonus": "Archery Ranges work 10% faster.",
        "tip": "Mass crossbows in Castle, transition to longbows in Imp. Keep distance, never let cavalry close.",
        "meta_tier": "A",
    },

    "Franks": {
        "id": 2,
        "type": "Cavalry",
        "expansion": "The Age of Kings",
        "unique_units": ["Throwing Axeman"],
        "unique_techs": [
            "Bearded Axe: Throwing Axemen +1 range.",
            "Chivalry: Stables work 40% faster."
        ],
        "bonuses": [
            "Farm upgrades are free.",
            "Castles are 15%/25% cheaper in the Castle/Imperial Age.",
            "Mounted units have +20% hit points (starting in the Feudal Age).",
            "Foragers work 15% faster."
        ],
        "team_bonus": "Knights have +2 Line of Sight.",
        "tip": "Power spike in Castle Age with knights. Get 3 TCs and mass knights. Cheap castles = map control.",
        "meta_tier": "A",
    },

    "Goths": {
        "id": 3,
        "type": "Infantry",
        "expansion": "The Age of Kings",
        "unique_units": ["Huskarl"],
        "unique_techs": [
            "Anarchy: Huskarls can be created at Barracks.",
            "Perfusion: Barracks work 100% faster."
        ],
        "bonuses": [
            "Infantry units are 15%/20%/25%/30% cheaper in Dark/Feudal/Castle/Imperial Age.",
            "Infantry have +1/+2/+3 attack vs standard buildings in Feudal/Castle/Imperial Age.",
            "Villagers have +5 attack vs wild boar; carry +15 food from hunted animals.",
            "Population cap +10 in the Imperial Age.",
            "Loom is free."
        ],
        "team_bonus": "Barracks work 20% faster.",
        "tip": "Survive to Imperial and flood with huskarls + champions. You outproduce everyone late game.",
        "meta_tier": "B",
    },

    "Teutons": {
        "id": 4,
        "type": "Infantry and Siege",
        "expansion": "The Age of Kings",
        "unique_units": ["Teutonic Knight"],
        "unique_techs": [
            "Ironclad: Gives siege weapons +4 melee armor.",
            "Crenellations: Gives Castles +3 range and makes garrisoned infantry shoot arrows."
        ],
        "bonuses": [
            "Monks have double healing range.",
            "Towers garrison twice as many units.",
            "Murder Holes and Herbal Medicine are free.",
            "Farms are 40% cheaper.",
            "Town Centers can garrison +10 units.",
            "Barracks and Stable units receive +1/+2 melee armor in the Castle/Imperial Age."
        ],
        "team_bonus": "Units resist conversion (+3 min, +1 max conversion time).",
        "tip": "Slow but powerful. Wall up, boom, and push with Teutonic Knights + siege. Your farms are dirt cheap.",
        "meta_tier": "B",
    },

    "Japanese": {
        "id": 5,
        "type": "Infantry",
        "expansion": "The Age of Kings",
        "unique_units": ["Samurai"],
        "unique_techs": [
            "Yasama: Towers fire extra arrows.",
            "Kataparuto: Trebuchets fire and pack faster."
        ],
        "bonuses": [
            "Fishing Ships have double hit points, +2 pierce armor, and work 5%/10%/15%/20% faster in the Dark/Feudal/Castle/Imperial Age.",
            "Mill, Lumber Camp, and Mining Camp cost -50% wood.",
            "Infantry attack 33% faster starting in the Feudal Age."
        ],
        "team_bonus": "Galleys have +50% Line of Sight.",
        "tip": "Your infantry attack 33% faster. Samurai counter unique units. Trebuchets pack faster for mobility.",
        "meta_tier": "B",
    },

    "Chinese": {
        "id": 6,
        "type": "Archer and Gunpowder",
        "expansion": "The Age of Kings",
        "unique_units": ["Chu Ko Nu", "Dragon Ship"],
        "unique_techs": [
            "Great Wall: Increases the hit points of walls and towers by +30%.",
            "Rocketry: Scorpions, Rocket Carts, Lou Chuans +25% attack. Lou Chuans fire rockets with AoE damage."
        ],
        "bonuses": [
            "Start game with +3 Villagers, but with -200 food, -50 wood.",
            "Town Centers support 15 population (instead of 5) and have +7 Line of Sight.",
            "Technologies are 5%/10%/15% cheaper in the Feudal/Castle/Imperial Age, respectively.",
            "Fire Galley-line and Fire Lancers move 5%/10% faster in the Castle/Imperial Ages, respectively."
        ],
        "team_bonus": "Farms and Pastures contain +10% food.",
        "tip": "Tough start with fewer resources. Once stable, excellent tech tree. Chu Ko Nu shreds. Dragon Ships dominate water.",
        "meta_tier": "A",
    },

    "Byzantines": {
        "id": 7,
        "type": "Defensive",
        "expansion": "The Age of Kings",
        "unique_units": ["Cataphract"],
        "unique_techs": [
            "Greek Fire: Fire Ships +1 range.",
            "Logistica: Cataphracts deal trample damage and get +6 vs infantry."
        ],
        "bonuses": [
            "Buildings (except Gates, Palisades, Farms, Fish Traps, and Walls) have +10%/+20%/+30%/+40% hit points in the Dark/Feudal/Castle/Imperial Age.",
            "Camel Riders, Skirmishers, and the Spearman line are 25% cheaper.",
            "Fire Ships attack 25% faster.",
            "Advancing to the Imperial Age is 33% cheaper.",
            "Town Watch and Town Patrol are free."
        ],
        "team_bonus": "Monks heal 100% faster.",
        "tip": "Jack-of-all-trades civ. Counter whatever your opponent does. Cataphracts destroy infantry and halbs.",
        "meta_tier": "B",
    },

    "Persians": {
        "id": 8,
        "type": "Cavalry",
        "expansion": "The Age of Kings",
        "unique_units": ["War Elephant", "Savar"],
        "unique_techs": [
            "Kamandaran: Archer-line cost changed from 25 wood, 45 gold to 50 wood.",
            "Citadels: Castles +4 attack, +3 against Rams, +3 against Infantry, and receive -25% bonus damage."
        ],
        "bonuses": [
            "Start the game with +50 food, +50 wood.",
            "Town Centers and Docks have double hit points and work 5%/10%/15%/20% faster in the Dark/Feudal/Castle/Imperial Age.",
            "Parthian Tactics available in the Castle Age.",
            "Can build Caravanserais in the Imperial Age."
        ],
        "team_bonus": "Knights have +2 attack vs archers.",
        "tip": "Your TC works faster per age - huge eco advantage. Knights in Castle, War Elephants to close out games.",
        "meta_tier": "B",
    },

    "Saracens": {
        "id": 9,
        "type": "Camel and Naval",
        "expansion": "The Age of Kings",
        "unique_units": ["Mameluke"],
        "unique_techs": [
            "Bimaristan: Monks heal 2x speed and can heal siege too.",
            "Counterweights: Trebuchets and Mangonel-line +15% attack."
        ],
        "bonuses": [
            "The Market trade fee is only 5%.",
            "Transport Ships have double hit points and +5 carry capacity.",
            "Galleys attack 25% faster.",
            "Camel units have +10 hit points."
        ],
        "team_bonus": "Foot archers have +3 attack vs standard buildings.",
        "tip": "Market abuse for flexible economy. Mamelukes counter cavalry. Strong camel + siege composition.",
        "meta_tier": "B",
    },

    "Turks": {
        "id": 10,
        "type": "Gunpowder",
        "expansion": "The Age of Kings",
        "unique_units": ["Janissary"],
        "unique_techs": [
            "Sipahi: Cavalry Archers +20 hit points.",
            "Artillery: Bombard Towers, Bombard Cannons, and Cannon Galleons +2 range."
        ],
        "bonuses": [
            "Gunpowder units have +25% hit points.",
            "Gold miners work 20% faster.",
            "Chemistry is free.",
            "Light Cavalry and Hussar upgrades are free.",
            "Scout Cavalry line +1 pierce armor."
        ],
        "team_bonus": "Gunpowder units are created 25% faster.",
        "tip": "Free chemistry saves 300f 200g. Janissaries + Bombard Cannons push is devastating. Gold-heavy though.",
        "meta_tier": "B",
    },

    "Vikings": {
        "id": 11,
        "type": "Infantry and Naval",
        "expansion": "The Age of Kings",
        "unique_units": ["Berserk", "Longboat"],
        "unique_techs": [
            "Chieftains: Infantry have attack bonus vs cavalry and camels.",
            "Berserkergang: Berserks regenerate faster."
        ],
        "bonuses": [
            "Warships are 15%/15%/20% cheaper in the Feudal/Castle/Imperial Age.",
            "Infantry have +20% hit points starting in the Feudal Age.",
            "Wheelbarrow and Hand Cart are free."
        ],
        "team_bonus": "Docks are 15% cheaper.",
        "tip": "Massive eco advantage from free Wheelbarrow + Hand Cart. Berserks are tanky. Dominant on water maps.",
        "meta_tier": "A",
    },

    "Mongols": {
        "id": 12,
        "type": "Mounted Archer",
        "expansion": "The Age of Kings",
        "unique_units": ["Mangudai"],
        "unique_techs": [
            "Nomads: Houses retain population when destroyed.",
            "Drill: Siege Workshop units move 50% faster."
        ],
        "bonuses": [
            "Cavalry Archers fire 25% faster.",
            "Light Cavalry and Hussar +30% hit points.",
            "Hunters work 40% faster.",
            "Scout Cavalry, Light Cavalry, and Hussar have +2 Line of Sight."
        ],
        "team_bonus": "Scout Cavalry line +2 Line of Sight.",
        "tip": "Mangudai are game-ending. Fast hunt bonus = faster uptime. Drill siege rams are devastating.",
        "meta_tier": "S",
    },

    "Celts": {
        "id": 13,
        "type": "Infantry and Siege",
        "expansion": "The Age of Kings",
        "unique_units": ["Woad Raider"],
        "unique_techs": [
            "Stronghold: Castles and towers fire 33% faster.",
            "Furor Celtica: Siege Workshop units +40% hit points."
        ],
        "bonuses": [
            "Infantry move 15% faster starting in the Feudal Age.",
            "Lumberjacks work 15% faster.",
            "Siege weapons fire 25% faster.",
            "Herdables cannot be stolen (unless garrisoned by another player or converted)."
        ],
        "team_bonus": "Siege Workshops work 20% faster.",
        "tip": "Fast infantry and devastating siege. Lumberjack bonus is huge for early eco. Woad Raiders raid relentlessly.",
        "meta_tier": "B",
    },

    # ── The Conquerors ────────────────────────────────────────────────

    "Spanish": {
        "id": 14,
        "type": "Gunpowder and Monk",
        "expansion": "The Conquerors",
        "unique_units": ["Conquistador", "Missionary"],
        "unique_techs": [
            "Inquisition: Monks convert faster.",
            "Supremacy: Villagers become much stronger in combat."
        ],
        "bonuses": [
            "Builders work 30% faster.",
            "Blacksmith upgrades cost no gold.",
            "Cannon Galleons benefit from Ballistics (and fire faster).",
            "Trade units generate +25% gold."
        ],
        "team_bonus": "Trade units generate +25% gold.",
        "tip": "Conquistadors are mobile gunpowder cavalry. Trade bonus is huge in team games. Missionaries are fast monks.",
        "meta_tier": "B",
    },

    "Aztecs": {
        "id": 15,
        "type": "Infantry and Monk",
        "expansion": "The Conquerors",
        "unique_units": ["Jaguar Warrior"],
        "unique_techs": [
            "Atlatl: Skirmishers +1 attack and range.",
            "Garland Wars: Infantry +4 attack."
        ],
        "bonuses": [
            "Start the game with an Eagle Scout.",
            "Villagers carry +3 extra resources.",
            "All military units are created 15% faster.",
            "Monks gain 5 HP for every researched Monastery technology.",
            "Start with +50 gold."
        ],
        "team_bonus": "Relics generate +33% gold.",
        "tip": "Fast monks + eagles in Castle Age. Grab relics ASAP for gold income. Jaguar Warriors counter infantry.",
        "meta_tier": "A",
    },

    "Maya": {
        "id": 16,
        "type": "Foot Archer",
        "expansion": "The Conquerors",
        "unique_units": ["Plumed Archer"],
        "unique_techs": [
            "Hul'che Javelineers: Skirmishers throw a secondary projectile.",
            "El Dorado: Eagle Warriors have +40 hit points."
        ],
        "bonuses": [
            "Start the game with an Eagle Scout.",
            "Resources last 15% longer.",
            "Start with +1 Villager but -50 food.",
            "Archer line is 10%/20%/30% cheaper in the Feudal/Castle/Imperial Age."
        ],
        "team_bonus": "Walls are 50% cheaper.",
        "tip": "Plume archers are your power unit. Extra resources early = faster uptime. Eagles raid gold.",
        "meta_tier": "A",
    },

    "Huns": {
        "id": 17,
        "type": "Cavalry",
        "expansion": "The Conquerors",
        "unique_units": ["Tarkan"],
        "unique_techs": [
            "Marauders: Tarkans can be created at Stables.",
            "Atheism: +100 years for Relic/Wonder victories."
        ],
        "bonuses": [
            "Do not need Houses (but start with -100 wood).",
            "Cavalry Archers are 10%/20% cheaper in the Castle/Imperial Age.",
            "Trebuchets are 30% more accurate.",
            "Stables work 20% faster."
        ],
        "team_bonus": "Stables work 20% faster.",
        "tip": "No houses = perfect build order every time. Scouts into CA is the classic play. Very aggressive civ.",
        "meta_tier": "B",
    },

    "Koreans": {
        "id": 18,
        "type": "Defensive and Naval",
        "expansion": "The Conquerors",
        "unique_units": ["War Wagon", "Turtle Ship"],
        "unique_techs": [
            "Eupseong: Watch Towers, Guard Towers, and Keeps +2 range.",
            "Shinkichon: Mangonel-line +1 range."
        ],
        "bonuses": [
            "Villagers +3 Line of Sight.",
            "Stone Miners work 20% faster.",
            "Guard Tower and Keep upgrades are free.",
            "Military units (except Siege) cost -20% wood.",
            "Archer armor upgrades are free."
        ],
        "team_bonus": "Mangonel-line minimum range removed.",
        "tip": "War Wagons are mobile tanks with range. Tower rush is a classic Korean strategy. Strong on water.",
        "meta_tier": "B",
    },

    # ── The Forgotten ─────────────────────────────────────────────────

    "Italians": {
        "id": 19,
        "type": "Foot Archers and Navy",
        "expansion": "The Forgotten",
        "unique_units": ["Genoese Crossbowman", "Condottiero"],
        "unique_techs": [
            "Silk Road: Halves trade units' cost.",
            "Pirotechnia: Hand Cannoneers are more accurate and deal pass-through damage."
        ],
        "bonuses": [
            "Advancing to the next Age is 15% cheaper.",
            "Foot archers (except Skirmishers) and Condottieri +1/+1 armor.",
            "Dock and University technologies are 25% cheaper.",
            "Fishing Ships are 15% cheaper."
        ],
        "team_bonus": "Condottiero available at Barracks in the Imperial Age.",
        "tip": "Genoese Crossbowmen shred cavalry. Cheaper age-ups give timing advantage. Condottiero counters gunpowder.",
        "meta_tier": "B",
    },

    "Hindustanis": {
        "id": 20,
        "type": "Camel and Gunpowder",
        "expansion": "The Forgotten",
        "unique_units": ["Ghulam"],
        "unique_techs": [
            "Grand Trunk Road: All gold income +10%.",
            "Shatagni: Hand Cannoneers +2 range."
        ],
        "bonuses": [
            "Villagers cost -5%/10%/15%/20% in the Dark/Feudal/Castle/Imperial Age.",
            "Camel Riders attack 20% faster.",
            "Gunpowder units +1/+1 armor.",
            "Can build Caravanserais in the Imperial Age."
        ],
        "team_bonus": "Camel and Light Cavalry units +2 attack vs standard buildings.",
        "tip": "Ghulams counter archers. Camels attack faster = cavalry counter. Caravanserai heals and shields trade.",
        "meta_tier": "A",
    },

    "Inca": {
        "id": 21,
        "type": "Infantry",
        "expansion": "The Forgotten",
        "unique_units": ["Kamayuk", "Slinger"],
        "unique_techs": [
            "Andean Sling: Slingers +1 attack and removes the minimum range from Slingers and Skirmishers.",
            "Fabric Shields: Gives Champi Warriors, Kamayuks, and Slingers +1/+1 armor."
        ],
        "bonuses": [
            "Military units cost -5%/-10%/-15%/-20% food in Dark/Feudal/Castle/Imperial Ages.",
            "Villagers benefit from Blacksmith infantry technologies starting in the Castle Age.",
            "Houses and Settlements support 10 population.",
            "Buildings cost -15% stone."
        ],
        "team_bonus": "Farms are built 100% faster.",
        "tip": "Kamayuks counter cavalry with long reach. Slingers counter infantry. Cheap military food costs. Reworked Feb 2026.",
        "meta_tier": "B",
    },

    "Magyars": {
        "id": 22,
        "type": "Cavalry",
        "expansion": "The Forgotten",
        "unique_units": ["Magyar Huszar"],
        "unique_techs": [
            "Corvinian Army: Magyar Huszars cost no gold.",
            "Recurve Bow: Cavalry Archers +1 range and +1 attack."
        ],
        "bonuses": [
            "Forging, Iron Casting, and Blast Furnace are free.",
            "Scout Cavalry line costs -15% in Castle and Imperial Age.",
            "Villagers kill wild animals in one strike."
        ],
        "team_bonus": "Foot archers +2 Line of Sight.",
        "tip": "Free Blacksmith attack upgrades save huge resources. Magyar Huszar is a gold-free raider. Scout rush king.",
        "meta_tier": "A",
    },

    "Slavs": {
        "id": 23,
        "type": "Infantry and Siege",
        "expansion": "The Forgotten",
        "unique_units": ["Boyar"],
        "unique_techs": [
            "Detinets: Replaces 40% of Castle and tower stone cost with wood.",
            "Druzhina: Infantry do trample damage."
        ],
        "bonuses": [
            "Farmers work 10% faster.",
            "Supplies is free.",
            "Siege Workshop units are 15% cheaper."
        ],
        "team_bonus": "Military buildings (except Castles and Docks) provide +5 population.",
        "tip": "Farmers are faster = strong eco. Boyars have high melee armor. Druzhina makes infantry splash damage.",
        "meta_tier": "B",
    },

    # ── The African Kingdoms ──────────────────────────────────────────

    "Portuguese": {
        "id": 24,
        "type": "Naval and Gunpowder",
        "expansion": "The African Kingdoms",
        "unique_units": ["Organ Gun", "Caravel"],
        "unique_techs": [
            "Carrack: Ships +1/+1 armor.",
            "Arquebus: Gunpowder units are more accurate (ballistics-like)."
        ],
        "bonuses": [
            "All units cost -20% gold.",
            "Ships +10% hit points.",
            "Can build Feitorias (unlimited slow resource trickle) in the Imperial Age.",
            "Technologies are researched 25% faster in the Dock."
        ],
        "team_bonus": "Line of Sight is shared with allies from the start of the game.",
        "tip": "20% gold discount on everything is massive. Organ Guns shred infantry. Feitorias for late-game resources.",
        "meta_tier": "B",
    },

    "Ethiopians": {
        "id": 25,
        "type": "Foot Archer",
        "expansion": "The African Kingdoms",
        "unique_units": ["Shotel Warrior"],
        "unique_techs": [
            "Royal Heirs: Shotels and Camel units receive -3 damage from mounted units.",
            "Torsion Engines: Increases the blast radius of Siege Workshop units."
        ],
        "bonuses": [
            "The Archer line fires 18% faster.",
            "Receive +100 food, +100 gold whenever a new Age is reached.",
            "The Pikeman upgrade is free."
        ],
        "team_bonus": "Outposts +3 Line of Sight and stone cost removed.",
        "tip": "Archers fire 18% faster - devastating crossbow timing. Free resources on age up. Free Pikeman upgrade.",
        "meta_tier": "A",
    },

    "Malians": {
        "id": 26,
        "type": "Infantry",
        "expansion": "The African Kingdoms",
        "unique_units": ["Gbeto"],
        "unique_techs": [
            "Tigui: Town Centers fire arrows without garrisoned units.",
            "Farimba: Cavalry +5 attack."
        ],
        "bonuses": [
            "Buildings cost -15% wood.",
            "Barracks units have +1/+2/+3 pierce armor in the Feudal/Castle/Imperial Age.",
            "Gold mines last 30% longer."
        ],
        "team_bonus": "Universities work 80% faster.",
        "tip": "Infantry with +3 pierce armor shrug off arrows. Gbeto are ranged infantry raiders. Wood savings from buildings.",
        "meta_tier": "A",
    },

    "Berbers": {
        "id": 27,
        "type": "Cavalry and Naval",
        "expansion": "The African Kingdoms",
        "unique_units": ["Camel Archer", "Genitour"],
        "unique_techs": [
            "Kasbah: Team Castles work 25% faster.",
            "Maghreb Camels: Camel units regenerate."
        ],
        "bonuses": [
            "Villagers move 10% faster.",
            "Stable units are 15%/20% cheaper in the Castle/Imperial Age.",
            "Ships move 10% faster."
        ],
        "team_bonus": "Genitours are available at the Archery Range starting in the Castle Age.",
        "tip": "Cheaper stable units (15/20% discount). Camel Archers are excellent vs. other archer civs. Strong on open maps.",
        "meta_tier": "A",
    },

    # ── Rise of the Rajas ─────────────────────────────────────────────

    "Khmer": {
        "id": 28,
        "type": "Siege and Elephant",
        "expansion": "Rise of the Rajas",
        "unique_units": ["Ballista Elephant"],
        "unique_techs": [
            "Tusk Swords: Battle Elephants +3 attack.",
            "Double Crossbow: Ballista Elephants and Scorpions fire two projectiles."
        ],
        "bonuses": [
            "No building requirements to advance Ages or build structures.",
            "Battle Elephants move 10% faster.",
            "Villagers can garrison in Houses.",
            "Farmers do not need to drop off food."
        ],
        "team_bonus": "Scorpions have +1 range.",
        "tip": "No building requirements = flexible builds (skip barracks!). Scorpions are deadly. Ballista Elephants are unique.",
        "meta_tier": "A",
    },

    "Malay": {
        "id": 29,
        "type": "Infantry and Naval",
        "expansion": "Rise of the Rajas",
        "unique_units": ["Karambit Warrior"],
        "unique_techs": [
            "Thalassocracy: Docks are upgraded to Harbors, which shoot arrows.",
            "Forced Levy: Militia line costs no gold."
        ],
        "bonuses": [
            "Advancing to Ages is 66% faster.",
            "Fish Traps cost -33% and provide unlimited food.",
            "Battle Elephants are 30%/40% cheaper in the Castle/Imperial Age.",
            "Docks have double Line of Sight."
        ],
        "team_bonus": "Docks have double Line of Sight.",
        "tip": "Age up 66% faster! Rush to Castle/Imperial before your opponent. Forced Levy = free trash two-handed swordsmen.",
        "meta_tier": "B",
    },

    "Vietnamese": {
        "id": 30,
        "type": "Archer",
        "expansion": "Rise of the Rajas",
        "unique_units": ["Rattan Archer"],
        "unique_techs": [
            "Chatras: Battle Elephants +100 hit points.",
            "Paper Money: Tributes 500 gold to each ally."
        ],
        "bonuses": [
            "Reveal enemy Town Center locations at the start of the game.",
            "Archery Range units have +20% hit points.",
            "Economic upgrades cost no wood.",
            "Conscription is free."
        ],
        "team_bonus": "Imperial Skirmisher upgrade available.",
        "tip": "You see enemy TC at game start - scout is less critical. Rattan Archers tank arrow fire. Paper Money helps allies.",
        "meta_tier": "B",
    },

    "Burmese": {
        "id": 31,
        "type": "Infantry and Cavalry",
        "expansion": "Rise of the Rajas",
        "unique_units": ["Arambai"],
        "unique_techs": [
            "Howdah: Battle Elephants +1/+1 armor.",
            "Manipur Cavalry: Cavalry and Arambai +3 attack vs archers."
        ],
        "bonuses": [
            "Free Lumber Camp upgrades.",
            "Infantry +1/+2/+3 attack in the Feudal/Castle/Imperial Age.",
            "Monastery technologies cost -50%."
        ],
        "team_bonus": "Relics are visible on the map from the game start.",
        "tip": "Free lumber camp techs boost early eco. Arambai hit hard but inaccurately. Monks with cheap monastery techs.",
        "meta_tier": "B",
    },

    # ── The Last Khans ────────────────────────────────────────────────

    "Lithuanians": {
        "id": 32,
        "type": "Cavalry and Monk",
        "expansion": "The Last Khans",
        "unique_units": ["Leitis", "Winged Hussar"],
        "unique_techs": [
            "Hill Forts: Town Centers +3 range.",
            "Tower Shields: Spearman-line and Skirmishers +2 pierce armor."
        ],
        "bonuses": [
            "Start the game with +150 food.",
            "Spearman-line and Skirmishers move 10% faster.",
            "Each Garrisoned Relic gives Knights and Leitis +1 attack (max +4).",
            "Monastery works 20% faster."
        ],
        "team_bonus": "Monastery works 20% faster.",
        "tip": "COLLECT RELICS! Each relic adds +1 attack to your knights (up to +4). Leitis ignore armor entirely.",
        "meta_tier": "A",
    },

    "Bulgarians": {
        "id": 33,
        "type": "Infantry and Cavalry",
        "expansion": "The Last Khans",
        "unique_units": ["Konnik"],
        "unique_techs": [
            "Stirrups: Cavalry attack 33% faster.",
            "Bagains: Militia-line +5 melee armor."
        ],
        "bonuses": [
            "Militia-line upgrades are free.",
            "Town Centers cost -50% stone.",
            "Can build Kreposts.",
            "Blacksmith and Siege Workshop technologies cost -50% food."
        ],
        "team_bonus": "Blacksmiths work 80% faster.",
        "tip": "Free militia line upgrades save big. Konniks fight on foot when unhorsed. Krepost is a cheaper castle alternative.",
        "meta_tier": "B",
    },

    "Cumans": {
        "id": 34,
        "type": "Cavalry",
        "expansion": "The Last Khans",
        "unique_units": ["Kipchak"],
        "unique_techs": [
            "Steppe Husbandry: Scout Cavalry line, Steppe Lancers, and Cavalry Archers are trained 100% faster.",
            "Cuman Mercenaries: Team receives 5 free Elite Kipchaks."
        ],
        "bonuses": [
            "Can build an additional Town Center in the Feudal Age (2 max before Castle Age).",
            "Siege Workshop and Battering Ram available in the Feudal Age.",
            "Cavalry move 5%/10%/15% faster in the Feudal/Castle/Imperial Age.",
            "Palisade Walls have +33% hit points and can be built 50% faster."
        ],
        "team_bonus": "Palisade Walls have +33% hit points.",
        "tip": "Build a SECOND TC in Feudal Age! Massive eco boom potential. Kipchaks fire multiple arrows. Speed bonus helps raiding.",
        "meta_tier": "B",
    },

    "Tatars": {
        "id": 35,
        "type": "Mounted Archer",
        "expansion": "The Last Khans",
        "unique_units": ["Keshik", "Flaming Camel"],
        "unique_techs": [
            "Silk Armor: Scout Cavalry line, Steppe Lancers and mounted archers have +1/+1 armor.",
            "Timurid Siegecraft: Trebuchets have +2 range."
        ],
        "bonuses": [
            "Herdable animals contain +50% food.",
            "Units do +20% damage when attacking from higher elevations (+50% instead of +25%).",
            "Parthian Tactics and Thumb Ring are free.",
            "Two Sheep spawn near newly-constructed Town Centers starting in the Castle Age."
        ],
        "team_bonus": "Cavalry Archers +2 Line of Sight.",
        "tip": "Free Thumb Ring + hill bonus = deadly archers. Keshiks generate gold when fighting. Flaming Camels are siege surprise.",
        "meta_tier": "B",
    },

    # ── Lords of the West ─────────────────────────────────────────────

    "Burgundians": {
        "id": 36,
        "type": "Cavalry",
        "expansion": "Lords of the West",
        "unique_units": ["Coustillier", "Flemish Militia"],
        "unique_techs": [
            "Burgundian Vineyards: Farmers generate gold in addition to food.",
            "Flemish Revolution: Upgrades all Villagers to Flemish Militia."
        ],
        "bonuses": [
            "Economic upgrades available one Age earlier than other civilizations.",
            "Cavalier upgrade is available in the Castle Age.",
            "Stable technologies are 50% cheaper.",
            "Gunpowder units +25% attack."
        ],
        "team_bonus": "Relics generate 0.5 food/s in addition to gold.",
        "tip": "Get eco techs one age earlier = huge timing advantage. Flemish Revolution is all-in but devastating.",
        "meta_tier": "B",
    },

    "Sicilians": {
        "id": 37,
        "type": "Infantry",
        "expansion": "Lords of the West",
        "unique_units": ["Serjeant"],
        "unique_techs": [
            "First Crusade: Each Town Center spawns a one-time batch of Serjeants (max 35 total).",
            "Hauberk: Knight-line +1/+2 armor."
        ],
        "bonuses": [
            "Castles and Town Centers are built 100% faster.",
            "Land military units (except Siege) receive 50% less bonus damage.",
            "Farm upgrades provide +100% additional food to Farms.",
            "Can build Donjons, which are upgraded Watch Towers that can train Serjeants and garrison up to 15 units."
        ],
        "team_bonus": "Transport Ships +5 carry capacity and +10 armor vs anti-ship bonus attacks.",
        "tip": "50% less bonus damage means halbs barely hurt your knights. Serjeants build Donjons for forward pressure.",
        "meta_tier": "A",
    },

    # ── Dawn of the Dukes ─────────────────────────────────────────────

    "Bohemians": {
        "id": 38,
        "type": "Gunpowder and Monk",
        "expansion": "Dawn of the Dukes",
        "unique_units": ["Hussite Wagon", "Houfnice"],
        "unique_techs": [
            "Wagenburg Tactics: Gunpowder units move 15% faster.",
            "Hussite Reforms: Monks and Monastery technologies have their gold cost replaced by food."
        ],
        "bonuses": [
            "Blacksmith upgrades cost no gold.",
            "Chemistry is available in the Castle Age.",
            "Spearman-line deals full damage with charged attack.",
            "Fervor and Sanctity are free.",
            "Mining Camp upgrades are free."
        ],
        "team_bonus": "Markets work 80% faster.",
        "tip": "Chemistry in CASTLE AGE is unique. Hand cannoneers early dominate. Houfnice (BBC upgrade) in Imp destroys everything.",
        "meta_tier": "A",
    },

    "Poles": {
        "id": 39,
        "type": "Cavalry",
        "expansion": "Dawn of the Dukes",
        "unique_units": ["Obuch", "Winged Hussar"],
        "unique_techs": [
            "Szlachta Privileges: Knight line costs -60% gold.",
            "Lechitic Legacy: Scout Cavalry line deals 33% trample damage in 0.5 tiles radius."
        ],
        "bonuses": [
            "Folwarks replace Mills and generate food from nearby Farms.",
            "Stone Miners generate extra gold.",
            "Villagers regenerate 5 HP per minute in the Dark Age, 10 in the Feudal, 15 in Castle, 20 in Imperial.",
            "Scout Cavalry, Light Cavalry, and Winged Hussar have +1 attack vs archers."
        ],
        "team_bonus": "Scout Cavalry line, Light Cavalry, and Winged Hussar +1 attack vs archers.",
        "tip": "Folwark grants instant food from farms. Obuch strips armor - pair them with archers for melting anything.",
        "meta_tier": "A",
    },

    # ── Dynasties of India ────────────────────────────────────────────

    "Dravidians": {
        "id": 40,
        "type": "Infantry and Naval",
        "expansion": "Dynasties of India",
        "unique_units": ["Urumi Swordsman", "Thirisadai"],
        "unique_techs": [
            "Medical Corps: Elephant units regenerate 30 hit points per minute.",
            "Wootz Steel: Infantry and cavalry attacks ignore armor."
        ],
        "bonuses": [
            "Receive 200 wood when advancing to the next Age.",
            "Fishermen, Oyster gatherers, and Fishing Ships carry +15.",
            "Barracks technologies cost -50%.",
            "Siege units cost -33% wood.",
            "Skirmishers and Elephant Archers attack 25% faster."
        ],
        "team_bonus": "Docks provide +5 population space.",
        "tip": "200 bonus wood helps Dark Age. Urumi charge attack devastates groups. Medical Corps heals elephants. Naval powerhouse.",
        "meta_tier": "B",
    },

    "Bengalis": {
        "id": 41,
        "type": "Elephant and Naval",
        "expansion": "Dynasties of India",
        "unique_units": ["Ratha"],
        "unique_techs": [
            "Paiks: Rathas and elephant units attack 20% faster.",
            "Mahayana: Villagers take 10% less population space."
        ],
        "bonuses": [
            "Elephant units receive 25% less bonus damage and are more resistant to conversion.",
            "Town Centers spawn 2 Villagers when the next Age is reached.",
            "Ships regenerate 15 hit points per minute.",
            "Monks have +3/+3 armor."
        ],
        "team_bonus": "Trade units yield 10% food in addition to gold.",
        "tip": "Ratha switches between ranged and melee mode. Resistance vs. conversion for elephants. Paiks makes elephants attack faster.",
        "meta_tier": "B",
    },

    "Gurjaras": {
        "id": 42,
        "type": "Cavalry and Camel",
        "expansion": "Dynasties of India",
        "unique_units": ["Shrivamsha Rider", "Chakram Thrower"],
        "unique_techs": [
            "Kshatriyas: Military units cost -25% food.",
            "Frontier Guards: Camel Riders and Elephant units +4 melee armor."
        ],
        "bonuses": [
            "Can garrison livestock inside Mills to generate food (1 food per 8 seconds per food unit on the animal).",
            "Mounted units deal +50% bonus damage (multiplicative).",
            "Can train Camel Scouts in the Feudal Age.",
            "Herdables (Sheep etc.) cannot be stolen by enemy players."
        ],
        "team_bonus": "Camel and elephant units are created 25% faster.",
        "tip": "Shrivamsha Riders dodge projectiles! Chakram Throwers are ranged infantry raiders. Mill bonus with garrisoning livestock.",
        "meta_tier": "A",
    },

    # ── Return of Rome ────────────────────────────────────────────────

    "Romans": {
        "id": 43,
        "type": "Infantry",
        "expansion": "Return of Rome",
        "unique_units": ["Centurion", "Legionary"],
        "unique_techs": [
            "Ballistas: Scorpions and Galley-line fire 33% faster.",
            "Comitatenses: Hand Cannoneers and Militia line switch between modes."
        ],
        "bonuses": [
            "Infantry gain +5% movement speed per each Barracks technology.",
            "Galley-line +1 attack.",
            "Villagers gathering Shore Fish work 25% faster, and Dock technologies are researched 50% faster.",
            "Scorpions cost -60%."
        ],
        "team_bonus": "Scorpion-line minimum range removed.",
        "tip": "Centurion boosts nearby infantry. Legionary has scorpion attack bonus. Ballista unique building provides area damage.",
        "meta_tier": "B",
    },

    # ── The Mountain Royals ───────────────────────────────────────────

    "Armenians": {
        "id": 44,
        "type": "Infantry and Naval",
        "expansion": "The Mountain Royals",
        "unique_units": ["Composite Bowman", "Warrior Priest"],
        "unique_techs": [
            "Cilician Fleet: Demolition Ships +20% blast radius; Galley-line and Dromons +1 range.",
            "Fereters: Infantry (except Spearman-line) +30 hit points, Warrior Priests +100% heal speed."
        ],
        "bonuses": [
            "Mule Carts cost -25%. Mule Carts replace Lumber Camps and Mining Camps.",
            "Mule Cart technologies are 40% more effective.",
            "Fortified Churches replace Monasteries, and the first one constructed receives a free Relic.",
            "Long Swordsman and above, and Spearman line available one Age earlier.",
            "Galley-line and Dromons fire one additional projectile each."
        ],
        "team_bonus": "Infantry have +2 Line of Sight.",
        "tip": "Fortified Church stores relics AND heals. Composite Bowmen ignore armor. Warrior Priests fight and heal.",
        "meta_tier": "B",
    },

    "Georgians": {
        "id": 45,
        "type": "Cavalry and Defensive",
        "expansion": "The Mountain Royals",
        "unique_units": ["Monaspa"],
        "unique_techs": [
            "Svan Towers: Towers, Kreposts, and Castles periodically regenerate, and are built 25% faster.",
            "Aznauri Cavalry: Knight-line, Steppe Lancers, and Monaspas take -15% population space."
        ],
        "bonuses": [
            "Fortified Churches replace Monasteries. Receives a free Fortified Church upgrade.",
            "Cavalry regenerate 20 HP/min on hills and 10 HP/min on other terrain starting in the Castle Age.",
            "Received damage is reduced by 15% when at 50% HP or less.",
            "Walls and towers cost -25%."
        ],
        "team_bonus": "Repairing buildings costs -25% resources.",
        "tip": "Units regenerate on hills. Monaspa gets attack bonus per nearby cavalry. Defensive buildings are cheap and strong.",
        "meta_tier": "B",
    },

    # ── The Three Kingdoms (May 2025) ─────────────────────────────────

    "Jurchens": {
        "id": 46,
        "type": "Cavalry and Gunpowder",
        "expansion": "The Three Kingdoms",
        "unique_units": ["Iron Pagoda", "Grenadier"],
        "unique_techs": [
            "Fortified Bastions: Fortifications regenerate 500 hit points per minute.",
            "Thunderclap Bombs: Rocket Carts, Grenadiers, and Lou Chuans detonate when defeated; projectiles produce additional explosions."
        ],
        "bonuses": [
            "Meat of hunted and livestock animals does not decay.",
            "Mounted units and Fire Lancers attack +25% faster starting in the Feudal Age.",
            "Siege Engineers available in the Castle Age.",
            "Siege and fortification technologies cost -75% wood and are researched 100% faster.",
            "Military units receive -50% friendly fire damage."
        ],
        "team_bonus": "Gunpowder units +2 Line of Sight.",
        "tip": "Iron Pagodas brush off melee attacks. Grenadiers deal blast damage. Strong siege with early Siege Engineers.",
        "meta_tier": "B",
    },

    "Khitans": {
        "id": 47,
        "type": "Infantry and Cavalry",
        "expansion": "The Three Kingdoms",
        "unique_units": ["Liao Dao", "Mounted Trebuchet"],
        "unique_techs": [
            "Gauntlet Riders: Scout Cavalry line, Steppe Lancers, and Cavalry Archers receive -50% bonus damage.",
            "Ordo: Town Centers, Castles, and Kreposts slowly train a free Mounted Trebuchet."
        ],
        "bonuses": [
            "Buildings, siege, and ships cost -15% wood.",
            "Cavalry Archers and Hand Cannoneers +2 attack vs Siege.",
            "Advancing to the next Age is 50% faster (only available from the Feudal Age).",
            "Towers have double garrison capacity and free Murder Holes."
        ],
        "team_bonus": "Light Cavalry line +25% hit points.",
        "tip": "Liao Dao deals bleeding damage. Mounted Trebuchets leave fire on impact. Extremely fast age-ups from Feudal onward.",
        "meta_tier": "B",
    },

    "Shu": {
        "id": 48,
        "type": "Infantry",
        "expansion": "The Three Kingdoms",
        "unique_units": ["White Feather Guard", "War Chariot"],
        "unique_techs": [
            "Coiled Serpent Array: Spearman-line and White Feather Guards gain additional hit points when near each other.",
            "Bolt Magazine: Archer-line, War Chariots, and Lou Chuans fire additional projectiles."
        ],
        "bonuses": [
            "Lumberjacks generate 0.7 food for every 10 wood.",
            "Archery unit technologies at the Archery Range and Blacksmith cost -25%.",
            "All land siege units and Lou Chuans move +10/15% faster in Castle/Imperial Age."
        ],
        "team_bonus": "Foot archer units except Skirmishers +2 Line of Sight.",
        "tip": "White Feather Guards slow enemies. War Chariots replace Scorpions with dual attack modes. Strong archer-siege synergy.",
        "meta_tier": "B",
    },

    "Wei": {
        "id": 49,
        "type": "Cavalry",
        "expansion": "The Three Kingdoms",
        "unique_units": ["Tiger Cavalry", "Xianbei Raider"],
        "unique_techs": [
            "Iron Decree: Knight-line and Tiger Cavalry +1/+2 armor.",
            "Tuntian System: Villagers slowly generate food while idle or garrisoned."
        ],
        "bonuses": [
            "Military unit line upgrades and Blacksmith technologies cost -50%.",
            "Stables work +25% faster.",
            "Cavalry units regenerate 10 hit points per minute starting in the Castle Age.",
            "Town Centers +3 attack."
        ],
        "team_bonus": "Cavalry +2 Line of Sight.",
        "tip": "Tiger Cavalry grows stronger with kills. Xianbei Raiders fire arrow bursts. Cheap military upgrades and fast stables.",
        "meta_tier": "B",
    },

    "Wu": {
        "id": 50,
        "type": "Naval and Archer",
        "expansion": "The Three Kingdoms",
        "unique_units": ["Zhangjian Swordsman", "Lou Chuan"],
        "unique_techs": [
            "Kuaisuo: Fire Galleys, Fire Ships, and Fast Fire Ships, and Fire Lancers +2 range.",
            "Fire Assault: Fire Lancer charges set enemies on fire; Fire Ships, Lou Chuans, and Rocket Carts leave residual fire on death."
        ],
        "bonuses": [
            "Lumber Camp upgrades provide Villagers +1 carry capacity each.",
            "Fire Galley-line and Fire Lancers have +1 range and +10%/20% hit points in Castle/Imperial Age.",
            "Military buildings are built 50% faster.",
            "Docks provide +5 population space."
        ],
        "team_bonus": "Fire Galley-line and Fire Lancers +3 attack vs buildings.",
        "tip": "Zhangjian Swordsmen are strong melee fighters. Lou Chuans dominate water. Fire units have extended range and leave fire.",
        "meta_tier": "B",
    },

    # ── The Last Chieftains (Feb 2026) ────────────────────────────────

    "Mapuche": {
        "id": 51,
        "type": "Cavalry and counter-units",
        "expansion": "The Last Chieftains",
        "unique_units": ["Bolas Rider", "Kona"],
        "unique_techs": [
            "Malon: Bolas Riders, Slingers, and Skirmishers deal pass-through damage.",
            "Butalmapu: Team Castle unique units and Bola Riders cost -15%."
        ],
        "bonuses": [
            "Foragers drop off +20% food.",
            "Settlements can train the Spearman and Skirmisher lines.",
            "Infantry, Slingers, and Skirmishers get +5/10/15 hit points in the Feudal/Castle/Imperial Age.",
            "Mounted units generate +3 gold per military unit killed.",
            "Enemy Castles are revealed on the map."
        ],
        "team_bonus": "Spearmen and Skirmishers have +2 Line of Sight.",
        "tip": "Bolas Riders slow enemies. Kona deals extra damage to injured targets. Settlements train spears and skirms for defense.",
        "meta_tier": "B",
    },

    "Muisca": {
        "id": 52,
        "type": "Monk and Economy",
        "expansion": "The Last Chieftains",
        "unique_units": ["Guecha Warrior", "Temple Guard"],
        "unique_techs": [
            "Herbalism: Archer and Champi Scout lines move 15% faster.",
            "Huaracas: Slingers have +1 range and are trained 25% faster."
        ],
        "bonuses": [
            "Advancing to the next Age costs -50% gold.",
            "Settlements cost -25% and heal allied units within 3 tiles by 5/10/15/15 HP/min in Dark/Feudal/Castle/Imperial Age.",
            "The Champi Scout line and Archery Range units have +1/2/3 melee armor in the Feudal/Castle/Imperial Age.",
            "Monks regain faith 100% faster.",
            "Caravan and Guilds are free."
        ],
        "team_bonus": "Natural gold sources (Foxes, Gold Mines, Oysters, and Whales) last 15% longer.",
        "tip": "Guecha Warriors heal allies on death. Temple Guards ramp up attack speed. Cheap age-ups and healing Settlements.",
        "meta_tier": "B",
    },

    "Tupi": {
        "id": 53,
        "type": "Infantry and Archer",
        "expansion": "The Last Chieftains",
        "unique_units": ["Blackwood Archer", "Jungle Warrior"],
        "unique_techs": [
            "Cunhambebe's Feast: Fallen enemy military units have a 50% chance to spawn a Jungle Warrior.",
            "Tapirape Arrows: Blackwood Archers, Slingers, and Champi Scout-line +2 attack."
        ],
        "bonuses": [
            "Start with +25 of each resource.",
            "Villagers gathering from Farms, Berry Bushes, and Shore Fish generate 0.35 gold per trip.",
            "Fallen units, except siege, leave food on the ground that can be gathered.",
            "Archery Range works 20% faster."
        ],
        "team_bonus": "The Loom technology is free.",
        "tip": "Blackwood Archers train in pairs cheaply. Jungle Warriors spawn from kills. Food from fallen units sustains aggression.",
        "meta_tier": "B",
    },
}


# ──────────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────────

def get_civ_info(civ_name: str) -> dict | None:
    """Look up a civilization by name (case-insensitive, fuzzy)."""
    # Exact match
    if civ_name in CIV_DATABASE:
        return CIV_DATABASE[civ_name]

    # Case-insensitive match
    for name, data in CIV_DATABASE.items():
        if name.lower() == civ_name.lower():
            return data

    # Partial match
    for name, data in CIV_DATABASE.items():
        if civ_name.lower() in name.lower() or name.lower() in civ_name.lower():
            return data

    return None


def get_civ_by_id(civ_id: int) -> tuple[str, dict] | None:
    """Look up a civilization by its internal ID."""
    name = CIV_IDS.get(civ_id)
    if name and name in CIV_DATABASE:
        return (name, CIV_DATABASE[name])
    return None


def get_civs_by_type(civ_type: str) -> list[str]:
    """Return all civilizations matching a type keyword (e.g. 'Cavalry', 'Archer')."""
    results = []
    for name, data in CIV_DATABASE.items():
        if civ_type.lower() in data["type"].lower():
            results.append(name)
    return results


def get_civs_by_expansion(expansion: str) -> list[str]:
    """Return all civilizations from a given expansion."""
    results = []
    for name, exp in CIV_EXPANSION.items():
        if expansion.lower() in exp.lower():
            results.append(name)
    return results


def get_counter_tips(civ_name: str) -> str:
    """Get the coaching tip for a civilization."""
    info = get_civ_info(civ_name)
    if info:
        return info.get("tip", "No specific tip available.")
    return f"Unknown civilization: {civ_name}"


def list_all_civs() -> list[str]:
    """Return sorted list of all civilization names."""
    return sorted(CIV_DATABASE.keys())
