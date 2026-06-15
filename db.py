"""
Single database layer. All teams, groups, matches, users, predictions live here.
Uses PostgreSQL via Supabase.
"""
import psycopg2
import psycopg2.extras
import secrets
import bcrypt
from datetime import datetime, timezone
from contextlib import contextmanager
import streamlit as st


def get_conn():
    return psycopg2.connect(
        st.secrets["SUPABASE_DB_URL"],
        sslmode="require",
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


@contextmanager
def _db():
    conn = get_conn()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Schema
# ─────────────────────────────────────────────────────────────────────────────
def init_schema():
    with _db() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id   SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id            SERIAL PRIMARY KEY,
                name          TEXT UNIQUE NOT NULL,
                flag          TEXT NOT NULL DEFAULT '',
                group_id      INTEGER REFERENCES groups(id),
                confederation TEXT NOT NULL DEFAULT ''
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS venues (
                id   SERIAL PRIMARY KEY,
                key  TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id          SERIAL PRIMARY KEY,
                group_id    INTEGER REFERENCES groups(id),
                home_id     INTEGER REFERENCES teams(id),
                away_id     INTEGER REFERENCES teams(id),
                kickoff_utc TEXT NOT NULL,
                venue_id    INTEGER REFERENCES venues(id),
                score_home  INTEGER,
                score_away  INTEGER
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id             SERIAL PRIMARY KEY,
                username       TEXT UNIQUE NOT NULL,
                email          TEXT UNIQUE NOT NULL,
                password_hash  TEXT NOT NULL,
                role           TEXT NOT NULL DEFAULT 'user',
                verified       INTEGER NOT NULL DEFAULT 0,
                favorite_team  TEXT DEFAULT '',
                tz_name        TEXT DEFAULT 'Jordan (UTC+3)',
                tz_offset      INTEGER DEFAULT 3,
                startup_points INTEGER NOT NULL DEFAULT 0,
                created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token      TEXT PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id           SERIAL PRIMARY KEY,
                user_id      INTEGER NOT NULL REFERENCES users(id),
                match_id     INTEGER NOT NULL REFERENCES matches(id),
                pred_home    INTEGER NOT NULL,
                pred_away    INTEGER NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, match_id)
            )
        """)
        # migration: add startup_points if missing
        c.execute("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS startup_points INTEGER NOT NULL DEFAULT 0
        """)


# ─────────────────────────────────────────────────────────────────────────────
# Seed lookup data
# ─────────────────────────────────────────────────────────────────────────────
_VENUES = [
    ("Azteca",    "Estadio Azteca, Mexico City"),
    ("Akron",     "Estadio Akron, Zapopan"),
    ("BBVA",      "Estadio BBVA, Guadalupe"),
    ("Jalisco",   "Estadio Jalisco, Guadalajara"),
    ("BMO",       "BMO Field, Toronto"),
    ("BC",        "BC Place, Vancouver"),
    ("Lumen",     "Lumen Field, Seattle"),
    ("MetLife",   "MetLife Stadium, East Rutherford NJ"),
    ("Gillette",  "Gillette Stadium, Foxborough MA"),
    ("HardRock",  "Hard Rock Stadium, Miami Gardens FL"),
    ("Lincoln",   "Lincoln Financial Field, Philadelphia"),
    ("ATT",       "AT&T Stadium, Arlington TX"),
    ("SoFi",      "SoFi Stadium, Inglewood CA"),
    ("Levis",     "Levi's Stadium, Santa Clara CA"),
    ("NRG",       "NRG Stadium, Houston TX"),
    ("Arrowhead", "Arrowhead Stadium, Kansas City MO"),
    ("Mercedes",  "Mercedes-Benz Stadium, Atlanta GA"),
]

