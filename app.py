import streamlit as st

st.set_page_config(
    page_title="World Cup 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from style import inject_css
from db import (init_schema, seed_data, login_user, register_user,
                create_session, get_session_user, delete_session)
import pages.home        as pg_home
import pages.schedule    as pg_schedule
import pages.groups      as pg_groups
import pages.results     as pg_results
import pages.predict     as pg_predict
import pages.scores      as pg_scores
import pages.leaderboard as pg_leaderboard
import pages.admin       as pg_admin
import pages.profile     as pg_profile

inject_css()

@st.cache_resource
def _init_db():
    init_schema()
    seed_data()

_init_db()

# ── Cookie-based session ───────────────────────────────────────────────────────
import extra_streamlit_components as stx

COOKIE_NAME = "wc2026_session"
COOKIE_TTL  = 30  # days

cookie_mgr = stx.CookieManager(key="wc2026_cm")

if "user" not in st.session_state:
    token = cookie_mgr.get(COOKIE_NAME)
    if token and len(token) > 10:
        restored = get_session_user(token)
        if restored:
            st.session_state["user"]          = restored
            st.session_state["session_token"] = token

# ── Auth gate ──────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.markdown("""
    <div style='text-align:center;padding:2rem 0 1rem'>
        <h1 style='font-size:2.5rem;color:#8B0000;'>&#x26BD; World Cup 2026</h1>
        <p style='color:#555;font-size:1.1rem;'>USA &bull; Canada &bull; Mexico</p>
    </div>
    """, unsafe_allow_html=True)

    tab_in, tab_up = st.tabs(["Login", "Create Account"])

    with tab_in:
        with st.form("login"):
            ident = st.text_input("Username or Email")
            pw    = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if ident and pw:
                    status, u = login_user(ident, pw)
                    if status == "ok":
                        token = create_session(u["id"])
                        cookie_mgr.set(COOKIE_NAME, token, max_age=COOKIE_TTL * 86400)
                        st.session_state["user"]          = u
                        st.session_state["session_token"] = token
                        st.rerun()
                    elif status == "pending":
                        st.warning(
                            "⏳ Your account is pending admin approval. "
                            "Please wait — you'll be able to log in once verified."
                        )
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Please fill in all fields.")

    with tab_up:
        with st.form("register"):
            nu = st.text_input("Username", key="ru")
            ne = st.text_input("Email",    key="re")
            np = st.text_input("Password", type="password", key="rp")
            nc = st.text_input("Confirm Password", type="password", key="rc")
            if st.form_submit_button("Create Account", use_container_width=True):
                if not all([nu, ne, np, nc]):
                    st.error("Please fill in all fields.")
                elif np != nc:
                    st.error("Passwords do not match.")
                else:
                    ok, msg = register_user(nu, ne, np)
                    st.success(msg) if ok else st.error(msg)
    st.stop()

# ── Logged-in ──────────────────────────────────────────────────────────────────
user     = st.session_state["user"]
is_admin = user.get("role") == "admin"

def _logout():
    token = st.session_state.pop("session_token", None)
    delete_session(token)
    try:
        cookie_mgr.set(COOKIE_NAME, "", max_age=0)
    except Exception:
        pass
    for key in ["user", "page", "show_profile"]:
        st.session_state.pop(key, None)

# ── Global top-bar CSS ─────────────────────────────────────────────────────────
tz_name = user.get("tz_name") or "Jordan (UTC+3)"
fav     = user.get("favorite_team") or ""

st.markdown("""
<style>
/* Remove default top padding so our header sits flush */
section.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
}
/* Fixed header bar */
#wc-topbar {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3.4rem;
    background: #0e0e0e;
    border-bottom: 2px solid #8B0000;
    display: flex;
    align-items: center;
    padding: 0 1rem 0 1.5rem;
    z-index: 9999;
    box-shadow: 0 2px 10px rgba(0,0,0,.6);
}
#wc-topbar .title {
    font-size: 1.05rem;
    font-weight: 800;
    color: #C8A951;
    letter-spacing: .04em;
    flex: 1;
}
#wc-topbar .tz {
    font-size: .72rem;
    color: #666;
    margin-right: 1rem;
}
/* Spacer to push content below the fixed bar */
#wc-topbar-spacer {
    height: 3.6rem;
}
/* Style the two top-right action buttons */
div[data-testid="stHorizontalBlock"].topbar-btns {
    justify-content: flex-end;
    margin-bottom: .5rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div id="wc-topbar">
    <span class="title">&#x26BD; World Cup 2026</span>
    <span class="tz">🕐 {tz_name}</span>
</div>
<div id="wc-topbar-spacer"></div>
""", unsafe_allow_html=True)

# ── Top-right buttons (Profile & Logout) ───────────────────────────────────────
_gap, _col_p, _col_l = st.columns([0.75, 0.14, 0.11])

with _col_p:
    if st.button(f"👤 {user['username']}", use_container_width=True, key="hdr_profile"):
        st.session_state["show_profile"] = not st.session_state.get("show_profile", False)
        st.rerun()

with _col_l:
    if st.button("🚪 Logout", use_container_width=True, key="hdr_logout"):
        _logout()
        st.rerun()

# ── Profile panel (toggleable inline) ─────────────────────────────────────────
if st.session_state.get("show_profile", False):
    with st.container(border=True):
        # Close button at top of panel
        close_col, _ = st.columns([0.15, 0.85])
        with close_col:
            if st.button("✕ Close", key="profile_close"):
                st.session_state["show_profile"] = False
                st.rerun()
        pg_profile.render(user)
    st.markdown("---")

# ── Navigation ─────────────────────────────────────────────────────────────────
NAV = {
    "Home":        "⚽",
    "Schedule":    "📅",
    "Groups":      "🏆",
    "Results":     "📋",
    "Predict":     "🎯",
    "Scores":      "🏅",
    "Leaderboard": "📊",
}
if is_admin:
    NAV["Admin"] = "⚙️"

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

# Sidebar (desktop)
with st.sidebar:
    st.markdown(f"**{user['username']}**")
    if fav:
        st.caption(fav)
    st.caption(f"🕐 {tz_name}")
    if is_admin:
        st.caption("⚙️ Admin")
    st.markdown("---")
    for label, icon in NAV.items():
        active = "✦ " if st.session_state["page"] == label else ""
        if st.button(f"{icon} {active}{label}", use_container_width=True, key=f"sb_{label}"):
            st.session_state["page"]         = label
            st.session_state["show_profile"] = False
            st.rerun()
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True, key="sb_logout"):
        _logout()
        st.rerun()

# Mobile / top tab bar (radio)
choice = st.radio(
    "nav", list(NAV.keys()),
    index=list(NAV.keys()).index(st.session_state["page"]),
    horizontal=True, label_visibility="collapsed",
)
if choice != st.session_state["page"]:
    st.session_state["page"]         = choice
    st.session_state["show_profile"] = False

# ── Render page ────────────────────────────────────────────────────────────────
if not st.session_state.get("show_profile", False):
    p = st.session_state["page"]
    if   p == "Home":        pg_home.render(user)
    elif p == "Schedule":    pg_schedule.render(user)
    elif p == "Groups":      pg_groups.render(user)
    elif p == "Results":     pg_results.render(user)
    elif p == "Predict":     pg_predict.render(user)
    elif p == "Scores":      pg_scores.render(user)
    elif p == "Leaderboard": pg_leaderboard.render(user)
    elif p == "Admin":       pg_admin.render(user)
