from datetime import datetime, timezone

# ── Helpers ───────────────────────────────────────────────────────────────────
def _now_utc():
    return datetime.now(timezone.utc)

def _parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)

def compute_status(kickoff_utc_str, score_home, score_away):
    if score_home is not None and score_away is not None:
        return "completed"
    if _now_utc() >= _parse_utc(kickoff_utc_str):
        return "live"
    return "upcoming"

def is_locked(kickoff_utc_str):
    return _now_utc() >= _parse_utc(kickoff_utc_str)

def calc_points(pred_h, pred_a, actual_h, actual_a):
    if pred_h == actual_h and pred_a == actual_a:
        return 3
    def outcome(h, a): return "H" if h > a else ("A" if a > h else "D")
    if outcome(pred_h, pred_a) == outcome(actual_h, actual_a):
        return 1
    return 0

# ── Teams (48) ────────────────────────────────────────────────────────────────
TEAMS = {
    # Group A
    "Mexico":                 {"flag": "🇲🇽", "group": "A", "conf": "CONCACAF"},
    "South Africa":           {"flag": "🇿🇦", "group": "A", "conf": "CAF"},
    "Korea Republic":         {"flag": "🇰🇷", "group": "A", "conf": "AFC"},
    "Czechia":                {"flag": "🇨🇿", "group": "A", "conf": "UEFA"},
    # Group B
    "Canada":                 {"flag": "🇨🇦", "group": "B", "conf": "CONCACAF"},
    "Bosnia and Herzegovina": {"flag": "🇧🇦", "group": "B", "conf": "UEFA"},
    "Qatar":                  {"flag": "🇶🇦", "group": "B", "conf": "AFC"},
    "Switzerland":            {"flag": "🇨🇭", "group": "B", "conf": "UEFA"},
    # Group C
    "Brazil":                 {"flag": "🇧🇷", "group": "C", "conf": "CONMEBOL"},
    "Morocco":                {"flag": "🇲🇦", "group": "C", "conf": "CAF"},
    "Haiti":                  {"flag": "🇭🇹", "group": "C", "conf": "CONCACAF"},
    "Scotland":               {"flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "group": "C", "conf": "UEFA"},
    # Group D
    "USA":                    {"flag": "🇺🇸", "group": "D", "conf": "CONCACAF"},
    "Paraguay":               {"flag": "🇵🇾", "group": "D", "conf": "CONMEBOL"},
    "Australia":              {"flag": "🇦🇺", "group": "D", "conf": "AFC"},
    "Turkey":                 {"flag": "🇹🇷", "group": "D", "conf": "UEFA"},
    # Group E
    "Germany":                {"flag": "🇩🇪", "group": "E", "conf": "UEFA"},
    "Curaçao":                {"flag": "🇨🇼", "group": "E", "conf": "CONCACAF"},
    "Ivory Coast":            {"flag": "🇨🇮", "group": "E", "conf": "CAF"},
    "Ecuador":                {"flag": "🇪🇨", "group": "E", "conf": "CONMEBOL"},
    # Group F
    "Netherlands":            {"flag": "🇳🇱", "group": "F", "conf": "UEFA"},
    "Japan":                  {"flag": "🇯🇵", "group": "F", "conf": "AFC"},
    "Sweden":                 {"flag": "🇸🇪", "group": "F", "conf": "UEFA"},
    "Tunisia":                {"flag": "🇹🇳", "group": "F", "conf": "CAF"},
    # Group G
    "Belgium":                {"flag": "🇧🇪", "group": "G", "conf": "UEFA"},
    "Egypt":                  {"flag": "🇪🇬", "group": "G", "conf": "CAF"},
    "Iran":                   {"flag": "🇮🇷", "group": "G", "conf": "AFC"},
    "New Zealand":            {"flag": "🇳🇿", "group": "G", "conf": "OFC"},
    # Group H
    "Spain":                  {"flag": "🇪🇸", "group": "H", "conf": "UEFA"},
    "Uruguay":                {"flag": "🇺🇾", "group": "H", "conf": "CONMEBOL"},
    "Saudi Arabia":           {"flag": "🇸🇦", "group": "H", "conf": "AFC"},
    "Cape Verde":             {"flag": "🇨🇻", "group": "H", "conf": "CAF"},
    # Group I
    "France":                 {"flag": "🇫🇷", "group": "I", "conf": "UEFA"},
    "Senegal":                {"flag": "🇸🇳", "group": "I", "conf": "CAF"},
    "Iraq":                   {"flag": "🇮🇶", "group": "I", "conf": "AFC"},
    "Norway":                 {"flag": "🇳🇴", "group": "I", "conf": "UEFA"},
    # Group J
    "Argentina":              {"flag": "🇦🇷", "group": "J", "conf": "CONMEBOL"},
    "Algeria":                {"flag": "🇩🇿", "group": "J", "conf": "CAF"},
    "Austria":                {"flag": "🇦🇹", "group": "J", "conf": "UEFA"},
    "Jordan":                 {"flag": "🇯🇴", "group": "J", "conf": "AFC"},
    # Group K
    "Portugal":               {"flag": "🇵🇹", "group": "K", "conf": "UEFA"},
    "DR Congo":               {"flag": "🇨🇩", "group": "K", "conf": "CAF"},
    "Uzbekistan":             {"flag": "🇺🇿", "group": "K", "conf": "AFC"},
    "Colombia":               {"flag": "🇨🇴", "group": "K", "conf": "CONMEBOL"},
    # Group L
    "England":                {"flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "group": "L", "conf": "UEFA"},
    "Croatia":                {"flag": "🇭🇷", "group": "L", "conf": "UEFA"},
    "Ghana":                  {"flag": "🇬🇭", "group": "L", "conf": "CAF"},
    "Panama":                 {"flag": "🇵🇦", "group": "L", "conf": "CONCACAF"},
}

# ── Venues ────────────────────────────────────────────────────────────────────
VENUES = {
    "Azteca":    "Estadio Azteca, Mexico City",
    "Akron":     "Estadio Akron, Zapopan",
    "BBVA":      "Estadio BBVA, Guadalupe",
    "Jalisco":   "Estadio Jalisco, Guadalajara",
    "BMO":       "BMO Field, Toronto",
    "BC":        "BC Place, Vancouver",
    "Lumen":     "Lumen Field, Seattle",
    "MetLife":   "MetLife Stadium, East Rutherford NJ",
    "Gillette":  "Gillette Stadium, Foxborough MA",
    "HardRock":  "Hard Rock Stadium, Miami Gardens FL",
    "Lincoln":   "Lincoln Financial Field, Philadelphia",
    "ATT":       "AT&T Stadium, Arlington TX",
    "SoFi":      "SoFi Stadium, Inglewood CA",
    "Levis":     "Levi's Stadium, Santa Clara CA",
    "NRG":       "NRG Stadium, Houston TX",
    "Arrowhead": "Arrowhead Stadium, Kansas City MO",
    "Mercedes":  "Mercedes-Benz Stadium, Atlanta GA",
}

# ── Raw matches ───────────────────────────────────────────────────────────────
# (home, away, kickoff_utc "YYYY-MM-DDTHH:MM", venue_key, score_home, score_away)
RAW_MATCHES = [
    # ── GROUP A ──────────────────────────────────────────────────────────────
    ("Mexico",          "South Africa",           "2026-06-11T19:00", "Azteca",    2,    0),
    ("Korea Republic",  "Czechia",              "2026-06-12T02:00", "Akron",     2,    1),
    ("Czechia",         "South Africa",         "2026-06-18T16:00", "Mercedes",  None, None),
    ("Mexico",          "Korea Republic",       "2026-06-19T01:00", "Akron",     None, None),
    ("Czechia",         "Mexico",               "2026-06-25T01:00", "Azteca",    None, None),
    ("South Africa",    "Korea Republic",       "2026-06-25T01:00", "BBVA",      None, None),
    # ── GROUP B ──────────────────────────────────────────────────────────────
    ("Canada",       "Bosnia and Herzegovina", "2026-06-12T19:00", "BMO",       1,    1),
    ("Qatar",        "Switzerland",            "2026-06-13T19:00", "Levis",     None, None),
    ("Switzerland",  "Bosnia and Herzegovina", "2026-06-18T19:00", "SoFi",      None, None),
    ("Canada",       "Qatar",                  "2026-06-18T22:00", "BC",        None, None),
    ("Switzerland",  "Canada",                 "2026-06-24T19:00", "BC",        None, None),
    ("Bosnia and Herzegovina","Qatar",         "2026-06-24T19:00", "Lumen",     None, None),
    # ── GROUP C ──────────────────────────────────────────────────────────────
    ("Brazil",       "Morocco",                "2026-06-13T22:00", "MetLife",   None, None),
    ("Haiti",        "Scotland",               "2026-06-14T01:00", "Gillette",  None, None),
    ("Scotland",     "Morocco",                "2026-06-19T22:00", "Gillette",  None, None),
    ("Brazil",       "Haiti",                  "2026-06-20T00:30", "Lincoln",   None, None),
    ("Scotland",     "Brazil",                 "2026-06-24T22:00", "HardRock",  None, None),
    ("Morocco",      "Haiti",                  "2026-06-24T22:00", "Mercedes",  None, None),
    # ── GROUP D ──────────────────────────────────────────────────────────────
    ("USA",          "Paraguay",               "2026-06-13T01:00", "SoFi",      4,    1),
    ("Australia",    "Turkey",                 "2026-06-14T04:00", "BC",        None, None),
    ("USA",          "Australia",              "2026-06-19T19:00", "Lumen",     None, None),
    ("Turkey",       "Paraguay",               "2026-06-20T03:00", "Levis",     None, None),
    ("Turkey",       "USA",                    "2026-06-26T02:00", "SoFi",      None, None),
    ("Paraguay",     "Australia",              "2026-06-26T02:00", "Levis",     None, None),
    # ── GROUP E ──────────────────────────────────────────────────────────────
    ("Germany",      "Curaçao",                "2026-06-14T17:00", "NRG",       None, None),
    ("Ivory Coast",  "Ecuador",                "2026-06-14T23:00", "Lincoln",   None, None),
    ("Germany",      "Ivory Coast",            "2026-06-20T20:00", "BMO",       None, None),
    ("Ecuador",      "Curaçao",                "2026-06-21T00:00", "Arrowhead", None, None),
    ("Curaçao",      "Ivory Coast",            "2026-06-25T20:00", "Lincoln",   None, None),
    ("Ecuador",      "Germany",                "2026-06-25T20:00", "MetLife",   None, None),
    # ── GROUP F ──────────────────────────────────────────────────────────────
    ("Netherlands",  "Japan",                  "2026-06-14T20:00", "ATT",       None, None),
    ("Sweden",       "Tunisia",                "2026-06-15T02:00", "BBVA",      None, None),
    ("Netherlands",  "Sweden",                 "2026-06-20T17:00", "NRG",       None, None),
    ("Tunisia",      "Japan",                  "2026-06-21T04:00", "BBVA",      None, None),
    ("Japan",        "Sweden",                 "2026-06-25T22:00", "ATT",       None, None),
    ("Tunisia",      "Netherlands",            "2026-06-25T23:00", "Arrowhead", None, None),
    # ── GROUP G ──────────────────────────────────────────────────────────────
    ("Iran",         "New Zealand",            "2026-06-16T01:00", "SoFi",      None, None),
    ("Belgium",      "Egypt",                  "2026-06-16T02:00", "Lumen",     None, None),
    ("New Zealand",  "Egypt",                  "2026-06-22T01:00", "BC",        None, None),
    ("Belgium",      "Iran",                   "2026-06-22T02:00", "SoFi",      None, None),
    ("Egypt",        "Iran",                   "2026-06-27T03:00", "Lumen",     None, None),
    ("New Zealand",  "Belgium",                "2026-06-27T03:00", "BC",        None, None),
    # ── GROUP H ──────────────────────────────────────────────────────────────
    ("Spain",        "Cape Verde",             "2026-06-15T16:00", "Mercedes",  None, None),
    ("Saudi Arabia", "Uruguay",                "2026-06-15T22:00", "HardRock",  None, None),
    ("Spain",        "Saudi Arabia",           "2026-06-21T16:00", "Mercedes",  None, None),
    ("Uruguay",      "Cape Verde",             "2026-06-21T22:00", "HardRock",  None, None),
    ("Cape Verde",   "Saudi Arabia",           "2026-06-27T00:00", "NRG",       None, None),
    ("Uruguay",      "Spain",                  "2026-06-27T00:00", "Akron",     None, None),
    # ── GROUP I ──────────────────────────────────────────────────────────────
    ("France",       "Senegal",                "2026-06-16T19:00", "MetLife",   None, None),
    ("Iraq",         "Norway",                 "2026-06-16T22:00", "Gillette",  None, None),
    ("France",       "Iraq",                   "2026-06-22T21:00", "Lincoln",   None, None),
    ("Norway",       "Senegal",                "2026-06-23T00:00", "MetLife",   None, None),
    ("Norway",       "France",                 "2026-06-26T19:00", "Gillette",  None, None),
    ("Senegal",      "Iraq",                   "2026-06-26T19:00", "BMO",       None, None),
    # ── GROUP J ──────────────────────────────────────────────────────────────
    ("Argentina",    "Algeria",                "2026-06-17T01:00", "Arrowhead", None, None),
    ("Austria",      "Jordan",                 "2026-06-17T04:00", "Levis",     None, None),
    ("Argentina",    "Austria",                "2026-06-23T01:00", "ATT",       None, None),
    ("Jordan",       "Algeria",                "2026-06-23T04:00", "Levis",     None, None),
    ("Algeria",      "Austria",                "2026-06-28T01:00", "Arrowhead", None, None),
    ("Jordan",       "Argentina",              "2026-06-28T01:00", "ATT",       None, None),
    # ── GROUP K ──────────────────────────────────────────────────────────────
    ("Portugal",     "DR Congo",               "2026-06-17T17:00", "NRG",       None, None),
    ("Uzbekistan",   "Colombia",               "2026-06-18T02:00", "Azteca",    None, None),
    ("Portugal",     "Uzbekistan",             "2026-06-23T17:00", "NRG",       None, None),
    ("Colombia",     "DR Congo",               "2026-06-24T02:00", "Akron",     None, None),
    ("Colombia",     "Portugal",               "2026-06-27T23:30", "HardRock",  None, None),
    ("DR Congo",     "Uzbekistan",             "2026-06-27T23:30", "Mercedes",  None, None),
    # ── GROUP L ──────────────────────────────────────────────────────────────
    ("England",      "Croatia",                "2026-06-17T20:00", "ATT",       None, None),
    ("Ghana",        "Panama",                 "2026-06-17T23:00", "BMO",       None, None),
    ("England",      "Ghana",                  "2026-06-23T20:00", "Gillette",  None, None),
    ("Panama",       "Croatia",                "2026-06-23T23:00", "BMO",       None, None),
    ("Panama",       "England",                "2026-06-27T21:00", "MetLife",   None, None),
    ("Croatia",      "Ghana",                  "2026-06-27T21:00", "Lincoln",   None, None),
]


def build_matches():
    matches = []
    for i, row in enumerate(RAW_MATCHES, start=1):
        home, away, kickoff_utc, venue_key, sh, sa = row
        group = TEAMS.get(home, {}).get("group", "?")
        matches.append({
            "id":           i,
            "group":        group,
            "home":         home,
            "away":         away,
            "home_flag":    TEAMS.get(home, {}).get("flag", "🏳"),
            "away_flag":    TEAMS.get(away, {}).get("flag", "🏳"),
            "kickoff_utc":  kickoff_utc,
            "venue":        VENUES.get(venue_key, venue_key),
            "score_home":   sh,
            "score_away":   sa,
            "status":       compute_status(kickoff_utc, sh, sa),
            "locked":       is_locked(kickoff_utc),
        })
    return matches


def compute_standings():
    standings = {t: {"group": info["group"], "flag": info["flag"],
                     "P":0,"W":0,"D":0,"L":0,"GF":0,"GA":0,"GD":0,"Pts":0}
                 for t, info in TEAMS.items()}
    for m in MATCHES:
        if m["status"] != "completed":
            continue
        h, a, sh, sa = m["home"], m["away"], m["score_home"], m["score_away"]
        standings[h]["P"] += 1; standings[a]["P"] += 1
        standings[h]["GF"] += sh; standings[h]["GA"] += sa
        standings[a]["GF"] += sa; standings[a]["GA"] += sh
        if sh > sa:
            standings[h]["W"] += 1; standings[h]["Pts"] += 3; standings[a]["L"] += 1
        elif sa > sh:
            standings[a]["W"] += 1; standings[a]["Pts"] += 3; standings[h]["L"] += 1
        else:
            standings[h]["D"] += 1; standings[h]["Pts"] += 1
            standings[a]["D"] += 1; standings[a]["Pts"] += 1
    for t in standings:
        standings[t]["GD"] = standings[t]["GF"] - standings[t]["GA"]
    return standings


MATCHES = build_matches()
STANDINGS = compute_standings()
ALL_TEAMS_LIST = sorted(TEAMS.keys())
GROUPS = {g: [t for t, info in TEAMS.items() if info["group"] == g]
          for g in "ABCDEFGHIJKL"}

# Match IDs with official fixed results that no user may predict on
LOCKED_RESULT_IDS = {1, 2, 7, 19}
