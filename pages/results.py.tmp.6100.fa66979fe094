import streamlit as st
from db import get_matches, get_standings, get_groups
from tz import format_kickoff


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3
    matches   = get_matches()
    standings = get_standings()
    groups    = get_groups()

    st.title("Results")
    st.caption(f"Times in **{user.get('tz_name','Jordan (UTC+3)')}**")

    done = [m for m in matches if m["status"] == "completed"]
    if not done:
        st.info("No completed matches yet.")
        return

    total_goals = sum(m["score_home"] + m["score_away"] for m in done)
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches Played", len(done))
    c2.metric("Total Goals",    total_goals)
    c3.metric("Avg Goals/Match", f"{total_goals/len(done):.1f}" if done else "0")

    st.markdown("---")

    for grp in groups:
        grp_done = [m for m in done if m["group"] == grp]
        if not grp_done:
            continue

        st.markdown(f'<div class="group-header">Group {grp}</div>', unsafe_allow_html=True)

        # Mini standings
        grp_teams = sorted(
            [t for t, s in standings.items() if s["group"] == grp],
            key=lambda t: (-standings[t]["Pts"], -standings[t]["GD"], -standings[t]["GF"]),
        )
        html = ("<table><thead><tr><th>#</th><th style='text-align:left'>Team</th>"
                "<th>P</th><th>W</th><th>D</th><th>L</th>"
                "<th>GF</th><th>GA</th><th>GD</th><th>Pts</th></tr></thead><tbody>")
        for i, t in enumerate(grp_teams, 1):
            s  = standings[t]
            hl = " qualify" if i <= 2 else ""
            html += (f"<tr class='{hl}'><td>{i}</td>"
                     f"<td style='text-align:left'>{s['flag']} {t}</td>"
                     f"<td>{s['P']}</td><td>{s['W']}</td><td>{s['D']}</td><td>{s['L']}</td>"
                     f"<td>{s['GF']}</td><td>{s['GA']}</td><td>{s['GD']}</td>"
                     f"<td><b>{s['Pts']}</b></td></tr>")
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)
        st.markdown("<div style='margin:.5rem 0'></div>", unsafe_allow_html=True)

        for m in grp_done:
            if m["score_home"] > m["score_away"]:
                winner = m["home"]
            elif m["score_away"] > m["score_home"]:
                winner = m["away"]
            else:
                winner = None

            hw = "font-weight:900;color:#C8A951;" if winner == m["home"]  else ""
            aw = "font-weight:900;color:#C8A951;" if winner == m["away"]  else ""
            outcome_badge = (
                f'<span class="badge" style="background:#C8A951;color:#000;">Winner: {winner}</span>'
                if winner else
                '<span class="badge" style="background:#555;color:#fff;">Draw</span>'
            )
            st.markdown(f"""
            <div class="match-card completed">
                <div class="match-teams">
                    <span style="{hw}">{m['home_flag']} {m['home']}</span>
                    <span class="match-score">{m['score_home']} – {m['score_away']}</span>
                    <span style="{aw}">{m['away']} {m['away_flag']}</span>
                </div>
                <div class="match-meta">
                    {format_kickoff(m['kickoff_utc'], tz_offset)} &nbsp;|&nbsp; {m['venue']}
                    &nbsp;<span class="badge badge-completed">FT</span>
                    &nbsp;{outcome_badge}
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
