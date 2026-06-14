import streamlit as st
from db import get_matches, get_standings, update_user_field, get_teams
from tz import TIMEZONES, format_kickoff


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3
    tz_name   = user.get("tz_name") or "Jordan (UTC+3)"

    st.title("My Profile")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"""
        <div style='background:#1a1a1a;border-radius:12px;padding:1.2rem;text-align:center;'>
            <div style='font-size:3rem;'>&#128100;</div>
            <h3 style='margin:0.3rem 0;'>{user['username']}</h3>
            <p style='color:#888;font-size:.85rem;margin:0;'>{user['email']}</p>
            <p style='color:#C8A951;font-size:.8rem;margin:.3rem 0 0;'>{user.get("role","user").upper()}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        teams     = {t["name"]: t for t in get_teams()}
        all_names = ["(None)"] + sorted(teams.keys())

        st.subheader("Favourite Team")
        cur_fav = user.get("favorite_team") or ""
        idx     = all_names.index(cur_fav) if cur_fav in all_names else 0
        new_fav = st.selectbox("Team", all_names, index=idx)
        if st.button("Save Team", use_container_width=True):
            val = "" if new_fav == "(None)" else new_fav
            update_user_field(user["id"], "favorite_team", val)
            st.session_state["user"]["favorite_team"] = val
            user["favorite_team"] = val
            st.success("Saved!")

        st.markdown("<div style='margin-top:1rem'></div>", unsafe_allow_html=True)

        st.subheader("Timezone")
        tz_opts = list(TIMEZONES.keys())
        tz_idx  = tz_opts.index(tz_name) if tz_name in tz_opts else 0
        new_tz  = st.selectbox("Timezone", tz_opts, index=tz_idx)
        if st.button("Save Timezone", use_container_width=True):
            new_off = TIMEZONES[new_tz]
            update_user_field(user["id"], "tz_name",   new_tz)
            update_user_field(user["id"], "tz_offset",  new_off)
            st.session_state["user"]["tz_name"]   = new_tz
            st.session_state["user"]["tz_offset"]  = new_off
            user["tz_name"]   = new_tz
            user["tz_offset"] = new_off
            st.success(f"Timezone set to {new_tz}")
            st.rerun()

    st.markdown("---")

    fav = user.get("favorite_team") or ""
    if not fav:
        st.info("Select a favourite team above to track their matches here.")
        return

    t    = teams.get(fav, {})
    flag = t.get("flag", "")
    st.subheader(f"{flag} {fav} — All Matches")

    matches = get_matches()
    team_m  = [m for m in matches if fav in (m["home"], m["away"])]
    for m in team_m:
        status = m["status"]
        badge  = {
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
            <div class="match-meta">Group {m['group']} &nbsp;|&nbsp; {m['venue']} &nbsp;{badge}</div>
        </div>""", unsafe_allow_html=True)

    s = get_standings().get(fav)
    if s:
        st.subheader(f"Group {s['group']} Standing")
        st.markdown(f"""
        <table style='width:auto'>
            <thead><tr><th>P</th><th>W</th><th>D</th><th>L</th>
            <th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead>
            <tbody><tr>
            <td>{s['P']}</td><td>{s['W']}</td><td>{s['D']}</td><td>{s['L']}</td>
            <td>{s['GF']}</td><td>{s['GA']}</td><td>{s['GD']}</td>
            <td><b>{s['Pts']}</b></td>
            </tr></tbody>
        </table>""", unsafe_allow_html=True)
