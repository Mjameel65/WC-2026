import streamlit as st
from db import get_standings, get_groups


def render(user: dict):
    st.title("Group Standings")
    st.caption("Top 2 from each group + 8 best 3rd-place teams advance.")

    standings = get_standings()
    groups    = get_groups()

    fav = user.get("favorite_team", "")
    if fav and fav in standings:
        st.info(f"Your team **{standings[fav]['flag']} {fav}** is in **Group {standings[fav]['group']}**")

    for i in range(0, len(groups), 2):
        col_a, col_b = st.columns(2)
        for col, grp in zip([col_a, col_b], groups[i:i+2]):
            with col:
                st.markdown(f'<div class="group-header">Group {grp}</div>', unsafe_allow_html=True)
                teams = sorted(
                    [t for t, s in standings.items() if s["group"] == grp],
                    key=lambda t: (-standings[t]["Pts"], -standings[t]["GD"], -standings[t]["GF"]),
                )
                html = ("<table><thead><tr><th>#</th>"
                        "<th style='text-align:left'>Team</th>"
                        "<th>P</th><th>W</th><th>D</th><th>L</th>"
                        "<th>GF</th><th>GA</th><th>GD</th><th>Pts</th>"
                        "</tr></thead><tbody>")
                for rank, t in enumerate(teams, 1):
                    s  = standings[t]
                    hl = " qualify" if rank <= 2 else ""
                    html += (f"<tr class='{hl}'><td>{rank}</td>"
                             f"<td style='text-align:left'>{s['flag']} {t}</td>"
                             f"<td>{s['P']}</td><td>{s['W']}</td><td>{s['D']}</td><td>{s['L']}</td>"
                             f"<td>{s['GF']}</td><td>{s['GA']}</td><td>{s['GD']}</td>"
                             f"<td><b>{s['Pts']}</b></td></tr>")
                html += "</tbody></table><p style='font-size:.72rem;color:#888;margin-top:.3rem;'>Gold = advance</p>"
                st.markdown(html, unsafe_allow_html=True)
