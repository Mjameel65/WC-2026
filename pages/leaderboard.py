import streamlit as st
from db import get_leaderboard, get_matches, get_all_predictions_for_match, get_teams, calc_points


def render(user: dict):
    st.title("Leaderboard")
    st.caption("**3 pts** exact score · **1 pt** correct outcome · **0** wrong")

    board    = get_leaderboard()
    matches  = get_matches()
    done     = [m for m in matches if m["status"] == "completed"]
    teams    = {t["name"]: t for t in get_teams()}
    medals   = {1: "🥇", 2: "🥈", 3: "🥉"}
    me       = user["username"]

    if not board:
        st.info("No predictions yet.")
        return

    # ── My card ───────────────────────────────────────────────────────────────
    my_row = next((r for r in board if r["username"] == me), None)
    if my_row:
        rank = board.index(my_row) + 1
        fav_flag = teams.get(my_row["fav_team"], {}).get("flag", "") if my_row["fav_team"] else ""
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#8B0000,#3d0000);border-radius:12px;
                    padding:1rem 1.5rem;margin-bottom:1.2rem;'>
            <div style='color:#C8A951;font-size:.8rem;font-weight:700;
                        text-transform:uppercase;letter-spacing:.08em;'>Your Standing</div>
            <div style='display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;gap:.5rem;margin-top:.4rem;'>
                <div style='font-size:1.4rem;font-weight:700;color:#fff;'>
                    #{rank} &nbsp; {fav_flag} {me}
                </div>
                <div style='display:flex;gap:1.5rem;'>
                    <div style='text-align:center;'>
                        <div style='font-size:1.8rem;font-weight:800;color:#C8A951;'>{my_row["points"]}</div>
                        <div style='font-size:.7rem;color:#ccc;'>Points</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.8rem;font-weight:800;color:#fff;'>{my_row["exact"]}</div>
                        <div style='font-size:.7rem;color:#ccc;'>Exact</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.8rem;font-weight:800;color:#fff;'>{my_row["winner"]}</div>
                        <div style='font-size:.7rem;color:#ccc;'>Winner</div>
                    </div>
                    <div style='text-align:center;'>
                        <div style='font-size:1.8rem;font-weight:800;color:#888;'>{my_row["wrong"]}</div>
                        <div style='font-size:.7rem;color:#ccc;'>Wrong</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Standings table ───────────────────────────────────────────────────────
    html = """<table><thead><tr>
        <th>#</th><th style='text-align:left'>Player</th>
        <th>Pts</th><th>Exact</th><th>Winner</th><th>Wrong</th><th>No pick</th><th>Total picks</th>
    </tr></thead><tbody>"""
    for i, r in enumerate(board, 1):
        medal   = medals.get(i, str(i))
        flag    = teams.get(r["fav_team"], {}).get("flag", "") if r["fav_team"] else ""
        hl      = "color:#C8A951;font-weight:700;" if r["username"] == me else ""
        html   += (f"<tr><td style='{hl}'>{medal}</td>"
                   f"<td style='text-align:left;{hl}'>{flag} {r['username']}</td>"
                   f"<td style='font-weight:700;{hl}'>{r['points']}</td>"
                   f"<td>{r['exact']}</td><td>{r['winner']}</td>"
                   f"<td>{r['wrong']}</td><td style='color:#888;'>{r['no_pred']}</td>"
                   f"<td style='color:#888;'>{r['total_pred']}</td></tr>")
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # ── Per-match breakdown (expandable) ─────────────────────────────────────
    if done:
        st.markdown("---")
        st.subheader("Match-by-Match Breakdown")
        for m in reversed(done):
            preds = get_all_predictions_for_match(m["id"])
            with st.expander(
                f"Group {m['group']} · {m['home_flag']} {m['home']} "
                f"{m['score_home']}–{m['score_away']} {m['away']} {m['away_flag']}",
                expanded=False,
            ):
                if not preds:
                    st.caption("No predictions for this match.")
                    continue
                mhtml = """<table><thead><tr>
                    <th style='text-align:left'>Player</th>
                    <th>Predicted</th><th>Points</th>
                </tr></thead><tbody>"""
                for p in preds:
                    pts     = calc_points(p["pred_home"], p["pred_away"], m["score_home"], m["score_away"])
                    pt_lbl  = (f'<span style="color:#C8A951;font-weight:700;">+3 Exact</span>' if pts == 3
                               else (f'<span style="color:#2d6a4f;">+1 Winner</span>' if pts == 1
                                     else '<span style="color:#888;">0</span>'))
                    hl2     = "color:#C8A951;" if p["username"] == me else ""
                    mhtml  += (f"<tr><td style='text-align:left;{hl2}'>{p['username']}</td>"
                               f"<td>{p['pred_home']} – {p['pred_away']}</td>"
                               f"<td>{pt_lbl}</td></tr>")
                # Users who didn't predict
                predictors = {p["username"] for p in preds}
                for r in board:
                    if r["username"] not in predictors:
                        hl2 = "color:#888;"
                        mhtml += (f"<tr><td style='text-align:left;{hl2}'>{r['username']}</td>"
                                  f"<td style='color:#555;'>—</td>"
                                  f"<td style='color:#555;'>0</td></tr>")
                mhtml += "</tbody></table>"
                st.markdown(mhtml, unsafe_allow_html=True)
