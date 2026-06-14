import streamlit as st
from datetime import datetime, timezone
from db import get_matches, get_teams
from tz import format_kickoff, local_date, tz_label


def _card(m, tz_offset):
    status = m["status"]
    badge = {
        "live":      '<span class="badge badge-live">&#9679; LIVE</span>',
        "completed": '<span class="badge badge-completed">FT</span>',
        "upcoming":  '<span class="badge badge-upcoming">Upcoming</span>',
    }.get(status, "")
    if status == "completed":
        score = f"{m['score_home']} – {m['score_away']}"
    elif status == "live":
        score = "LIVE"
    else:
        score = format_kickoff(m["kickoff_utc"], tz_offset)

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
    teams     = {t["name"]: t for t in get_teams()}

    st.markdown("""
    <div class="hero">
        <h1>&#x26BD; FIFA World Cup 2026</h1>
        <p>USA &bull; Canada &bull; Mexico &nbsp;|&nbsp; June 11 – July 19, 2026</p>
    </div>
    """, unsafe_allow_html=True)

    today     = local_date(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M"), tz_offset)
    today_m   = [m for m in matches if local_date(m["kickoff_utc"], tz_offset) == today]
    completed = [m for m in matches if m["status"] == "completed"]
    upcoming  = [m for m in matches if m["status"] == "upcoming"][:6]

    fav = user.get("favorite_team", "")
    if fav:
        nxt_list = [m for m in matches if fav in (m["home"], m["away"]) and m["status"] in ("live","upcoming")]
        if nxt_list:
            nxt  = nxt_list[0]
            flag = teams.get(fav, {}).get("flag", "")
            opp  = nxt["away"] if nxt["home"] == fav else nxt["home"]
            st.info(f"**{flag} {fav}** — next: {format_kickoff(nxt['kickoff_utc'], tz_offset)} vs **{opp}**")

    c1, c2 = st.columns(2)
    c1.metric("Teams", "48")
    c1.metric("Matches Played", len(completed))
    c2.metric("Matches Remaining", len([m for m in matches if m["status"] != "completed"]))
    c2.metric("Timezone", tz_label(tz_offset))

    st.markdown("---")
    if today_m:
        st.subheader(f"Today — {today}")
        for m in today_m:
            _card(m, tz_offset)

    st.subheader("Recent Results")
    if completed:
        for m in reversed(completed[-6:]):
            _card(m, tz_offset)
    else:
        st.caption("No completed matches yet.")

    st.subheader("Upcoming")
    for m in upcoming:
        _card(m, tz_offset)
