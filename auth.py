import sqlite3
import bcrypt
import streamlit as st
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

# Match IDs whose scores are fixed and cannot be overridden by anyone.
# Mexico 2-0 South Africa (id=1), Korea Republic 2-1 Czechia (id=2),
# Canada 1-1 Bosnia (id=7), USA 4-1 Paraguay (id=19)
LOCKED_RESULT_IDS = {1, 2, 7, 19}


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                favorite_team TEXT DEFAULT '',
                tz_name TEXT DEFAULT 'Jordan (UTC+3)',
                tz_offset INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add tz columns if upgrading an existing DB
        for col, default in [("tz_name", "'Jordan (UTC+3)'"), ("tz_offset", "3")]:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT DEFAULT {default}")
            except Exception:
                pass
        conn.commit()
    _seed_users()


def _seed_users():
    seeds = [
        ("Mohammad Alhassan", "m.alhasan@minerets.com",  "Minerets@2026"),
        ("Mohammad Souqi",    "m.souqi@minerets.com",    "Minerets@2026"),
    ]
    with _get_conn() as conn:
        for username, email, password in seeds:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE email = ?", (email,)
            ).fetchone()
            if not exists:
                pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, pw_hash),
                )
        conn.commit()


def init_predictions_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                pred_home INTEGER NOT NULL,
                pred_away INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, match_id)
            )
        """)
        conn.commit()


def save_prediction(user_id: int, match_id: int, pred_home: int, pred_away: int) -> tuple[bool, str]:
    if match_id in LOCKED_RESULT_IDS:
        return False, "This match result is official and cannot be predicted."
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO predictions (user_id, match_id, pred_home, pred_away)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, match_id) DO UPDATE SET
               pred_home=excluded.pred_home, pred_away=excluded.pred_away,
               created_at=CURRENT_TIMESTAMP""",
            (user_id, match_id, pred_home, pred_away),
        )
        conn.commit()
    return True, "Prediction saved."


def get_user_predictions(user_id: int) -> dict:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT match_id, pred_home, pred_away FROM predictions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    return {r["match_id"]: (r["pred_home"], r["pred_away"]) for r in rows}


def get_leaderboard() -> list:
    from data import MATCHES, calc_points
    completed = {m["id"]: m for m in MATCHES if m["status"] == "completed"}

    with _get_conn() as conn:
        users = conn.execute("SELECT id, username, favorite_team FROM users").fetchall()
        all_preds = conn.execute(
            "SELECT user_id, match_id, pred_home, pred_away FROM predictions"
        ).fetchall()

    user_preds: dict[int, list] = {}
    for p in all_preds:
        user_preds.setdefault(p["user_id"], []).append(p)

    results = []
    for u in users:
        preds = user_preds.get(u["id"], [])
        total_pts = exact = winner = missed = 0
        for p in preds:
            m = completed.get(p["match_id"])
            if m:
                pts = calc_points(p["pred_home"], p["pred_away"], m["score_home"], m["score_away"])
                total_pts += pts
                if pts == 3:
                    exact += 1
                elif pts == 1:
                    winner += 1
                else:
                    missed += 1
        results.append({
            "username":         u["username"],
            "favorite_team":    u["favorite_team"] or "",
            "points":           total_pts,
            "exact":            exact,
            "winner":           winner,
            "missed":           missed,
            "predictions_made": len(preds),
        })

    results.sort(key=lambda x: (-x["points"], -x["exact"], -x["winner"]))
    return results


def update_favorite_team(user_id: int, team: str):
    with _get_conn() as conn:
        conn.execute("UPDATE users SET favorite_team = ? WHERE id = ?", (team, user_id))
        conn.commit()


def update_timezone(user_id: int, tz_name: str, tz_offset: int):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE users SET tz_name = ?, tz_offset = ? WHERE id = ?",
            (tz_name, tz_offset, user_id),
        )
        conn.commit()


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username.strip(), email.strip().lower(), pw_hash),
            )
            conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "Username already taken."
        if "email" in str(e):
            return False, "Email already registered."
        return False, "Registration failed."


def login_user(username_or_email: str, password: str) -> tuple[bool, dict | None]:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_email.strip(), username_or_email.strip().lower()),
        ).fetchone()
    if row is None:
        return False, None
    if bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return True, dict(row)
    return False, None


def render_auth_page():
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0 1rem 0;'>
        <h1 style='font-size:2.5rem; color:#8B0000;'>&#x26BD; World Cup 2026</h1>
        <p style='color:#555; font-size:1.1rem;'>USA &bull; Canada &bull; Mexico</p>
    </div>
    """, unsafe_allow_html=True)

    tab_login, tab_register = st.tabs(["Login", "Create Account"])

    with tab_login:
        with st.form("login_form"):
            identifier = st.text_input("Username or Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            if not identifier or not password:
                st.error("Please fill in all fields.")
            else:
                ok, user = login_user(identifier, password)
                if ok:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

    with tab_register:
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_user")
            new_email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type="password", key="reg_pw")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_pw2")
            submitted_reg = st.form_submit_button("Create Account", use_container_width=True)
        if submitted_reg:
            if not all([new_username, new_email, new_password, confirm_password]):
                st.error("Please fill in all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                ok, msg = register_user(new_username, new_email, new_password)
                if ok:
                    st.success(msg + " Please login.")
                else:
                    st.error(msg)

    return "user" in st.session_state
