"""
A Password Manager Written in Python
"""
import httpx
# Data Structure

# /
#   username
#       .passwords.json

# .passwords.json layout
# {
#   username: user's encrypted password
#   "key": key used for password encryption
#   "servers": {
#       "server_title": {
#           "server_address": The server's IP address,
#           "server_port": The port the server is listening on
#   "data": {
#       service name: {
#           username of service: {
#               "password": the encrypted password,
#               "key": the encryption key
#           }
#       }
#   }
# }

# TODO: Add way to determine whether or not device is sending data, or receiving data for data migration

# TODO: Finish the password syncing method, add a way for the user to decide to upload passwords,
#  download passwords, or recursively upload or download. Integrate password requests on server

# Window related imports
import toga
from toga.style import Pack

# App related imports
import json
import random
import os.path
import asyncio
import secrets
import textwrap
import json_repair
import cryptography.fernet
from functools import partial
from cryptography import fernet
from cryptography.fernet import Fernet

# Data migration imports
import socket
import uvicorn
from fastapi import FastAPI

from pprint import pprint as print

if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
    from tatogalib.system.clipboard import Clipboard

else:
    import pyperclip


    class FastAPIMigrationApp:
        def __init__(self, server_host: str = "0.0.0.0", server_port: int = 9001):
            self.fastapi = FastAPI()
            uvicorn.run(self.fastapi, host=server_host, port=server_port)

            @self.fastapi.post("/")
            def receive_user_data(current_user: str, user_data: str, main_key: str):
                user_data = json.loads(user_data)

                env_data = json_repair.from_file(os.path.join(toga.App().paths.data, ".env"))
                env_data["MAIN_KEY"] = main_key

                with open(os.path.join(toga.App().paths.data, current_user, ".passwords.json"), mode="w") as passwords_file:
                    json.dump(user_data, passwords_file)


                with open(os.path.join(toga.App().paths.data, ".env"), mode="w") as env_file:
                    json.dump(env_data, env_file)

                os.environ['MIGRATION_SUCCESSFUL'] = "true"

                return {
                    "success": True,
                    "messages": None
                }

            self.fastapi.add_api_route("/{current_user}/{user_data}/{main_key}", receive_user_data, methods=["POST"])

