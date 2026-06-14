import streamlit as st
from db import get_matches, get_teams
from tz import format_kickoff, local_date


def _card(m, tz_offset):
    status = m["status"]
    badge = {
        "live":      '<span class="badge badge-live">&#9679; LIVE</span>',
        "completed": '<span class="badge badge-completed">FT</span>',
        "upcoming":  '<span class="badge badge-upcoming">Upcoming</span>',
    }.get(status, "")
    score = (f"{m['score_home']} – {m['score_away']}" if status == "completed"
             else ("LIVE" if status == "live"
                   else format_kickoff(m["kickoff_utc"], tz_offset)))
    st.markdown(f"""
    <div class="match-card {status}">
        <div class="match-teams">
            <span>{m['home_flag']} {m['home']}</span>
            <span class="match-score">{score}</span>
            <span>{m['away']} {m['away_flag']}</span>
        </div>
        <div class="match-meta">
            Group {m['group']} &nbsp;|&nbsp;
            {local_date(m['kickoff_utc'], tz_offset)} &nbsp;|&nbsp;
            {m['venue']} &nbsp;{badge}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3
    matches   = get_matches()
    all_teams = sorted({m["home"] for m in matches} | {m["away"] for m in matches})

    st.title("Match Schedule")
    st.caption(f"Times in **{user.get('tz_name','Jordan (UTC+3)')}** — change in Profile.")

    c1, c2, c3 = st.columns(3)
    status_f = c1.selectbox("Status", ["All", "Upcoming", "Live", "Completed"])
    group_f  = c2.selectbox("Group",  ["All"] + list("ABCDEFGHIJKL"))
    team_f   = c3.selectbox("Team",   ["All"] + all_teams)

    filtered = matches
    if status_f != "All":
        filtered = [m for m in filtered if m["status"] == status_f.lower()]
    if group_f != "All":
        filtered = [m for m in filtered if m["group"] == group_f]
    if team_f != "All":
        filtered = [m for m in filtered if team_f in (m["home"], m["away"])]

    st.caption(f"{len(filtered)} match(es)")
    if not filtered:
        st.info("No matches found.")
        return

    dates = sorted(set(local_date(m["kickoff_utc"], tz_offset) for m in filtered))
    for d in dates:
        st.markdown(f"### {d}")
        for m in filtered:
            if local_date(m["kickoff_utc"], tz_offset) == d:
                _card(m, tz_offset)