# (name, flag, group, confederation)
_TEAMS = [
    ("Mexico",                 "🇲🇽", "A", "CONCACAF"),
    ("South Africa",           "🇿🇦", "A", "CAF"),
    ("Korea Republic",         "🇰🇷", "A", "AFC"),
    ("Czechia",                "🇨🇿", "A", "UEFA"),
    ("Canada",                 "🇨🇦", "B", "CONCACAF"),
    ("Bosnia and Herzegovina", "🇧🇦", "B", "UEFA"),
    ("Qatar",                  "🇶🇦", "B", "AFC"),
    ("Switzerland",            "🇨🇭", "B", "UEFA"),
    ("Brazil",                 "🇧🇷", "C", "CONMEBOL"),
    ("Morocco",                "🇲🇦", "C", "CAF"),
    ("Haiti",                  "🇭🇹", "C", "CONCACAF"),
    ("Scotland",               "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "C", "UEFA"),
    ("USA",                    "🇺🇸", "D", "CONCACAF"),
    ("Paraguay",               "🇵🇾", "D", "CONMEBOL"),
    ("Australia",              "🇦🇺", "D", "AFC"),
    ("Turkey",                 "🇹🇷", "D", "UEFA"),
    ("Germany",                "🇩🇪", "E", "UEFA"),
    ("Curaçao",                "🇨🇼", "E", "CONCACAF"),
    ("Ivory Coast",            "🇨🇮", "E", "CAF"),
    ("Ecuador",                "🇪🇨", "E", "CONMEBOL"),
    ("Netherlands",            "🇳🇱", "F", "UEFA"),
    ("Japan",                  "🇯🇵", "F", "AFC"),
    ("Sweden",                 "🇸🇪", "F", "UEFA"),
    ("Tunisia",                "🇹🇳", "F", "CAF"),
    ("Belgium",                "🇧🇪", "G", "UEFA"),
    ("Egypt",                  "🇪🇬", "G", "CAF"),
    ("Iran",                   "🇮🇷", "G", "AFC"),
    ("New Zealand",            "🇳🇿", "G", "OFC"),
    ("Spain",                  "🇪🇸", "H", "UEFA"),
    ("Uruguay",                "🇺🇾", "H", "CONMEBOL"),
    ("Saudi Arabia",           "🇸🇦", "H", "AFC"),
    ("Cape Verde",             "🇨🇻", "H", "CAF"),
    ("France",                 "🇫🇷", "I", "UEFA"),
    ("Senegal",                "🇸🇳", "I", "CAF"),
    ("Iraq",                   "🇮🇶", "I", "AFC"),
    ("Norway",                 "🇳🇴", "I", "UEFA"),
    ("Argentina",              "🇦🇷", "J", "CONMEBOL"),
    ("Algeria",                "🇩🇿", "J", "CAF"),
    ("Austria",                "🇦🇹", "J", "UEFA"),
    ("Jordan",                 "🇯🇴", "J", "AFC"),
    ("Portugal",               "🇵🇹", "K", "UEFA"),
    ("DR Congo",               "🇨🇩", "K", "CAF"),
    ("Uzbekistan",             "🇺🇿", "K", "AFC"),
    ("Colombia",               "🇨🇴", "K", "CONMEBOL"),
    ("England",                "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "L", "UEFA"),
    ("Croatia",                "🇭🇷", "L", "UEFA"),
    ("Ghana",                  "🇬🇭", "L", "CAF"),
    ("Panama",                 "🇵🇦", "L", "CONCACAF"),
]

# (home, away, kickoff_utc, venue_key, score_home, score_away)
_MATCHES = [
    ("Mexico",          "South Africa",           "2026-06-11T19:00", "Azteca",    2,    0),
    ("Korea Republic",  "Czechia",                "2026-06-12T02:00", "Akron",     2,    1),
    ("Czechia",         "South Africa",           "2026-06-18T16:00", "Mercedes",  None, None),
    ("Mexico",          "Korea Republic",         "2026-06-19T01:00", "Akron",     None, None),
    ("Czechia",         "Mexico",                 "2026-06-25T01:00", "Azteca",    None, None),
    ("South Africa",    "Korea Republic",         "2026-06-25T01:00", "BBVA",      None, None),
    ("Canada",          "Bosnia and Herzegovina", "2026-06-12T19:00", "BMO",       1,    1),
    ("Qatar",           "Switzerland",            "2026-06-13T19:00", "Levis",     None, None),
    ("Switzerland",     "Bosnia and Herzegovina", "2026-06-18T19:00", "SoFi",      None, None),
    ("Canada",          "Qatar",                  "2026-06-18T22:00", "BC",        None, None),
    ("Switzerland",     "Canada",                 "2026-06-24T19:00", "BC",        None, None),
    ("Bosnia and Herzegovina", "Qatar",           "2026-06-24T19:00", "Lumen",     None, None),
    ("Brazil",          "Morocco",                "2026-06-13T22:00", "MetLife",   None, None),
    ("Haiti",           "Scotland",               "2026-06-14T01:00", "Gillette",  None, None),
    ("Scotland",        "Morocco",                "2026-06-19T22:00", "Gillette",  None, None),
    ("Brazil",          "Haiti",                  "2026-06-20T00:30", "Lincoln",   None, None),
    ("Scotland",        "Brazil",                 "2026-06-24T22:00", "HardRock",  None, None),
    ("Morocco",         "Haiti",                  "2026-06-24T22:00", "Mercedes",  None, None),
    ("USA",             "Paraguay",               "2026-06-13T01:00", "SoFi",      4,    1),
    ("Australia",       "Turkey",                 "2026-06-14T04:00", "BC",        None, None),
    ("USA",             "Australia",              "2026-06-19T19:00", "Lumen",     None, None),
    ("Turkey",          "Paraguay",               "2026-06-20T03:00", "Levis",     None, None),
    ("Turkey",          "USA",                    "2026-06-26T02:00", "SoFi",      None, None),
    ("Paraguay",        "Australia",              "2026-06-26T02:00", "Levis",     None, None),
    ("Germany",         "Curaçao",                "2026-06-14T17:00", "NRG",       None, None),
    ("Ivory Coast",     "Ecuador",                "2026-06-14T23:00", "Lincoln",   None, None),
    ("Germany",         "Ivory Coast",            "2026-06-20T20:00", "BMO",       None, None),
    ("Ecuador",         "Curaçao",                "2026-06-21T00:00", "Arrowhead", None, None),
    ("Curaçao",         "Ivory Coast",            "2026-06-25T20:00", "Lincoln",   None, None),
    ("Ecuador",         "Germany",                "2026-06-25T20:00", "MetLife",   None, None),
    ("Netherlands",     "Japan",                  "2026-06-14T20:00", "ATT",       None, None),
    ("Sweden",          "Tunisia",                "2026-06-15T02:00", "BBVA",      None, None),
    ("Netherlands",     "Sweden",                 "2026-06-20T17:00", "NRG",       None, None),
    ("Tunisia",         "Japan",                  "2026-06-21T04:00", "BBVA",      None, None),
    ("Japan",           "Sweden",                 "2026-06-25T22:00", "ATT",       None, None),
    ("Tunisia",         "Netherlands",            "2026-06-25T23:00", "Arrowhead", None, None),
    ("Iran",            "New Zealand",            "2026-06-16T01:00", "SoFi",      None, None),
    ("Belgium",         "Egypt",                  "2026-06-16T02:00", "Lumen",     None, None),
    ("New Zealand",     "Egypt",                  "2026-06-22T01:00", "BC",        None, None),
    ("Belgium",         "Iran",                   "2026-06-22T02:00", "SoFi",      None, None),
    ("Egypt",           "Iran",                   "2026-06-27T03:00", "Lumen",     None, None),
    ("New Zealand",     "Belgium",                "2026-06-27T03:00", "BC",        None, None),
    ("Spain",           "Cape Verde",             "2026-06-15T16:00", "Mercedes",  None, None),
    ("Saudi Arabia",    "Uruguay",                "2026-06-15T22:00", "HardRock",  None, None),
    ("Spain",           "Saudi Arabia",           "2026-06-21T16:00", "Mercedes",  None, None),
    ("Uruguay",         "Cape Verde",             "2026-06-21T22:00", "HardRock",  None, None),
    ("Cape Verde",      "Saudi Arabia",           "2026-06-27T00:00", "NRG",       None, None),
    ("Uruguay",         "Spain",                  "2026-06-27T00:00", "Akron",     None, None),
    ("France",          "Senegal",                "2026-06-16T19:00", "MetLife",   None, None),
    ("Iraq",            "Norway",                 "2026-06-16T22:00", "Gillette",  None, None),
    ("France",          "Iraq",                   "2026-06-22T21:00", "Lincoln",   None, None),
    ("Norway",          "Senegal",                "2026-06-23T00:00", "MetLife",   None, None),
    ("Norway",          "France",                 "2026-06-26T19:00", "Gillette",  None, None),
    ("Senegal",         "Iraq",                   "2026-06-26T19:00", "BMO",       None, None),
    ("Argentina",       "Algeria",                "2026-06-17T01:00", "Arrowhead", None, None),
    ("Austria",         "Jordan",                 "2026-06-17T04:00", "Levis",     None, None),
    ("Argentina",       "Austria",                "2026-06-23T01:00", "ATT",       None, None),
    ("Jordan",          "Algeria",                "2026-06-23T04:00", "Levis",     None, None),
    ("Algeria",         "Austria",                "2026-06-28T01:00", "Arrowhead", None, None),
    ("Jordan",          "Argentina",              "2026-06-28T01:00", "ATT",       None, None),
    ("Portugal",        "DR Congo",               "2026-06-17T17:00", "NRG",       None, None),
    ("Uzbekistan",      "Colombia",               "2026-06-18T02:00", "Azteca",    None, None),
    ("Portugal",        "Uzbekistan",             "2026-06-23T17:00", "NRG",       None, None),
    ("Colombia",        "DR Congo",               "2026-06-24T02:00", "Akron",     None, None),
    ("Colombia",        "Portugal",               "2026-06-27T23:30", "HardRock",  None, None),
    ("DR Congo",        "Uzbekistan",             "2026-06-27T23:30", "Mercedes",  None, None),
    ("England",         "Croatia",                "2026-06-17T20:00", "ATT",       None, None),
    ("Ghana",           "Panama",                 "2026-06-17T23:00", "BMO",       None, None),
    ("England",         "Ghana",                  "2026-06-23T20:00", "Gillette",  None, None),
    ("Panama",          "Croatia",                "2026-06-23T23:00", "BMO",       None, None),
    ("Panama",          "England",                "2026-06-27T21:00", "MetLife",   None, None),
    ("Croatia",         "Ghana",                  "2026-06-27T21:00", "Lincoln",   None, None),
]

_SEED_USERS = [
    ("Mohammad Alhassan", "m.alhasan@minerets.com", "Minerets@2026",  "admin"),
    ("Mohammad Souqi",    "m.souqi@minerets.com",   "Minerets@2026",  "user"),
    ("Mohammad Jameel",   "m.jameel65@hotmail.com", "a28852000",      "admin"),
]


def seed_data():
    with _db() as c:
        # groups
        for g in "ABCDEFGHIJKL":
            c.execute("INSERT INTO groups(name) VALUES(%s) ON CONFLICT DO NOTHING", (g,))

        # venues
        for key, name in _VENUES:
            c.execute("INSERT INTO venues(key,name) VALUES(%s,%s) ON CONFLICT DO NOTHING", (key, name))

        # teams
        for name, flag, grp, conf in _TEAMS:
            c.execute("SELECT id FROM groups WHERE name=%s", (grp,))
            grp_id = c.fetchone()["id"]
            c.execute(
                "INSERT INTO teams(name,flag,group_id,confederation) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (name, flag, grp_id, conf),
            )

        # matches (only insert if table is empty)
        c.execute("SELECT COUNT(*) FROM matches")
        if c.fetchone()["count"] == 0:
            for home, away, kickoff, venue_key, sh, sa in _MATCHES:
                c.execute("SELECT id FROM teams WHERE name=%s", (home,))
                home_id = c.fetchone()["id"]
                c.execute("SELECT id FROM teams WHERE name=%s", (away,))
                away_id = c.fetchone()["id"]
                c.execute("SELECT id FROM venues WHERE key=%s", (venue_key,))
                venue_id = c.fetchone()["id"]
                c.execute("SELECT group_id FROM teams WHERE id=%s", (home_id,))
                grp_id = c.fetchone()["group_id"]
                c.execute(
                    "INSERT INTO matches(group_id,home_id,away_id,kickoff_utc,venue_id,score_home,score_away) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (grp_id, home_id, away_id, kickoff, venue_id, sh, sa),
                )

        # seed users — always verified
        for username, email, password, role in _SEED_USERS:
            c.execute("SELECT 1 FROM users WHERE email=%s", (email,))
            if not c.fetchone():
                pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                c.execute(
                    "INSERT INTO users(username,email,password_hash,role,verified) VALUES(%s,%s,%s,%s,1)",
                    (username, email, pw, role),
                )
            else:
                c.execute("UPDATE users SET verified=1 WHERE email=%s", (email,))


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────
def _now_utc():
    return datetime.now(timezone.utc)

def _parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)

def _status(kickoff_utc, score_home, score_away):
    if score_home is not None and score_away is not None:
        return "completed"
    if _now_utc() >= _parse(kickoff_utc):
        return "live"
    return "upcoming"

def _is_locked(kickoff_utc):
    return _now_utc() >= _parse(kickoff_utc)


def get_matches():
    with _db() as c:
        c.execute("""
            SELECT m.id, g.name AS grp,
                   ht.name AS home, ht.flag AS home_flag,
                   at.name AS away, at.flag AS away_flag,
                   m.kickoff_utc, v.name AS venue,
                   m.score_home, m.score_away
            FROM matches m
            JOIN groups g  ON g.id  = m.group_id
            JOIN teams  ht ON ht.id = m.home_id
            JOIN teams  at ON at.id = m.away_id
            JOIN venues v  ON v.id  = m.venue_id
            ORDER BY m.kickoff_utc, m.id
        """)
        rows = c.fetchall()
    out = []
    for r in rows:
        out.append({
            "id":          r["id"],
            "group":       r["grp"],
            "home":        r["home"],
            "home_flag":   r["home_flag"],
            "away":        r["away"],
            "away_flag":   r["away_flag"],
            "kickoff_utc": r["kickoff_utc"],
            "venue":       r["venue"],
            "score_home":  r["score_home"],
            "score_away":  r["score_away"],
            "status":      _status(r["kickoff_utc"], r["score_home"], r["score_away"]),
            "locked":      _is_locked(r["kickoff_utc"]),
        })
    return out


def get_teams():
    with _db() as c:
        c.execute("""
            SELECT t.id, t.name, t.flag, g.name AS grp, t.confederation
            FROM teams t JOIN groups g ON g.id=t.group_id
            ORDER BY g.name, t.name
        """)
        rows = c.fetchall()
    return [dict(r) for r in rows]


def get_groups():
    with _db() as c:
        c.execute("SELECT name FROM groups ORDER BY name")
        rows = c.fetchall()
    return [r["name"] for r in rows]


def get_standings():
    teams   = get_teams()
    matches = get_matches()
    s = {}
    for t in teams:
        s[t["name"]] = {"group": t["grp"], "flag": t["flag"],
                        "P":0,"W":0,"D":0,"L":0,"GF":0,"GA":0,"GD":0,"Pts":0}
    for m in matches:
        if m["status"] != "completed":
            continue
        h, a, sh, sa = m["home"], m["away"], m["score_home"], m["score_away"]
        for t in (h, a):
            if t not in s:
                s[t] = {"group":"?","flag":"🏳","P":0,"W":0,"D":0,"L":0,"GF":0,"GA":0,"GD":0,"Pts":0}
        s[h]["P"]+=1; s[a]["P"]+=1
        s[h]["GF"]+=sh; s[h]["GA"]+=sa
        s[a]["GF"]+=sa; s[a]["GA"]+=sh
        if sh>sa:   s[h]["W"]+=1; s[h]["Pts"]+=3; s[a]["L"]+=1
        elif sa>sh: s[a]["W"]+=1; s[a]["Pts"]+=3; s[h]["L"]+=1
        else:       s[h]["D"]+=1; s[h]["Pts"]+=1; s[a]["D"]+=1; s[a]["Pts"]+=1
    for t in s:
        s[t]["GD"] = s[t]["GF"] - s[t]["GA"]
    return s


# ─────────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────────
def calc_points(ph, pa, ah, aa):
    """3 pts: exact score. 1 pt: correct outcome. 0: wrong."""
    def outcome(h, a): return "H" if h > a else ("A" if a > h else "D")
    if ph == ah and pa == aa:
        return 3
    if outcome(ph, pa) == outcome(ah, aa):
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Predictions
# ─────────────────────────────────────────────────────────────────────────────
def save_prediction(user_id, match_id, pred_home, pred_away):
    with _db() as c:
        c.execute("""
            INSERT INTO predictions(user_id,match_id,pred_home,pred_away)
            VALUES(%s,%s,%s,%s)
            ON CONFLICT(user_id,match_id) DO UPDATE SET
              pred_home=EXCLUDED.pred_home,
              pred_away=EXCLUDED.pred_away,
              submitted_at=CURRENT_TIMESTAMP
        """, (user_id, match_id, pred_home, pred_away))


def get_user_predictions(user_id):
    with _db() as c:
        c.execute(
            "SELECT match_id,pred_home,pred_away FROM predictions WHERE user_id=%s",
            (user_id,),
        )
        rows = c.fetchall()
    return {r["match_id"]: (r["pred_home"], r["pred_away"]) for r in rows}


def get_all_predictions():
    """Returns {match_id: {username: (pred_home, pred_away)}} for all matches."""
    with _db() as c:
        c.execute("""
            SELECT p.match_id, u.username, p.pred_home, p.pred_away
            FROM predictions p JOIN users u ON u.id = p.user_id
        """)
        rows = c.fetchall()
    result = {}
    for r in rows:
        result.setdefault(r["match_id"], {})[r["username"]] = (r["pred_home"], r["pred_away"])
    return result


def get_all_predictions_for_match(match_id):
    with _db() as c:
        c.execute("""
            SELECT u.username, p.pred_home, p.pred_away, p.submitted_at
            FROM predictions p JOIN users u ON u.id=p.user_id
            WHERE p.match_id=%s
            ORDER BY u.username
        """, (match_id,))
        rows = c.fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Admin: update match result
# ─────────────────────────────────────────────────────────────────────────────
def set_match_result(match_id, score_home, score_away):
    with _db() as c:
        c.execute(
            "UPDATE matches SET score_home=%s, score_away=%s WHERE id=%s",
            (score_home, score_away, match_id),
        )


def clear_match_result(match_id):
    with _db() as c:
        c.execute(
            "UPDATE matches SET score_home=NULL, score_away=NULL WHERE id=%s",
            (match_id,),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Leaderboard
# ─────────────────────────────────────────────────────────────────────────────
def get_leaderboard():
    matches   = get_matches()
    completed = {m["id"]: m for m in matches if m["status"] == "completed"}

    with _db() as c:
        c.execute("SELECT id, username, favorite_team, startup_points FROM users ORDER BY username")
        users = c.fetchall()
        c.execute("SELECT user_id,match_id,pred_home,pred_away FROM predictions")
        all_pred = c.fetchall()

    upreds = {}
    for p in all_pred:
        upreds.setdefault(p["user_id"], []).append(p)

    rows = []
    for u in users:
        preds   = upreds.get(u["id"], [])
        startup = u["startup_points"] or 0
        pts = exact = winner = wrong = 0
        for p in preds:
            m = completed.get(p["match_id"])
            if m:
                pt = calc_points(p["pred_home"], p["pred_away"], m["score_home"], m["score_away"])
                pts += pt
                if pt == 3:   exact  += 1
                elif pt == 1: winner += 1
                else:         wrong  += 1
        no_pred_on_done = len(completed) - sum(
            1 for p in preds if p["match_id"] in completed
        )
        rows.append({
            "username":       u["username"],
            "fav_team":       u["favorite_team"] or "",
            "points":         pts + startup,
            "match_points":   pts,
            "startup_points": startup,
            "exact":          exact,
            "winner":         winner,
            "wrong":          wrong,
            "no_pred":        no_pred_on_done,
            "total_pred":     len(preds),
        })
    rows.sort(key=lambda x: (-x["points"], -x["exact"], -x["winner"]))
    return rows


def set_user_startup_points(user_id: int, points: int):
    with _db() as c:
        c.execute("UPDATE users SET startup_points=%s WHERE id=%s", (points, user_id))


# ─────────────────────────────────────────────────────────────────────────────
# User auth
# ─────────────────────────────────────────────────────────────────────────────
def register_user(username, email, password):
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with _db() as c:
            c.execute(
                "INSERT INTO users(username,email,password_hash,role,verified) VALUES(%s,%s,%s,'user',0)",
                (username.strip(), email.strip().lower(), pw),
            )
        return True, "Account created! Please wait for admin verification before you can access the app."
    except Exception as e:
        msg = str(e)
        if "username" in msg: return False, "Username already taken."
        if "email"    in msg: return False, "Email already registered."
        return False, "Registration failed."


def login_user(identifier, password):
    """Returns (status, user_dict). status: 'ok' | 'bad_credentials' | 'pending'"""
    with _db() as c:
        c.execute(
            "SELECT * FROM users WHERE username=%s OR email=%s",
            (identifier.strip(), identifier.strip().lower()),
        )
        row = c.fetchone()
    if not row:
        return "bad_credentials", None
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return "bad_credentials", None
    verified = row["verified"]
    if str(verified) not in ("1", "True", "true"):
        return "pending", dict(row)
    return "ok", dict(row)


def update_user_field(user_id, field, value):
    allowed = {"favorite_team", "tz_name", "tz_offset"}
    if field not in allowed:
        return
    with _db() as c:
        c.execute(f"UPDATE users SET {field}=%s WHERE id=%s", (value, user_id))


def get_all_users():
    with _db() as c:
        c.execute(
            "SELECT id,username,email,role,verified,favorite_team,created_at FROM users ORDER BY username"
        )
        rows = c.fetchall()
    return [dict(r) for r in rows]


def set_user_role(user_id, role):
    with _db() as c:
        c.execute("UPDATE users SET role=%s WHERE id=%s", (role, user_id))


def set_user_verified(user_id, verified: bool):
    with _db() as c:
        c.execute("UPDATE users SET verified=%s WHERE id=%s", (1 if verified else 0, user_id))


def get_pending_users():
    with _db() as c:
        c.execute(
            "SELECT id,username,email,created_at FROM users WHERE verified=0 ORDER BY created_at"
        )
        rows = c.fetchall()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────────────────────────────────────
def create_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    with _db() as c:
        c.execute("INSERT INTO sessions(token,user_id) VALUES(%s,%s)", (token, user_id))
    return token


def get_session_user(token: str) -> dict | None:
    if not token:
        return None
    with _db() as c:
        c.execute("""
            SELECT u.* FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = %s
        """, (token,))
        row = c.fetchone()
    if not row:
        return None
    if str(row["verified"]) not in ("1", "True", "true"):
        return None
    return dict(row)


def delete_session(token: str):
    if token:
        with _db() as c:
            c.execute("DELETE FROM sessions WHERE token=%s", (token,))