class PyPass(toga.App):
    # --------------------- App related functions ---------------------#
    async def on_running(self):
        self.load_env()
        self.main_fernet: Fernet = await self.get_main_fernet_object()

    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box()

        main_box = toga.Box(
            style=Pack(
                direction="column",
                align_items="center",
                justify_content="start"
            )
        )

        self.error_title = "Oh No!"
        self.success_title = "Yay!"
        self.confirm_title = "Confirm?"

        self.logged_in_user = None
        self.server_key = None
        self.server = None

        self.backup_words = {
            "A": [
                "a",
                "ability",
                "able",
                "about",
                "above",
                "abroad",
                "absence",
                "absent",
                "absolute",
                "accept",
                "accident",
                "accord",
                "account",
                "accuse",
                "accustom",
                "ache",
                "across",
                "act",
                "action",
                "active",
                "actor",
                "actress",
                "actual",
                "add",
                "address",
                "admire",
                "admission",
                "admit",
                "adopt",
                "adoption",
                "advance",
                "advantage",
                "adventure",
                "advertise",
                "advice",
                "advise",
                "affair",
                "afford",
                "afraid",
                "after",
                "afternoon",
                "again",
                "against",
                "age",
                "agency",
                "agent",
                "ago",
                "agree",
                "agriculture",
                "ahead",
                "aim",
                "air",
                "airplane",
                "alike",
                "alive",
                "all",
                "allow",
                "allowance",
                "almost",
                "alone",
                "along",
                "aloud",
                "already",
                "also",
                "although",
                "altogether",
                "always",
                "ambition",
                "ambitious",
                "among",
                "amongst",
                "amount",
                "amuse",
                "ancient",
                "and",
                "anger",
                "angle",
                "angry",
                "animal",
                "annoy",
                "annoyance",
                "another",
                "answer",
                "anxiety",
                "anxious",
                "any",
                "anybody",
                "anyhow",
                "anyone",
                "anything",
                "anyway",
                "anywhere",
                "apart",
                "apology",
                "appear",
                "appearance",
                "applaud",
                "applause",
                "apple",
                "application",
                "apply",
                "appoint",
                "approve",
                "arch",
                "argue",
                "arise",
                "arm",
                "army",
                "around",
                "arrange",
                "arrest",
                "arrive",
                "arrow",
                "art",
                "article",
                "artificial",
                "as",
                "ash",
                "ashamed",
                "aside",
                "ask",
                "asleep",
                "association",
                "astonish",
                "at",
                "attack",
                "attempt",
                "attend",
                "attention",
                "attentive",
                "attract",
                "attraction",
                "attractive",
                "audience",
                "aunt",
                "autumn",
                "avenue",
                "average",
                "avoid",
                "avoidance",
                "awake",
                "away",
                "awkward",
                "axe"
            ],
            "B": [
                "baby",
                "back",
                "backward",
                "bad",
                "bag",
                "baggage",
                "bake",
                "balance",
                "ball",
                "band",
                "bank",
                "bar",
                "barber",
                "bare",
                "bargain",
                "barrel",
                "base",
                "basic",
                "basin",
                "basis",
                "basket",
                "bath",
                "bathe",
                "battery",
                "battle",
                "bay",
                "be",
                "beak",
                "beam",
                "bean",
                "bear",
                "beard",
                "beast",
                "beat",
                "beauty",
                "because",
                "become",
                "bed",
                "bedroom",
                "before",
                "beg",
                "begin",
                "behave",
                "behavior",
                "behind",
                "being",
                "belief",
                "believe",
                "bell",
                "belong",
                "below",
                "belt",
                "bend",
                "beneath",
                "berry",
                "beside",
                "besides",
                "best",
                "better",
                "between",
                "beyond",
                "bicycle",
                "big",
                "bill",
                "bind",
                "bird",
                "birth",
                "bit",
                "bite",
                "bitter",
                "black",
                "blade",
                "blame",
                "bleed",
                "bless",
                "blind",
                "block",
                "blood",
                "blow",
                "blue",
                "board",
                "boast",
                "boat",
                "body",
                "boil",
                "bold",
                "bone",
                "book",
                "border",
                "borrow",
                "both",
                "bottle",
                "bottom",
                "bound",
                "boundary",
                "bow",
                "bowl",
                "box",
                "boy",
                "brain",
                "branch",
                "brass",
                "brave",
                "bravery",
                "bread",
                "breadth",
                "break",
                "breakfast",
                "breath",
                "breathe",
                "bribe",
                "bribery",
                "brick",
                "bridge",
                "bright",
                "brighten",
                "bring",
                "broad",
                "broadcast",
                "brother",
                "brown",
                "brush",
                "bucket",
                "build",
                "bunch",
                "bundle",
                "burn",
                "burst",
                "bury",
                "bus",
                "bush",
                "business",
                "businesslike",
                "businessman",
                "busy",
                "but",
                "butter",
                "button",
                "buy",
                "by"
            ],
            "C": [
                "cage",
                "cake",
                "calculate",
                "calculation",
                "calculator",
                "call",
                "calm",
                "camera",
                "camp",
                "can",
                "canal",
                "cap",
                "cape",
                "capital",
                "captain",
                "car",
                "card",
                "care",
                "carriage",
                "carry",
                "cart",
                "case",
                "castle",
                "cat",
                "catch",
                "cattle",
                "cause",
                "caution",
                "cautious",
                "cave",
                "cent",
                "center",
                "century",
                "ceremony",
                "certain",
                "certainty",
                "chain",
                "chair",
                "chairman",
                "chalk",
                "chance",
                "change",
                "character",
                "charge",
                "charm",
                "cheap",
                "cheat",
                "check",
                "cheer",
                "cheese",
                "chest",
                "chicken",
                "chief",
                "child",
                "childhood",
                "chimney",
                "choice",
                "choose",
                "christmas",
                "church",
                "circle",
                "circular",
                "citizen",
                "city",
                "civilize",
                "claim",
                "class",
                "classification",
                "classify",
                "clay",
                "clean",
                "clear",
                "clerk",
                "clever",
                "cliff",
                "climb",
                "clock",
                "close",
                "cloth",
                "clothe",
                "cloud",
                "club",
                "coal",
                "coarse",
                "coast",
                "coat",
                "coffee",
                "coin",
                "cold",
                "collar",
                "collect",
                "collection",
                "collector",
                "college",
                "colony",
                "color",
                "comb",
                "combine",
                "come",
                "comfort",
                "command",
                "commerce",
                "commercial",
                "committee",
                "common",
                "companion",
                "companionship",
                "company",
                "compare",
                "comparison",
                "compete",
                "competition",
                "competitor",
                "complain",
                "complaint",
                "complete",
                "completion",
                "complicate",
                "complication",
                "compose",
                "composition",
                "concern",
                "condition",
                "confess",
                "confession",
                "confidence",
                "confident",
                "confidential",
                "confuse",
                "confusion",
                "congratulate",
                "congratulation",
                "connect",
                "connection",
                "conquer",
                "conqueror",
                "conquest",
                "conscience",
                "conscious",
                "consider",
                "contain",
                "content",
                "continue",
                "control",
                "convenience",
                "convenient",
                "conversation",
                "cook",
                "cool",
                "copper",
                "copy",
                "cork",
                "corn",
                "corner",
                "correct",
                "correction",
                "cost",
                "cottage",
                "cotton",
                "cough",
                "could",
                "council",
                "count",
                "country",
                "courage",
                "course",
                "court",
                "cousin",
                "cover",
                "cow",
                "coward",
                "cowardice",
                "crack",
                "crash",
                "cream",
                "creature",
                "creep",
                "crime",
                "criminal",
                "critic",
                "crop",
                "cross",
                "crowd",
                "crown",
                "cruel",
                "crush",
                "cry",
                "cultivate",
                "cultivation",
                "cultivator",
                "cup",
                "cupboard",
                "cure",
                "curious",
                "curl",
                "current",
                "curse",
                "curtain",
                "curve",
                "cushion",
                "custom",
                "customary",
                "customer",
                "cut"
            ],
            "D": [
                "daily",
                "damage",
                "damp",
                "dance",
                "danger",
                "dare",
                "dark",
                "darken",
                "date",
                "daughter",
                "day",
                "daylight",
                "dead",
                "deaf",
                "deafen",
                "deal",
                "dear",
                "death",
                "debt",
                "decay",
                "deceit",
                "deceive",
                "decide",
                "decision",
                "decisive",
                "declare",
                "decrease",
                "deed",
                "deep",
                "deepen",
                "deer",
                "defeat",
                "defend",
                "defendant",
                "defense",
                "degree",
                "delay",
                "delicate",
                "delight",
                "deliver",
                "delivery",
                "demand",
                "department",
                "depend",
                "dependence",
                "dependent",
                "depth",
                "descend",
                "descendant",
                "descent",
                "describe",
                "description",
                "desert",
                "deserve",
                "desire",
                "desk",
                "despair",
                "destroy",
                "destruction",
                "destructive",
                "detail",
                "determine",
                "develop",
                "devil",
                "diamond",
                "dictionary",
                "die",
                "difference",
                "different",
                "difficult",
                "difficulty",
                "dig",
                "dine",
                "dinner",
                "dip",
                "direct",
                "direction",
                "director",
                "dirt",
                "disagree",
                "disappear",
                "disappearance",
                "disappoint",
                "disapprove",
                "discipline",
                "discomfort",
                "discontent",
                "discover",
                "discovery",
                "discuss",
                "discussion",
                "disease",
                "disgust",
                "dish",
                "dismiss",
                "disregard",
                "disrespect",
                "dissatisfaction",
                "dissatisfy",
                "distance",
                "distant",
                "distinguish",
                "district",
                "disturb",
                "ditch",
                "dive",
                "divide",
                "division",
                "do",
                "doctor",
                "dog",
                "dollar",
                "donkey",
                "door",
                "dot",
                "double",
                "doubt",
                "down",
                "dozen",
                "drag",
                "draw",
                "drawer",
                "dream",
                "dress",
                "drink",
                "drive",
                "drop",
                "drown",
                "drum",
                "dry",
                "duck",
                "due",
                "dull",
                "during",
                "dust",
                "duty"
            ],
            "E": [
                "each",
                "eager",
                "ear",
                "early",
                "earn",
                "earnest",
                "earth",
                "ease",
                "east",
                "eastern",
                "easy",
                "eat",
                "edge",
                "educate",
                "education",
                "educator",
                "effect",
                "effective",
                "efficiency",
                "efficient",
                "effort",
                "egg",
                "either",
                "elastic",
                "elder",
                "elect",
                "election",
                "electric",
                "electrician",
                "elephant",
                "else",
                "elsewhere",
                "empire",
                "employ",
                "employee",
                "empty",
                "enclose",
                "enclosure",
                "encourage",
                "end",
                "enemy",
                "engine",
                "engineer",
                "english",
                "enjoy",
                "enough",
                "enter",
                "entertain",
                "entire",
                "entrance",
                "envelope",
                "envy",
                "equal",
                "escape",
                "especially",
                "essence",
                "essential",
                "even",
                "evening",
                "event",
                "ever",
                "everlasting",
                "every",
                "everybody",
                "everyday",
                "everyone",
                "everything",
                "everywhere",
                "evil",
                "exact",
                "examine",
                "example",
                "excellence",
                "excellent",
                "except",
                "exception",
                "excess",
                "excessive",
                "exchange",
                "excite",
                "excuse",
                "exercise",
                "exist",
                "existence",
                "expect",
                "expense",
                "expensive",
                "experience",
                "experiment",
                "explain",
                "explode",
                "explore",
                "explosion",
                "explosive",
                "express",
                "expression",
                "extend",
                "extension",
                "extensive",
                "extent",
                "extra",
                "extraordinary",
                "extreme",
                "eye"
            ],
            "F": [
                "face",
                "fact",
                "factory",
                "fade",
                "fail",
                "failure",
                "faint",
                "fair",
                "faith",
                "fall",
                "FALSE",
                "fame",
                "familiar",
                "family",
                "fan",
                "fancy",
                "far",
                "farm",
                "fashion",
                "fast",
                "fasten",
                "fat",
                "fate",
                "father",
                "fatten",
                "fault",
                "favor",
                "favorite",
                "fear",
                "feast",
                "feather",
                "feed",
                "feel",
                "fellow",
                "fellowship",
                "female",
                "fence",
                "fever",
                "few",
                "field",
                "fierce",
                "fight",
                "figure",
                "fill",
                "film",
                "find",
                "fine",
                "finger",
                "finish",
                "fire",
                "firm",
                "first",
                "fish",
                "fit",
                "fix",
                "flag",
                "flame",
                "flash",
                "flat",
                "flatten",
                "flavor",
                "flesh",
                "float",
                "flood",
                "floor",
                "flour",
                "flow",
                "flower",
                "fly",
                "fold",
                "follow",
                "fond",
                "food",
                "fool",
                "foot",
                "for",
                "forbid",
                "force",
                "foreign",
                "forest",
                "forget",
                "forgive",
                "fork",
                "form",
                "formal",
                "former",
                "forth",
                "fortunate",
                "fortune",
                "forward",
                "frame",
                "framework",
                "free",
                "freedom",
                "freeze",
                "frequency",
                "frequent",
                "fresh",
                "friend",
                "friendly",
                "friendship",
                "fright",
                "frighten",
                "from",
                "front",
                "fruit",
                "fry",
                "full",
                "fun",
                "funeral",
                "funny",
                "fur",
                "furnish",
                "furniture",
                "further",
                "future"
            ],
            "G": [
                "gaiety",
                "gain",
                "gallon",
                "game",
                "gap",
                "garage",
                "garden",
                "gas",
                "gate",
                "gather",
                "gay",
                "general",
                "generous",
                "gentle",
                "gentleman",
                "get",
                "gift",
                "girl",
                "give",
                "glad",
                "glass",
                "glory",
                "go",
                "goat",
                "god",
                "gold",
                "golden",
                "good",
                "govern",
                "governor",
                "grace",
                "gradual",
                "grain",
                "grammar",
                "grammatical",
                "grand",
                "grass",
                "grateful",
                "grave",
                "gray",
                "grease",
                "great",
                "greed",
                "green",
                "greet",
                "grind",
                "ground",
                "group",
                "grow",
                "growth",
                "guard",
                "guess",
                "guest",
                "guide",
                "guilt",
                "gun"
            ],
            "H": [
                "habit",
                "hair",
                "half",
                "hall",
                "hammer",
                "hand",
                "handkerchief",
                "handle",
                "handshake",
                "handwriting",
                "hang",
                "happen",
                "happy",
                "harbor",
                "hard",
                "harden",
                "hardly",
                "harm",
                "harvest",
                "haste",
                "hasten",
                "hat",
                "hate",
                "hatred",
                "have",
                "hay",
                "he",
                "head",
                "headache",
                "headdress",
                "heal",
                "health",
                "heap",
                "hear",
                "heart",
                "heat",
                "heaven",
                "heavenly",
                "heavy",
                "height",
                "heighten",
                "hello",
                "help",
                "here",
                "hesitate",
                "hesitation",
                "hide",
                "high",
                "highway",
                "hill",
                "hinder",
                "hindrance",
                "hire",
                "history",
                "hit",
                "hold",
                "hole",
                "holiday",
                "hollow",
                "holy",
                "home",
                "homecoming",
                "homemade",
                "homework",
                "honest",
                "honesty",
                "honor",
                "hook",
                "hope",
                "horizon",
                "horizontal",
                "horse",
                "hospital",
                "host",
                "hot",
                "hotel",
                "hour",
                "house",
                "how",
                "however",
                "human",
                "humble",
                "hunger",
                "hunt",
                "hurrah",
                "hurry",
                "hurt",
                "husband",
                "hut"
            ],
            "I": [
                "I",
                "ice",
                "idea",
                "ideal",
                "idle",
                "if",
                "ill",
                "imaginary",
                "imaginative",
                "imagine",
                "imitate",
                "imitation",
                "immediate",
                "immense",
                "importance",
                "important",
                "impossible",
                "improve",
                "in",
                "inch",
                "include",
                "inclusive",
                "increase",
                "indeed",
                "indoor",
                "industry",
                "influence",
                "influential",
                "inform",
                "ink",
                "inn",
                "inquire",
                "inquiry",
                "insect",
                "inside",
                "instant",
                "instead",
                "instrument",
                "insult",
                "insurance",
                "insure",
                "intend",
                "intention",
                "interest",
                "interfere",
                "interference",
                "international",
                "interrupt",
                "interruption",
                "into",
                "introduce",
                "introduction",
                "invent",
                "invention",
                "inventor",
                "invite",
                "inward",
                "iron",
                "island",
                "it"
            ],
            "J": [
                "jaw",
                "jealous",
                "jealousy",
                "jewel",
                "join",
                "joint",
                "joke",
                "journey",
                "joy",
                "judge",
                "juice",
                "jump",
                "just",
                "justice"
            ],
            "K": [
                "keep",
                "key",
                "kick",
                "kill",
                "kind",
                "king",
                "kingdom",
                "kiss",
                "kitchen",
                "knee",
                "kneel",
                "knife",
                "knock",
                "knot",
                "know",
                "knowledge"
            ],
            "L": [
                "lack",
                "ladder",
                "lady",
                "lake",
                "lamp",
                "land",
                "landlord",
                "language",
                "large",
                "last",
                "late",
                "lately",
                "latter",
                "laugh",
                "laughter",
                "law",
                "lawyer",
                "lay",
                "lazy",
                "lead",
                "leadership",
                "leaf",
                "lean",
                "learn",
                "least",
                "leather",
                "leave",
                "left",
                "leg",
                "lend",
                "length",
                "lengthen",
                "less",
                "lessen",
                "lesson",
                "let",
                "letter",
                "level",
                "liar",
                "liberty",
                "librarian",
                "library",
                "lid",
                "lie",
                "life",
                "lift",
                "light",
                "lighten",
                "like",
                "likely",
                "limb",
                "limit",
                "line",
                "lip",
                "lipstick",
                "liquid",
                "list",
                "listen",
                "literary",
                "literature",
                "little",
                "live",
                "load",
                "loaf",
                "loan",
                "local",
                "lock",
                "lodge",
                "log",
                "lonely",
                "long",
                "look",
                "loose",
                "loosen",
                "lord",
                "lose",
                "loss",
                "lot",
                "loud",
                "love",
                "lovely",
                "low",
                "loyal",
                "loyalty",
                "luck",
                "lump",
                "lunch",
                "lung"
            ],
            "M": [
                "machine",
                "machinery",
                "mad",
                "madden",
                "mail",
                "main",
                "make",
                "male",
                "man",
                "manage",
                "mankind",
                "manner",
                "manufacture",
                "many",
                "map",
                "march",
                "mark",
                "market",
                "marriage",
                "marry",
                "mass",
                "master",
                "mat",
                "match",
                "material",
                "matter",
                "may",
                "maybe",
                "meal",
                "mean",
                "meantime",
                "meanwhile",
                "measure",
                "meat",
                "mechanic",
                "mechanism",
                "medical",
                "medicine",
                "meet",
                "melt",
                "member",
                "membership",
                "memory",
                "mend",
                "mention",
                "merchant",
                "mercy",
                "mere",
                "merry",
                "message",
                "messenger",
                "metal",
                "middle",
                "might",
                "mild",
                "mile",
                "milk",
                "mill",
                "mind",
                "mine",
                "mineral",
                "minister",
                "minute",
                "miserable",
                "misery",
                "miss",
                "mistake",
                "mix",
                "mixture",
                "model",
                "moderate",
                "moderation",
                "modern",
                "modest",
                "modesty",
                "moment",
                "momentary",
                "money",
                "monkey",
                "month",
                "moon",
                "moonlight",
                "moral",
                "more",
                "moreover",
                "morning",
                "most",
                "mother",
                "motherhood",
                "motherly",
                "motion",
                "motor",
                "mountain",
                "mouse",
                "mouth",
                "move",
                "much",
                "mud",
                "multiplication",
                "multiply",
                "murder",
                "music",
                "musician",
                "must",
                "mystery"
            ],
            "N": [
                "nail",
                "name",
                "narrow",
                "nation",
                "native",
                "nature",
                "near",
                "neat",
                "necessary",
                "necessity",
                "neck",
                "need",
                "needle",
                "neglect",
                "neighbor",
                "neighborhood",
                "neither",
                "nephew",
                "nest",
                "net",
                "network",
                "never",
                "new",
                "news",
                "newspaper",
                "next",
                "nice",
                "niece",
                "night",
                "no",
                "noble",
                "nobody",
                "noise",
                "none",
                "noon",
                "nor",
                "north",
                "northern",
                "nose",
                "not",
                "note",
                "notebook",
                "nothing",
                "notice",
                "noun",
                "now",
                "nowadays",
                "nowhere",
                "nuisance",
                "number",
                "numerous",
                "nurse",
                "nursery",
                "nut"
            ],
            "O": [
                "oar",
                "obedience",
                "obedient",
                "obey",
                "object",
                "objection",
                "observe",
                "occasion",
                "ocean",
                "of",
                "off",
                "offend",
                "offense",
                "offer",
                "office",
                "officer",
                "official",
                "often",
                "oil",
                "old",
                "old-fashioned",
                "omission",
                "omit",
                "on",
                "once",
                "one",
                "only",
                "onto",
                "open",
                "operate",
                "operation",
                "operator",
                "opinion",
                "opportunity",
                "oppose",
                "opposite",
                "opposition",
                "or",
                "orange",
                "order",
                "ordinary",
                "organ",
                "organize",
                "origin",
                "ornament",
                "other",
                "otherwise",
                "ought",
                "ounce",
                "out",
                "outline",
                "outside",
                "outward",
                "over",
                "overcome",
                "overflow",
                "owe",
                "own",
                "ownership"
            ],
            "P": [
                "pack",
                "package",
                "pad",
                "page",
                "pain",
                "paint",
                "pair",
                "pale",
                "pan",
                "paper",
                "parcel",
                "pardon",
                "parent",
                "park",
                "part",
                "particle",
                "particular",
                "partner",
                "party",
                "pass",
                "passage",
                "passenger",
                "past",
                "paste",
                "pastry",
                "path",
                "patience",
                "patient",
                "patriotic",
                "pattern",
                "pause",
                "paw",
                "pay",
                "peace",
                "pearl",
                "peculiar",
                "pen",
                "pencil",
                "penny",
                "people",
                "per",
                "perfect",
                "perfection",
                "perform",
                "performance",
                "perhaps",
                "permanent",
                "permission",
                "permit",
                "person",
                "persuade",
                "persuasion",
                "pet",
                "photograph",
                "photography",
                "pick",
                "picture",
                "piece",
                "pig",
                "pigeon",
                "pile",
                "pin",
                "pinch",
                "pink",
                "pint",
                "pipe",
                "pity",
                "place",
                "plain",
                "plan",
                "plant",
                "plaster",
                "plate",
                "play",
                "pleasant",
                "please",
                "pleasure",
                "plenty",
                "plow",
                "plural",
                "pocket",
                "poem",
                "poet",
                "point",
                "poison",
                "police",
                "polish",
                "polite",
                "political",
                "politician",
                "politics",
                "pool",
                "poor",
                "popular",
                "population",
                "position",
                "possess",
                "possession",
                "possessor",
                "possible",
                "post",
                "postpone",
                "pot",
                "pound",
                "pour",
                "poverty",
                "powder",
                "power",
                "practical",
                "practice",
                "praise",
                "pray",
                "preach",
                "precious",
                "prefer",
                "preference",
                "prejudice",
                "prepare",
                "presence",
                "present",
                "preserve",
                "president",
                "press",
                "pressure",
                "pretend",
                "pretense",
                "pretty",
                "prevent",
                "prevention",
                "price",
                "pride",
                "priest",
                "print",
                "prison",
                "private",
                "prize",
                "probable",
                "problem",
                "procession",
                "produce",
                "product",
                "production",
                "profession",
                "profit",
                "program",
                "progress",
                "promise",
                "prompt",
                "pronounce",
                "pronunciation",
                "proof",
                "proper",
                "property",
                "proposal",
                "propose",
                "protect",
                "protection",
                "proud",
                "prove",
                "provide",
                "public",
                "pull",
                "pump",
                "punctual",
                "punish",
                "pupil",
                "pure",
                "purple",
                "purpose",
                "push",
                "put",
                "puzzle"
            ],
            "Q": [
                "qualification",
                "qualify",
                "quality",
                "quantity",
                "quarrel",
                "quart",
                "quarter",
                "queen",
                "question",
                "quick",
                "quiet",
                "quite"
            ],
            "R": [
                "rabbit",
                "race",
                "radio",
                "rail",
                "railroad",
                "rain",
                "raise",
                "rake",
                "rank",
                "rapid",
                "rare",
                "rate",
                "rather",
                "raw",
                "ray",
                "razor",
                "reach",
                "read",
                "ready",
                "real",
                "realize",
                "reason",
                "reasonable",
                "receipt",
                "receive",
                "recent",
                "recognition",
                "recognize",
                "recommend",
                "record",
                "red",
                "redden",
                "reduce",
                "reduction",
                "refer",
                "reference",
                "reflect",
                "reflection",
                "refresh",
                "refuse",
                "regard",
                "regret",
                "regular",
                "rejoice",
                "relate",
                "relation",
                "relative",
                "relief",
                "relieve",
                "religion",
                "remain",
                "remark",
                "remedy",
                "remember",
                "remind",
                "rent",
                "repair",
                "repeat",
                "repetition",
                "replace",
                "reply",
                "report",
                "represent",
                "representative",
                "reproduce",
                "reproduction",
                "republic",
                "reputation",
                "request",
                "rescue",
                "reserve",
                "resign",
                "resist",
                "resistance",
                "respect",
                "responsible",
                "rest",
                "restaurant",
                "result",
                "retire",
                "return",
                "revenge",
                "review",
                "reward",
                "ribbon",
                "rice",
                "rich",
                "rid",
                "ride",
                "right",
                "ring",
                "ripe",
                "ripen",
                "rise",
                "risk",
                "rival",
                "rivalry",
                "river",
                "road",
                "roar",
                "roast",
                "rob",
                "robbery",
                "rock",
                "rod",
                "roll",
                "roof",
                "room",
                "root",
                "rope",
                "rot",
                "rotten",
                "rough",
                "round",
                "row",
                "royal",
                "royalty",
                "rub",
                "rubber",
                "rubbish",
                "rude",
                "rug",
                "ruin",
                "rule",
                "run",
                "rush",
                "rust"
            ],
            "S": [
                "sacred",
                "sacrifice",
                "sad",
                "sadden",
                "saddle",
                "safe",
                "safety",
                "sail",
                "sailor",
                "sake",
                "salary",
                "sale",
                "salesman",
                "salt",
                "same",
                "sample",
                "sand",
                "satisfaction",
                "satisfactory",
                "satisfy",
                "sauce",
                "saucer",
                "save",
                "saw",
                "say",
                "scale",
                "scarce",
                "scatter",
                "scene",
                "scenery",
                "scent",
                "school",
                "science",
                "scientific",
                "scientist",
                "scissors",
                "scold",
                "scorn",
                "scrape",
                "scratch",
                "screen",
                "screw",
                "sea",
                "search",
                "season",
                "seat",
                "second",
                "secrecy",
                "secret",
                "secretary",
                "see",
                "seed",
                "seem",
                "seize",
                "seldom",
                "self",
                "selfish",
                "sell",
                "send",
                "sense",
                "sensitive",
                "sentence",
                "separate",
                "separation",
                "serious",
                "servant",
                "serve",
                "service",
                "set",
                "settle",
                "several",
                "severe",
                "sew",
                "shade",
                "shadow",
                "shake",
                "shall",
                "shallow",
                "shame",
                "shape",
                "share",
                "sharp",
                "sharpen",
                "shave",
                "she",
                "sheep",
                "sheet",
                "shelf",
                "shell",
                "shelter",
                "shield",
                "shilling",
                "shine",
                "ship",
                "shirt",
                "shock",
                "shoe",
                "shoot",
                "shop",
                "shore",
                "short",
                "shorten",
                "should",
                "shoulder",
                "shout",
                "show",
                "shower",
                "shut",
                "sick",
                "side",
                "sight",
                "sign",
                "signal",
                "signature",
                "silence",
                "silent",
                "silk",
                "silver",
                "simple",
                "simplicity",
                "since",
                "sincere",
                "sing",
                "single",
                "sink",
                "sir",
                "sister",
                "sit",
                "situation",
                "size",
                "skill",
                "skin",
                "skirt",
                "sky",
                "slave",
                "slavery",
                "sleep",
                "slide",
                "slight",
                "slip",
                "slippery",
                "slope",
                "slow",
                "small",
                "smell",
                "smile",
                "smoke",
                "smooth",
                "snake",
                "snow",
                "so",
                "soap",
                "social",
                "society",
                "sock",
                "soft",
                "soften",
                "soil",
                "soldier",
                "solemn",
                "solid",
                "solution",
                "solve",
                "some",
                "somebody",
                "somehow",
                "someone",
                "something",
                "sometime",
                "sometimes",
                "somewhere",
                "son",
                "song",
                "soon",
                "sore",
                "sorrow",
                "sorry",
                "sort",
                "soul",
                "sound",
                "soup",
                "sour",
                "south",
                "sow",
                "space",
                "spade",
                "spare",
                "speak",
                "special",
                "speech",
                "speed",
                "spell",
                "spend",
                "spill",
                "spin",
                "spirit",
                "spit",
                "spite",
                "splendid",
                "split",
                "spoil",
                "spoon",
                "sport",
                "spot",
                "spread",
                "spring",
                "square",
                "staff",
                "stage",
                "stain",
                "stair",
                "stamp",
                "stand",
                "standard",
                "staple",
                "star",
                "start",
                "state",
                "station",
                "stay",
                "steady",
                "steam",
                "steel",
                "steep",
                "steer",
                "stem",
                "step",
                "stick",
                "stiff",
                "stiffen",
                "still",
                "sting",
                "stir",
                "stock",
                "stocking",
                "stomach",
                "stone",
                "stop",
                "store",
                "storm",
                "story",
                "stove",
                "straight",
                "straighten",
                "strange",
                "strap",
                "straw",
                "stream",
                "street",
                "strength",
                "strengthen",
                "stretch",
                "strict",
                "strike",
                "string",
                "strip",
                "stripe",
                "stroke",
                "strong",
                "struggle",
                "student",
                "study",
                "stuff",
                "stupid",
                "subject",
                "substance",
                "succeed",
                "success",
                "such",
                "suck",
                "sudden",
                "suffer",
                "sugar",
                "suggest",
                "suggestion",
                "suit",
                "summer",
                "sun",
                "supper",
                "supply",
                "support",
                "suppose",
                "sure",
                "surface",
                "surprise",
                "surround",
                "suspect",
                "suspicion",
                "suspicious",
                "swallow",
                "swear",
                "sweat",
                "sweep",
                "sweet",
                "sweeten",
                "swell",
                "swim",
                "swing",
                "sword",
                "sympathetic",
                "sympathy",
                "system"
            ],
            "T": [
                "table",
                "tail",
                "tailor",
                "take",
                "talk",
                "tall",
                "tame",
                "tap",
                "taste",
                "tax",
                "taxi",
                "tea",
                "teach",
                "tear",
                "telegraph",
                "telephone",
                "tell",
                "temper",
                "temperature",
                "temple",
                "tempt",
                "tend",
                "tender",
                "tent",
                "term",
                "terrible",
                "test",
                "than",
                "thank",
                "that",
                "the",
                "theater",
                "theatrical",
                "then",
                "there",
                "therefore",
                "these",
                "they",
                "thick",
                "thicken",
                "thief",
                "thin",
                "thing",
                "think",
                "thirst",
                "this",
                "thorn",
                "thorough",
                "those",
                "though",
                "thread",
                "threat",
                "threaten",
                "throat",
                "through",
                "throw",
                "thumb",
                "thunder",
                "thus",
                "ticket",
                "tide",
                "tidy",
                "tie",
                "tight",
                "tighten",
                "till",
                "time",
                "tin",
                "tip",
                "tire",
                "title",
                "to",
                "tobacco",
                "today",
                "toe",
                "together",
                "tomorrow",
                "ton",
                "tongue",
                "tonight",
                "too",
                "tool",
                "tooth",
                "top",
                "total",
                "touch",
                "tough",
                "tour",
                "toward",
                "towel",
                "tower",
                "town",
                "toy",
                "track",
                "trade",
                "train",
                "translate",
                "translation",
                "translator",
                "trap",
                "travel",
                "tray",
                "treasure",
                "treasury",
                "treat",
                "tree",
                "tremble",
                "trial",
                "tribe",
                "trick",
                "trip",
                "trouble",
                "true",
                "trunk",
                "trust",
                "truth",
                "try",
                "tube",
                "tune",
                "turn",
                "twist",
                "type"
            ],
            "U": [
                "ugly",
                "umbrella",
                "uncle",
                "under",
                "underneath",
                "understand",
                "union",
                "unit",
                "unite",
                "unity",
                "universal",
                "universe",
                "university",
                "unless",
                "until",
                "up",
                "upon",
                "upper",
                "uppermost",
                "upright",
                "upset",
                "urge",
                "urgent",
                "use",
                "usual"
            ],
            "V": [
                "vain",
                "valley",
                "valuable",
                "value",
                "variety",
                "various",
                "veil",
                "verb",
                "verse",
                "very",
                "vessel",
                "victory",
                "view",
                "village",
                "violence",
                "violent",
                "virtue",
                "visit",
                "visitor",
                "voice",
                "vote",
                "vowel",
                "voyage"
            ],
            "W": [
                "wage",
                "waist",
                "wait",
                "waiter",
                "wake",
                "walk",
                "wall",
                "wander",
                "want",
                "war",
                "warm",
                "warmth",
                "warn",
                "wash",
                "waste",
                "watch",
                "water",
                "wave",
                "wax",
                "way",
                "we",
                "weak",
                "weaken",
                "wealth",
                "weapon",
                "wear",
                "weather",
                "weave",
                "weed",
                "week",
                "weekday",
                "weekend",
                "weigh",
                "weight",
                "welcome",
                "well",
                "west",
                "western",
                "wet",
                "what",
                "whatever",
                "wheat",
                "wheel",
                "when",
                "whenever",
                "where",
                "wherever",
                "whether",
                "which",
                "whichever",
                "while",
                "whip",
                "whisper",
                "whistle",
                "white",
                "whiten",
                "who",
                "whoever",
                "whole",
                "whom",
                "whose",
                "why",
                "wicked",
                "wide",
                "widen",
                "widow",
                "widower",
                "width",
                "wife",
                "wild",
                "will",
                "win",
                "wind",
                "window",
                "wine",
                "wing",
                "winter",
                "wipe",
                "wire",
                "wisdom",
                "wise",
                "wish",
                "with",
                "within",
                "without",
                "witness",
                "woman",
                "wonder",
                "wood",
                "wooden",
                "wool",
                "woolen",
                "word",
                "work",
                "world",
                "worm",
                "worry",
                "worse",
                "worship",
                "worth",
                "would",
                "wound",
                "wrap",
                "wreck",
                "wrist",
                "write",
                "wrong"
            ],
            "X": [
                "xenomorphically"
            ],
            "Y": [
                "yard",
                "year",
                "yellow",
                "yes",
                "yesterday",
                "yet",
                "yield",
                "you",
                "young",
                "youth"
            ],
            "Z": [
                "zero"
            ]
        }

        server_group = toga.Group(
            "Server Config",
            order=0
        )

        add_new_server_command = toga.Command(
            action=self.collect_server_data,
            text="Add New Server",
            group=server_group,
            order=0
        )

        edit_server_command = toga.Command(
            action=self.collect_server_data,
            text="Edit Server",
            group=server_group,
            order=1
        )

        connect_server_command = toga.Command(
            action=self.collect_server_data,
            text="Connect Server",
            group=server_group,
            order=2
        )

        upload_passwords_command = toga.Command(
            action=self.collect_server_data,
            text="Upload Passwords to Server",
            group=server_group,
            order=3
        )

        download_passwords_command = toga.Command(
            action=self.collect_server_data,
            text="Download Passwords from Server",
            group=server_group,
            order=4
        )

        delete_server_command = toga.Command(
            action=self.collect_server_data,
            text="Delete Server",
            group=server_group,
            order=6
        )

        self.label_style = Pack(
            margin_top=10,
            margin_bottom=10,
        )

        self.input_style = Pack(
            margin_top=10,
            margin_bottom=10
        )

        self.button_style = Pack(
            margin_top=10,
            margin_bottom=10,
        )

        user_label = toga.Label(
            text="User:",
            style=self.label_style
        )

        self.user_entry = toga.TextInput(
            style=self.input_style
        )

        password_label = toga.Label(
            text="Password:",
            style=self.label_style
        )

        self.password_entry = toga.TextInput(
            style=self.input_style
        )

        login_button = toga.Button(
            text="Login",
            on_press=self.login,
            style=self.button_style
        )

        create_user_button = toga.Button(
            text="Create User",
            on_press=self.create_user,
            style=self.button_style
        )

        delete_user_button = toga.Button(
            text="Delete User",
            on_press=self.delete_user,
            style=Pack(
                margin_top=10,
                margin_bottom=10,
                background_color="red"
            )
        )

        self.a_box = toga.Box(
            style=Pack(
                direction="column",
                align_items="center",
                width=10
            )
        )

        self.a_box.add(user_label)
        self.a_box.add(self.user_entry)
        self.a_box.add(password_label)
        self.a_box.add(self.password_entry)
        self.a_box.add(login_button)
        self.a_box.add(create_user_button)
        self.a_box.add(delete_user_button)

        main_box.add(self.a_box)
        self.commands.clear()

        self.commands.add(edit_server_command)
        self.commands.add(delete_server_command)
        self.commands.add(connect_server_command)
        self.commands.add(add_new_server_command)
        self.commands.add(upload_passwords_command)
        self.commands.add(download_passwords_command)

        self.paths.data.mkdir(parents=True, exist_ok=True)
        self.paths.logs.mkdir(parents=True, exist_ok=True)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    async def recover_key(self, _):
        backup_phrase = self.backup_phrase_entry.value.replace(" ", "").split("/")

        recovered_key = ""

        for word in backup_phrase:
            # word = word.replace(" ", "").replace('"', "")

            if word == '':
                del backup_phrase[backup_phrase.index(word)]

            elif word.isnumeric() is True or word == "-" or word == "=":
                recovered_key += word

            else:
                if word[-1] == "!":
                    recovered_key += word[0].title()

                else:
                    recovered_key += word[0]

            print(word)

        print("The recovered key is: " + recovered_key)

        try:
            Fernet(recovered_key).encrypt(b"text")

        except cryptography.fernet.InvalidToken:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Failed to recover key"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen(logged_in=False)

        else:
            username = self.user_entry.value
            password_file_path = os.path.join(self.paths.data, username, ".passwords.json")

            user_data = self.load_user_passwords(check_data_integrity=False)
            user_data["key"] = self.main_fernet.encrypt(recovered_key.encode()).decode()

            with open(password_file_path, mode="w") as passwords_file:
                json.dump(user_data, passwords_file, indent=4)

            dialog = toga.InfoDialog(
                title=self.success_title,
                message=f"Successfully recovered key for user {username}"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen(logged_in=False)

    def return_to_home_screen(self, logged_in=True):
        if logged_in:
            service_label = toga.Label(
                text="Service: ",
                style=self.label_style
            )

            self.service_entry = toga.TextInput(
                style=self.input_style
            )

            username_label = toga.Label(
                text="Username: ",
                style=self.label_style
            )

            self.username_entry = toga.TextInput(
                style=self.input_style
            )

            password_label = toga.Label(
                text="Password: ",
                style=self.label_style
            )

            self.service_password_entry = toga.TextInput(
                style=self.input_style
            )

            add_password_button = toga.Button(
                text="Add Password",
                on_press=self.add_password,
                style=self.button_style
            )

            generate_password_button = toga.Button(
                text="Generate Password",
                on_press=self.generate_password,
                style=self.button_style
            )

            edit_password_button = toga.Button(
                text="Edit Password",
                on_press=self.edit_password,
                style=self.button_style
            )

            get_password_button = toga.Button(
                text="Get Password",
                on_press=self.get_password,
                style=self.button_style
            )

            delete_username_button = toga.Button(
                text="Delete Username",
                on_press=self.delete_username,
                style=self.button_style
            )

            create_backup_phrase_button = toga.Button(
                text="Create backup phrase",
                on_press=self.create_backup_phrase,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    service_label,
                    self.service_entry,
                    username_label,
                    self.username_entry,
                    password_label,
                    self.service_password_entry,
                    add_password_button,
                    generate_password_button,
                    edit_password_button,
                    get_password_button,
                    delete_username_button,
                    create_backup_phrase_button
                ],
                clear_screen=True
            )
        else:
            user_label = toga.Label(
                text="User:",
                style=self.label_style
            )

            self.user_entry = toga.TextInput(
                style=self.input_style
            )

            password_label = toga.Label(
                text="Password:",
                style=self.label_style
            )

            self.password_entry = toga.TextInput(
                style=self.input_style
            )

            login_button = toga.Button(
                text="Login",
                on_press=self.login,
                style=self.button_style
            )

            create_user_button = toga.Button(
                text="Create User",
                on_press=self.create_user,
                style=self.button_style
            )

            delete_user_button = toga.Button(
                text="Delete User",
                on_press=self.delete_user,
                style=Pack(
                    margin_top=10,
                    margin_bottom=10,
                    background_color="red"
                )
            )

            self.add_to_screen(
                widgets=[
                    user_label,
                    self.user_entry,
                    password_label,
                    self.password_entry,
                    login_button,
                    create_user_button,
                    delete_user_button
                ],
                clear_screen=True
            )

    def load_env(self):
        if not os.path.exists(os.path.join(self.paths.data, ".env")):
            return None

        with open(os.path.join(self.paths.data, ".env"), mode="r") as env_file:
            env_data = json_repair.load(env_file)

        for key in env_data.keys():
            os.environ[key] = env_data[key]

    async def get_main_fernet_object(self) -> Fernet or None:
        main_key = os.environ.get("MAIN_KEY")

        if main_key is None:
            dialog = toga.QuestionDialog(
                title=self.confirm_title,
                message="No main key was found. Do you want to generate a new one? GENERATING A NEW MAIN KEY WILL "
                        "LOSE ALL SAVED PASSWORDS FOR ALL USERS!!!"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result is True:
                main_key = Fernet.generate_key()
                os.environ["MAIN_KEY"] = main_key.decode()

                with open(os.path.join(self.paths.data, ".env"), mode="a") as env_file:
                    json.dump(
                        {
                            "MAIN_KEY": main_key.decode()
                        },
                        env_file,
                        indent=4
                    )

                for user_folder in os.listdir(self.paths.data):
                    if os.path.isdir(user_folder):
                        user_path = os.path.join(self.paths.data, user_folder)

                        os.unlink(
                            os.path.join(
                                user_path,
                                ".passwords.json"
                            )
                        )

                        os.rmdir(user_path)

        print(main_key)

        main_fernet = Fernet(main_key)
        return main_fernet

# --------------------- User related functions ---------------------#

    async def login(self, _):
        username: str = self.user_entry.value
        password: str = self.password_entry.value
        username_path = os.path.join(self.paths.data, username)

        is_valid = await self.validate_values(
            to_validate={
                "username": username,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if not os.path.exists(username_path):
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"User {username} doesn't exist"
            )

            await self.dialog(
                dialog
            )

            return None

        users_passwords = self.load_user_passwords()

        try:
            user_password = users_passwords[username]
            user_key = self.main_fernet.decrypt(users_passwords["key"].encode())

        except KeyError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't login to user {username}. No decryption key found"
            )

            return await self.dialog(dialog)

        except fernet.InvalidToken:
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message="An invalid key was saved. Do you want to attempt key recovery? (Requires backup phrase)"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result:
                backup_phrase_label = toga.Label(
                    text="Please enter your backup phrase below, separating each word with '/ ', or paste in the backup "
                         "phrase that was copied to your clipboard:",
                    style=self.label_style
                )

                self.backup_phrase_entry = toga.TextInput(style=self.input_style)

                recover_backup_phrase_button = toga.Button(
                    text="Recover Key",
                    on_press=self.recover_key,
                    style=self.button_style
                )

                self.add_to_screen(
                    widgets=[
                        backup_phrase_label,
                        self.backup_phrase_entry,
                        recover_backup_phrase_button
                    ],
                    clear_screen=True
                )

                return None

        cipher = Fernet(user_key)

        if users_passwords == {}:
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message="Saved passwords are corrupt. Local recovery has already been attempted. Attempt recovery from server?"
            )

            dialog_result = await self.dialog(dialog)

            if dialog_result:
                server_address_label = toga.Label(
                    text="Server Address:",
                    style=self.label_style
                )

                self.server_address_entry = toga.TextInput(
                    style=self.input_style
                )

                server_port_label = toga.Label(
                    text="Server Port:",
                    style=self.label_style
                )

                self.server_port_entry = toga.TextInput(
                    style=self.input_style
                )

                recover_passwords_button = toga.Button(
                    text="Recover Passwords",
                    on_press=self.download_passwords,
                    style=self.button_style
                )

                self.add_to_screen(
                    widgets=[
                        server_address_label,
                        self.server_address_entry,
                        server_port_label,
                        self.server_port_entry,
                        recover_passwords_button
                    ],
                    clear_screen=True
                )


        print(cipher.decrypt(user_password).decode())

        if password == cipher.decrypt(user_password).decode():
            self.logged_in_user = username
            self.data_file_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

            print(self.main_window.size)

            self.return_to_home_screen()

            await self.migrate_data(_=None)

            return None

        else:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Incorrect password"
            )

            await self.dialog(dialog)

    async def create_user(self, _):
        user = self.user_entry.value
        password = self.password_entry.value

        self.data_file_path = os.path.join(self.paths.data, user, ".passwords.json")

        is_valid = await self.validate_values(
            {
                "user": user,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        encryption_key = Fernet.generate_key()
        cipher = Fernet(encryption_key)

        username_path = os.path.join(self.paths.data, user)

        if os.path.exists(username_path):
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"User {user} already exists"
            )

            await self.dialog(dialog)
            return None

        user_data = {
            user: cipher.encrypt(password.encode()).decode(),
            "key": self.main_fernet.encrypt(encryption_key).decode()
        }

        os.mkdir(username_path)

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully created user {user}"
        )

        await self.dialog(dialog)
        return None

    async def delete_user(self, _):
        user = self.user_entry.value
        password = self.password_entry.value

        user_data = self.load_user_passwords()

        if user_data == {}:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Cannot delete user. Failed to load user data or user doesn't exist"
            )

            await self.dialog(dialog)
            return None

        cipher = Fernet(
            self.main_fernet.decrypt(user_data["key"]),
        )

        is_valid = await self.validate_values(
            to_validate={
                "User": user,
                "Password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if password != cipher.decrypt(user_data[user]).decode():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Cannot delete user. Incorrect credentials"
            )

            await self.dialog(dialog)
            return None

        confirm_dialog = toga.ConfirmDialog(
            title=self.confirm_title,
            message=f"Are you really sure you want to delete user {user}?"
        )

        confirm_result = await self.dialog(confirm_dialog)

        if not confirm_result:
            return None

        os.unlink(
            os.path.join(
                self.paths.data,
                user,
                ".passwords.json"
            )
        )

        os.rmdir(
            os.path.join(
                self.paths.data,
                user
            )
        )

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted user {user}"
        )

        await self.dialog(dialog)
        return None

    # --------------------- Password related functions ---------------------#

    async def add_password(self, _):
        service = self.service_entry.value
        username = self.username_entry.value
        password = self.service_password_entry.value

        user_data = self.load_user_passwords()

        if not "data" in user_data.keys():
            user_data["data"] = {}

        password_key = Fernet.generate_key()
        cipher = Fernet(password_key)

        is_valid = await self.validate_values(
            to_validate={
                "service": service,
                "username": username,
                "password": password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )
        if not is_valid:
            return None

        if service in user_data["data"].keys() and username in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't add username {username} to service {service}. Username already exists"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            user_data["data"][service] = {
                username: {
                    "password": cipher.encrypt(password.encode()).decode(),
                    "key": self.main_fernet.encrypt(password_key).decode()
                }
            }

        elif username not in user_data["data"][service].keys():
            user_data["data"][service][username] = {
                "password": cipher.encrypt(password.encode()).decode(),
                "key": self.main_fernet.encrypt(password_key).decode()
            }

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        self.copy_to_clipboard(password)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully added username {username} to service {service}. \n\nThe Password has been copied to your clipboard"
        )

        await self.dialog(dialog)
        return None

    async def edit_password(self, _):
        new_password = self.service_password_entry.value
        username = self.username_entry.value
        service = self.service_entry.value

        new_key = Fernet.generate_key()
        cipher = Fernet(new_key)

        user_data = self.load_user_passwords()

        await self.validate_values(
            to_validate={
                "Service": service,
                "Username": username,
                "New Password": new_password
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if "data" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service}. No passwords are saved"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service}. No such service is saved"
            )

            await self.dialog(dialog)
            return None

        elif username not in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't edit password for service {service} username {username}. No such username is saved"
            )

            await self.dialog(dialog)
            return None

        user_data["data"][service][username]["key"] = self.main_fernet.encrypt(new_key).decode()
        user_data["data"][service][username]["password"] = cipher.encrypt(new_password.encode()).decode()

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

            self.copy_to_clipboard(new_password)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully edited password for service {service} username {username}\n\nThe new password has also been copied to your clipboard"
        )

        await self.dialog(dialog)
        return None

    async def get_password(self, _):
        service = self.service_entry.value
        username = self.username_entry.value
        user_data = self.load_user_passwords()

        is_valid = await self.validate_values(
            to_validate={
                "service": service,
                "username": username
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if not "data" in user_data.keys():
            user_data["data"] = {}

        if not service in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Service {service} doesn't exist"
            )

            await self.dialog(dialog)
            return

        if not username in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Username {username} doesn't exist in service {service}"
            )

            await self.dialog(dialog)
            return None

        encrypted_password: str = user_data["data"][service][username]["password"]
        encryption_key: str = self.main_fernet.decrypt(user_data["data"][service][username]["key"]).decode()

        cipher = Fernet(encryption_key.encode())

        self.copy_to_clipboard(cipher.decrypt(encrypted_password).decode())

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Password for service {service} and username {username} is: \n\n{cipher.decrypt(encrypted_password).decode()}. \n\nIt has been copied to your clipboard"
        )

        await self.dialog(dialog)
        return None

    async def delete_username(self, _):
        service = self.service_entry.value
        username = self.username_entry.value

        user_data = self.load_user_passwords()

        if "data" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No passwords saved"
            )

            await self.dialog(dialog)
            return None

        elif service not in user_data["data"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service}. No such service saved"
            )

            await self.dialog(dialog)
            return None

        elif username not in user_data["data"][service].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Can't delete password for service {service} username {username}. No such username saved"
            )

            await self.dialog(dialog)
            return None

        del user_data["data"][service][username]

        with open(self.data_file_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted service {service} username {username}"
        )

        return await self.dialog(dialog)

    async def generate_password(self, _):
        new_password = secrets.token_urlsafe(20)
        self.service_password_entry.value = new_password
        print(self.service_password_entry.value)

    async def create_backup_phrase(self, _):
        user_key: str = self.main_fernet.decrypt(self.load_user_passwords()["key"]).decode()
        backup_phrase = []

        print(user_key)

        index = 1
        for character in user_key:
            if character.isnumeric() is True or character == "-" or character == "=" or character == "_":
                string_to_append = character

            elif character.isupper():
                string_to_append = f"{random.choice(self.backup_words[character.upper()])}!"

            else:
                string_to_append = f"{random.choice(self.backup_words[character.upper()])}"

            if not user_key.index(character) % 3 == 0:
                string_to_append += "    "

            backup_phrase.append(string_to_append)

            index += 1

        phrase_copy_safe = []
        for word in backup_phrase:
            word = word.replace(" ", "")
            word += "/"

            phrase_copy_safe.append(word)
            print(word)

        self.copy_to_clipboard(
            str(phrase_copy_safe).replace("[", "").replace("]", "").replace(",", "").replace("'", ""))

        print(self.main_window.size)

        backup_phrase_label = toga.Label(
            text=textwrap.fill(f"Your backup phrase has been copied to your clipboard."
                               "\n\nSAVE THIS SOMEWHERE ELSE!!! If your key gets lost, you will not be able to recover it without"
                               " this backup phrase.".replace("[", "").replace("]", "")
                               .replace(",", "").replace("'", ""), 40, drop_whitespace=False),
            style=self.label_style
        )

        next_button = toga.Button(
            text="Continue to home",
            on_press=self.return_to_home_screen,
            style=self.button_style
        )

        self.add_to_screen(
            widgets=[
                backup_phrase_label,
                next_button
            ],
            clear_screen=True
        )

    async def migrate_data(self, _=None, send_data=False):
        if send_data:
            user = self.logged_in_user
            main_key = os.environ.get("MAIN_KEY")
            user_data = json.dumps(self.load_user_passwords())

            result = httpx.post(f"http://{self.to_device_address_input.value}:{self.to_device_port_input.value}/{user}/{user_data}/{main_key}")
            result.raise_for_status()

            print(result.status_code)
        
        dialog = toga.QuestionDialog(
            title=self.confirm_title,
            message="Do you want to receive or send data? Select 'No' to receive data, and 'Yes' to send data"
        )
        
        dialog_result = await self.dialog(dialog)

        print(dialog_result)
        
        if dialog_result:
            print("Defining widgets")

            to_device_address_label = toga.Label(
                text="Please enter the address of the receiving device",
                style=self.label_style
            )

            self.to_device_address_input = toga.TextInput(style=self.input_style)

            to_device_port_label = toga.Label(
                text="Please enter the port of the receiving device",
                style=self.label_style
            )

            self.to_device_port_input = toga.TextInput(style=self.input_style)

            send_data_button = toga.Button(
                text="Send data to receiving device",
                on_press=partial(self.migrate_data, send_data=True),
                style=self.button_style
            )

            print("Adding widgets to screen")

            await asyncio.to_thread(
                self.add_to_screen,
                widgets=[
                    to_device_address_label,
                    self.to_device_address_input,
                    to_device_port_label,
                    self.to_device_port_input,
                    send_data_button
                ],
                clear_screen=True
            )
            
        else:
            dialog = toga.QuestionDialog(
                title=self.confirm_title,
                message="THIS WILL REPLACE ALL PASSWORDS SAVED ON THIS DEVICE. Are you sure you want to continue?"
            )
    
            dialog_result = await self.dialog(dialog)
    
            if dialog_result:
                FastAPIMigrationApp()
    
                while os.environ.get("MIGRATION_SUCCESSFUL") is None:
                    await asyncio.sleep(10)
    
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message="Successfully migrated data"
                )
    
                await self.dialog(dialog)
    
            else:
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message="Data migration has been cancelled"
                )
    
                await self.dialog(dialog)

        # return self.return_to_home_screen()

    def load_user_passwords(self, check_data_integrity=True) -> dict:
        username = self.user_entry.value
        password_file_path = os.path.join(self.paths.data, username, ".passwords.json")

        if not os.path.exists(password_file_path):
            return {}

        user_data = json_repair.from_file(password_file_path)

        if user_data == "" and check_data_integrity == True:
            recovered_data = {}

            with open(password_file_path, mode="r") as data_file:
                user_data_list = data_file.readlines()
                print(user_data_list)

            print("Looking for User")
            if f'"{username}":' in user_data_list[1] and '"key":' in user_data_list[2]:
                print("Found User")
                new_key = Fernet.generate_key()
                cipher = Fernet(new_key)

                user_password = user_data_list[1].replace(f'"{username}": ', "").replace('"', '').replace(",",
                                                                                                          "").replace(
                    " ", "")
                old_key = user_data_list[2].replace('"key": ', "").replace('"', "").replace(",", "").replace(" ", "")

                user_login_data = {
                    username: cipher.encrypt(
                        Fernet(self.main_fernet.decrypt(old_key)).decrypt(user_password)
                    ).decode(),
                    "key": self.main_fernet.encrypt(new_key).decode()
                }

                recovered_data = user_login_data

                print("Recovered login data")

                found_data_line = False

                recovered_service = ""
                recovered_username = ""
                recovered_password = ""
                recovered_key = ""

                print("Attempting to recover services")
                for line_data in user_data_list:
                    line_data = line_data.replace("\n,", "")
                    print(repr(line_data))

                    if "data" in line_data:
                        found_data_line = True
                        continue

                    print(found_data_line)

                    if recovered_service == "" and line_data != "" and found_data_line:
                        recovered_service = line_data.replace('"', '').replace(":", "").replace("{", "").replace(" ",
                                                                                                                 "").replace(
                            "\n", "")
                        print("Found service")

                        continue

                    if recovered_username == "" and line_data != "" and found_data_line:
                        recovered_username = line_data.replace('"', '').replace(":", "").replace("{", "").replace(" ",
                                                                                                                  "").replace(
                            "\n", "")
                        print("Found username")

                        continue

                    if recovered_password == "" and line_data != "" and found_data_line:
                        recovered_password = line_data.replace("password", "").replace('"', '').replace(":",
                                                                                                        "").replace("{",
                                                                                                                    "").replace(
                            " ", "").replace("\n", "")
                        print("Found password")

                        continue

                    if recovered_key == "" and line_data != "" and found_data_line:
                        recovered_key = line_data.replace("key", "").replace('"', '').replace(":", "").replace("{",
                                                                                                               "").replace(
                            " ", "").replace("\n", "")
                        print("Found key")

                        continue

                    if recovered_service != "" and \
                            recovered_username != "" and \
                            recovered_password != "" and \
                            recovered_key != "":

                        if "data" not in recovered_data.keys():
                            recovered_data["data"] = {}

                        if recovered_service not in recovered_data["data"].keys():
                            recovered_data["data"][recovered_service] = {
                                recovered_username: {
                                    "password": recovered_password,
                                    "key": recovered_key
                                }
                            }

                        elif recovered_username not in recovered_data["data"][recovered_service].keys():
                            recovered_data["data"][recovered_service][recovered_username] = {
                                "password": recovered_password,
                                "key": recovered_key
                            }

                with open(password_file_path, mode="w") as data_file:
                    json.dump(recovered_data, data_file, indent=4)

            return recovered_data

        else:
            return user_data
# --------------------- Server related functions ---------------------#

    async def collect_server_data(self, command_called: toga.Command):
        if self.logged_in_user is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Please login before configuring servers"
            )

            await self.dialog(dialog)
            return

        print(command_called.text)

        if command_called.text == "Add New Server":
            server_title_label = toga.Label(
                text="Server Title: \n(Can be whatever you want) ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            server_address_label = toga.Label(
                text="Server Address: ",
                style=self.label_style
            )

            self.server_address_entry = toga.TextInput(
                style=self.input_style
            )

            server_port_label = toga.Label(
                text="Server Port: ",
                style=self.label_style
            )

            self.server_port_entry = toga.TextInput(
                value="9000",
                style=self.input_style
            )

            add_server_button = toga.Button(
                text="Add Server",
                on_press=self.add_new_server,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    server_address_label,
                    self.server_address_entry,
                    server_port_label,
                    self.server_port_entry,
                    add_server_button
                ],
                clear_screen=True
            )

        elif command_called.text == "Edit Server":
            server_title_label = toga.Label(
                text="Server Title: \n(Can be whatever you want) ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            server_address_label = toga.Label(
                text="Server Address: ",
                style=self.label_style
            )

            self.server_address_entry = toga.TextInput(
                style=self.input_style
            )

            server_port_label = toga.Label(
                text="Server Port: ",
                style=self.label_style
            )

            self.server_port_entry = toga.TextInput(
                value="9000",
                style=self.input_style
            )

            edit_server_button = toga.Button(
                text="Edit Server",
                on_press=self.edit_server,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    server_address_label,
                    self.server_address_entry,
                    server_port_label,
                    self.server_port_entry,
                    edit_server_button
                ],
                clear_screen=True
            )

        elif command_called.text == "Delete Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            delete_server_button = toga.Button(
                text="Delete Server",
                on_press=self.delete_server,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    delete_server_button
                ],
                clear_screen=True
            )

        if command_called.text == "Upload Passwords to Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            sync_passwords_button = toga.Button(
                text="Upload Passwords",
                on_press=self.upload_passwords,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    sync_passwords_button
                ],
                clear_screen=True
            )

        elif command_called.text == "Download Passwords from Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            download_passwords_button = toga.Button(
                text="Download Passwords",
                on_press=self.download_passwords,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    download_passwords_button
                ],
                clear_screen=True
            )

        elif command_called.text == "Connect Server":
            server_title_label = toga.Label(
                text="Server Title: ",
                style=self.label_style
            )

            self.server_title_entry = toga.TextInput(
                style=self.input_style
            )

            connect_server_button = toga.Button(
                text="Connect to Server",
                on_press=self.connect_to_server,
                style=self.button_style
            )

            self.add_to_screen(
                widgets=[
                    server_title_label,
                    self.server_title_entry,
                    connect_server_button
                ],
                clear_screen=True
            )

    async def add_new_server(self, _):
        server_title = self.server_title_entry.value
        server_address = self.server_address_entry.value
        server_port = self.server_port_entry.value

        user_data = self.load_user_passwords()
        user_data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title,
                "Server Address": server_address,
                "Server Port": server_port
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        if "servers" not in user_data.keys():
            user_data["servers"] = {}

        for server in user_data["servers"].keys():
            if server_address in user_data["servers"][server].keys():
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message=f"Couldn't add new server. Server with address of {server_address} is already saved"
                )

                await self.dialog(dialog)
                return None

        if server_title in user_data["servers"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't add new server. Server titled {server_title} already exists"
            )

            await self.dialog(dialog)
            return None

        user_data["servers"][server_title] = {
            "server_address": server_address,
            "server_port": server_port
        }

        with open(user_data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully added new server titled {server_title}"
        )

        await self.dialog(dialog)

        return self.return_to_home_screen()

    async def edit_server(self, _):
        server_title = self.server_title_entry.value
        server_address = self.server_address_entry.value
        server_port = self.server_port_entry.value

        user_data = self.load_user_passwords()
        data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title,
                "Server Address": server_address,
                "Server Port": server_port
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return None

        server_exists = self.check_for_server(server_title)

        if not server_exists:
            return None

        del user_data["servers"][server_title]

        user_data["servers"][server_title] = {
            "server_address": server_address,
            "server_port": server_port
        }

        with open(data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully edited server {server_title}"
        )

        await self.dialog(dialog)

        return self.return_to_home_screen()

    async def delete_server(self, _):
        server_title = self.server_title_entry.value

        user_data = self.load_user_passwords()
        data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        is_valid = await self.validate_values(
            to_validate={
                "Server title": server_title
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return

        server_exists = await self.check_for_server(server_title)

        if not server_exists:
            return

        del user_data["servers"][server_title]

        with open(data_path, mode="w") as data_file:
            json.dump(user_data, data_file, indent=4)

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully deleted server {server_title}"
        )

        await self.dialog(dialog)
        return

    async def upload_passwords(self, _):
        if self.server is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No server is connected. Please connect to a server, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        server_title = self.server_title_entry.value

        user_data = self.load_user_passwords()

        is_valid = await self.validate_values(
            to_validate={
                "Server Title": server_title
            },
            message_for_dialog="<value> cannot be empty",
            inverse_check=True
        )

        if not is_valid:
            return self.return_to_home_screen()

        server_exists = await self.check_for_server(server_title)

        if not server_exists:
            return self.return_to_home_screen()

        if not "data" in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="Can't upload passwords. No passwords are saved"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        try:
            for_server = {}
            server_cipher = Fernet(self.server_key)

        except ValueError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="The server sent an invalid key. Please restart the app, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        for service in user_data["data"].keys():
            for username in user_data["data"][service].keys():
                encrypted_password = user_data["data"][service][username]["password"]
                encryption_key = user_data["data"][service][username]["key"]
                print(encryption_key)
                cipher = Fernet(self.main_fernet.decrypt(encryption_key))

                if service not in for_server.keys():
                    for_server[service] = {
                        username: {
                            "password": cipher.decrypt(encrypted_password).decode(),
                            "key": self.server_key.decode()
                        }
                    }

                else:
                    for_server[service][username] = {
                        "password": cipher.decrypt(encrypted_password).decode(),
                        "key": self.server_key.decode()
                    }

        encrypted_for_server_string: bytes = server_cipher.encrypt(
            self.main_fernet.encrypt(
                json.dumps(for_server).encode()
            )
        )

        print(f"Encrypted string is: {encrypted_for_server_string}")
        await asyncio.to_thread(self.server.sendall, encrypted_for_server_string)
        print("Sent data")

        await asyncio.to_thread(self.server.sendall, b"DONE")

        confirm_dialog = toga.QuestionDialog(
            title=self.confirm_title,
            message="Do you want to recursively update data on server (Doesn't replace deleted passwords)?"
        )

        update_recursively = await self.dialog(confirm_dialog)

        print(f"Update recursively is: {update_recursively}")

        if update_recursively:
            await asyncio.to_thread(self.server.sendall, server_cipher.encrypt(self.main_fernet.encrypt(b"RECURSIVE")))
            print("Sent recursive command to server")

        else:
            await asyncio.to_thread(self.server.sendall, server_cipher.encrypt(self.main_fernet.encrypt(b"REPLACE")))

        self.server.sendall(server_cipher.encrypt(self.main_fernet.encrypt(b"DONE")))
        print("Sent done message to server")

        message_from_server = await asyncio.to_thread(self.server.recv, 1024)

        if message_from_server.decode() == "Successfully updated data":
            dialog = toga.InfoDialog(
                title=self.success_title,
                message="Successfully updated data"
            )

            await self.dialog(dialog)

        else:
            print(message_from_server)

        await asyncio.to_thread(self.server.close)
        self.server = None

        return self.return_to_home_screen()

    async def download_passwords(self, button_called: toga.Button):
        if button_called.text == "Recover Passwords":
            server_address = self.server_address_entry.value
            server_port = int(self.server_port_entry.value)

            try:
                self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.connect((server_address, server_port))

            except ConnectionRefusedError:
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message=f"Couldn't connect to server. Connection to server was refused. Please make sure the server address is correct, and listening on port {server_port}"
                )

                await self.dialog(dialog)
                return self.return_to_home_screen()

            await asyncio.to_thread(self.server.sendall, self.user_entry.value.encode())
            encrypted_server_key = await asyncio.to_thread(self.server.recv, 1024)

            try:
                self.server_key = self.main_fernet.decrypt(encrypted_server_key)

            except ValueError:
                dialog = toga.ErrorDialog(
                    title=self.error_title,
                    message="The server sent an invalid key. Please restart the app, and try again"
                )

                await self.dialog(dialog)
                return self.return_to_home_screen()

        if self.server is None:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No server is connected. Please connect to a server, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        if not button_called.text == "Recover Passwords":
            server_title = self.server_title_entry.value

            data_path = os.path.join(self.paths.data, self.logged_in_user, ".passwords.json")

        else:
            data_path = os.path.join(self.paths.data, self.user_entry.value, ".passwords.json")

        if not button_called.text == "Recover Passwords":
            is_valid = await self.validate_values(
                to_validate={
                    "Server Title": server_title
                },
                message_for_dialog="<value> cannot be empty",
                inverse_check=True
            )

            if not is_valid:
                print("Invalid values")
                return None

            server_exists = await self.check_for_server(server_title)

            if not server_exists:
                return None

        print("Sending download command")
        self.server.sendall(
            Fernet(self.server_key).encrypt(self.main_fernet.encrypt(b"DOWNLOAD_DATA"))
        )

        print("Sent download command to server, await response")

        downloaded_user_data_str: str = await self.receive_all()

        if downloaded_user_data_str.startswith("Failed to download passwords. "):
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Failed to download password from server. Reason: {downloaded_user_data_str.replace('Failed to download passwords. ', '')}"
            )

            self.return_to_home_screen()
            return await self.dialog(dialog)

        await asyncio.to_thread(self.server.close)
        self.server = None

        print("Received response")

        if not button_called.text == "Recover Passwords":
            dialog = toga.ConfirmDialog(
                title=self.confirm_title,
                message=f"Are you sure you want to download all passwords from the server titled {server_title}? \n\n"
                        "NOTE: This will overwrite all your existing passwords. "
                        "Any passwords that aren't saved to the server, will be lost"
            )

            dialog_result = await self.dialog(dialog)

        else:
            dialog_result = True

        if dialog_result:
            downloaded_server_data = json_repair.loads(downloaded_user_data_str)

            for downloaded_service in downloaded_server_data.keys():
                for downloaded_username in downloaded_server_data[downloaded_service].keys():
                    password = downloaded_server_data[downloaded_service][downloaded_username]["password"]
                    key = downloaded_server_data[downloaded_service][downloaded_username]["key"]
                    cipher = Fernet(key.encode())

                    downloaded_server_data[downloaded_service][downloaded_username] = {
                        "password": cipher.encrypt(password.encode()).decode(),
                        "key": self.main_fernet.encrypt(key.encode()).decode()
                    }

            user = self.user_entry.value
            password = self.password_entry.value
            encryption_key = Fernet.generate_key()

            downloaded_user_data = {
                user: Fernet(encryption_key).encrypt(password.encode()).decode(),
                "key": self.main_fernet.encrypt(encryption_key).decode(),
                "data": downloaded_server_data,
                "servers": self.load_user_passwords()["servers"]
            }

            with open(data_path, mode="w") as data_file:
                json.dump(downloaded_user_data, data_file, indent=4)

            if not button_called.text == "Recover Passwords":
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message=f"Successfully downloaded passwords from server titled {server_title}"
                )

                await self.dialog(dialog)

            else:
                dialog = toga.InfoDialog(
                    title=self.success_title,
                    message="Successfully recovered data"
                )

                await self.dialog(dialog)

        return self.return_to_home_screen()

    async def connect_to_server(self, _):
        server_title = self.server_title_entry.value

        if self.server is not None:
            await asyncio.to_thread(self.server.close)

        server_exists = await self.check_for_server(server_title)

        print(f"Server exists: {server_exists}")

        if not server_exists:
            return None

        server_data = self.load_user_passwords()["servers"][server_title]
        print("Retrieved server data")

        try:
            print("Connecting to server")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.connect((server_data["server_address"], int(server_data["server_port"])))

            print("Was able to connect to server`")

        except ConnectionRefusedError:
            print("Connection was refused")
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"Couldn't connect to server titled {server_title}. Connection was refused. \n "
                        f"Please ensure the server is running and listening on port {server_data['server_port']}"
            )

            return await self.dialog(dialog)

        self.server.sendall(self.logged_in_user.encode())
        await asyncio.to_thread(self.server.sendall, os.environ["MAIN_KEY"].encode())
        print("Sent logged in user and main key")

        try:
            encrypted_server_key = await asyncio.to_thread(self.server.recv, 1024)
            self.server_key = self.main_fernet.decrypt(encrypted_server_key)

        except ValueError:
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="The server sent an invalid key. Please restart the app, and try again"
            )

            await self.dialog(dialog)
            return self.return_to_home_screen()

        dialog = toga.InfoDialog(
            title=self.success_title,
            message=f"Successfully connected to server titled {server_title}"
        )

        self.return_to_home_screen()
        return await self.dialog(dialog)

    async def check_for_server(self, server_title: str) -> bool:
        user_data = self.load_user_passwords()

        if "servers" not in user_data.keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message="No servers are saved. Please save a server, then try again"
            )

            await self.dialog(dialog)
            self.return_to_home_screen()
            return False

        if server_title not in user_data["servers"].keys():
            dialog = toga.ErrorDialog(
                title=self.error_title,
                message=f"No server titled {server_title} is saved"
            )

            await self.dialog(dialog)
            return False

        return True

    # --------------------- Utility related functions ---------------------#

    def add_to_screen(self, _=None, widgets: list[toga.Widget] = [], clear_screen=False):
        if clear_screen:
            self.a_box.clear()

        for widget in widgets:
            self.a_box.add(widget)

    async def receive_all(self) -> str:
        print("Receive_all called")
        print(self.server_key)
        cipher = Fernet(self.server_key)

        encrypted_received_data: bytes = b""

        while True:
            print("Receiving new data")
            new_received_data = self.server.recv(1024)

            print(
                f"\n ------------------------------ \n    Total received data: {encrypted_received_data} \n ------------------------------ ")
            print(
                f"\n ------------------------------ \n    New data received: {new_received_data} \n ------------------------------ ")

            try:
                print("Trying to decrypt total received data")

                encrypted_received_data += new_received_data
                decrypted_received_data: str = cipher.decrypt(
                    self.main_fernet.decrypt(encrypted_received_data)).decode()

            except cryptography.fernet.InvalidToken:
                print("Couldn't decrypt received data")

            else:
                print("Data was successfully decrypted, breaking out of while loop")
                encrypted_received_data = b""
                break

        return decrypted_received_data

    async def validate_values(self, to_validate: dict, message_for_dialog: str or None, expected_value: str = "",
                              dialog_to_raise=None, inverse_check: bool = False):
        """
        A function to validate a list of variables

        to_validate: dict    The list of variables to validate. The key will be used to replace <value> in
        message_for_dialog. The value will be what is checked for validity

        message_for_dialog: str or None    The message used when a ErrorDialog is automatically generated. If
        dialog_to_raise is not None, then this is not required. Wherever <value> is put in message_for_dialog,
        it will be replaced with the value of to_validate that is currently being validated

        expected_value: str = ""    The value that all values of to_validate will be checked for

        dialog_to_raise = None    The dialog that will be raised if any value of to_validate isn't valid. If None,
        message_for_dialog is required, and an ErrorDialog will automatically be generated.

        inverse_check: bool = False    If True, a dialog will only be created if any value of to_validate equals expected_value
        """

        for variable in to_validate.keys():
            variable_value = to_validate.get(variable)

            if dialog_to_raise is None:
                dialog_to_raise = toga.ErrorDialog(
                    title=self.error_title,
                    message=message_for_dialog.replace("<value>", variable)
                )
            if inverse_check is False and variable_value != expected_value:
                await self.dialog(dialog_to_raise)

                return False

            if inverse_check is True and variable_value == expected_value:
                await self.dialog(dialog_to_raise)

                return False

            if message_for_dialog is not None:
                dialog_to_raise = None

        return True

    @staticmethod
    def copy_to_clipboard(data_to_copy: str):
        if toga.platform.current_platform.lower() == "android" or "window" in toga.platform.current_platform.lower():
            cb = Clipboard.get_clipboard()

            cb.set_text(data_to_copy)

        else:
            pyperclip.copy(data_to_copy)

def main():
    return PyPass()
