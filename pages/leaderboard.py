import streamlit as st
from datetime import datetime, timezone, timedelta, date
from db import get_leaderboard, get_matches, get_all_predictions_for_match, get_teams, calc_points
from tz import format_kickoff, local_date


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3

    st.title("Leaderboard")
    st.caption("**3 pts** exact score · **1 pt** correct outcome · **0** wrong")

    board   = get_leaderboard()
    matches = get_matches()
    teams   = {t["name"]: t for t in get_teams()}
    medals  = {1: "🥇", 2: "🥈", 3: "🥉"}
    me      = user["username"]

    if not board:
        st.info("No predictions yet.")
        return

    # ── My card ───────────────────────────────────────────────────────────────
    my_row = next((r for r in board if r["username"] == me), None)
    if my_row:
        rank     = board.index(my_row) + 1
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
        medal  = medals.get(i, str(i))
        flag   = teams.get(r["fav_team"], {}).get("flag", "") if r["fav_team"] else ""
        hl     = "color:#C8A951;font-weight:700;" if r["username"] == me else ""
        html  += (f"<tr><td style='{hl}'>{medal}</td>"
                  f"<td style='text-align:left;{hl}'>{flag} {r['username']}</td>"
                  f"<td style='font-weight:700;{hl}'>{r['points']}</td>"
                  f"<td>{r['exact']}</td><td>{r['winner']}</td>"
                  f"<td>{r['wrong']}</td><td style='color:#888;'>{r['no_pred']}</td>"
                  f"<td style='color:#888;'>{r['total_pred']}</td></tr>")
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

    # ── Match-by-Match Breakdown ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Match-by-Match Breakdown")

    # ── Date filter ───────────────────────────────────────────────────────────
    now_local   = datetime.now(timezone.utc) + timedelta(hours=tz_offset)
    today       = now_local.date()
    yesterday   = today - timedelta(days=1)
    tomorrow    = today + timedelta(days=1)

    match_dates = sorted({date.fromisoformat(local_date(m["kickoff_utc"], tz_offset)) for m in matches})
    min_date    = match_dates[0]  if match_dates else today
    max_date    = match_dates[-1] if match_dates else today

    f_col, d_col = st.columns([3, 2])
    with f_col:
        quick = st.radio(
            "lb_quick", ["Yesterday", "Today", "Tomorrow", "All"],
            index=1, horizontal=True, label_visibility="collapsed",
            key="lb_quick_filter",
        )
    with d_col:
        custom_date = st.date_input(
            "📅 Specific date",
            value=None,
            min_value=min_date,
            max_value=max_date,
            label_visibility="visible",
            key="lb_custom_date",
        )

    if custom_date:
        target_date  = custom_date
        filter_label = target_date.strftime("%d %b %Y")
    elif quick == "Yesterday":
        target_date  = yesterday
        filter_label = f"Yesterday ({yesterday.strftime('%d %b')})"
    elif quick == "Tomorrow":
        target_date  = tomorrow
        filter_label = f"Tomorrow ({tomorrow.strftime('%d %b')})"
    elif quick == "Today":
        target_date  = today
        filter_label = f"Today ({today.strftime('%d %b')})"
    else:
        target_date  = None
        filter_label = "All matches"

    if target_date:
        filtered = [
            m for m in matches
            if date.fromisoformat(local_date(m["kickoff_utc"], tz_offset)) == target_date
        ]
    else:
        filtered = matches

    st.caption(f"Showing: **{filter_label}** — {len(filtered)} match{'es' if len(filtered) != 1 else ''}")

    if not filtered:
        st.info("No matches on this date.")
        return

    # ── Expanders: one per match ───────────────────────────────────────────────
    for m in filtered:
        is_done = m["status"] == "completed"
        is_live = m["locked"] and not is_done

        preds    = get_all_predictions_for_match(m["id"])
        pred_map = {p["username"]: p for p in preds}

        # Expander title
        if is_done:
            title = (f"Group {m['group']} · "
                     f"{m['home_flag']} {m['home']} {m['score_home']}–{m['score_away']} "
                     f"{m['away']} {m['away_flag']}  ✅ FT")
        elif is_live:
            title = (f"Group {m['group']} · "
                     f"{m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}  🔴 LIVE")
        else:
            kick  = format_kickoff(m["kickoff_utc"], tz_offset)
            title = (f"Group {m['group']} · "
                     f"{m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}  🕐 {kick}")

        with st.expander(title, expanded=False):
            mhtml = """<table><thead><tr>
                <th style='text-align:left'>Player</th>
                <th>Predicted</th>
                <th>Points</th>
            </tr></thead><tbody>"""

            predictors = set()

            # Users who predicted
            for p in preds:
                predictors.add(p["username"])
                if is_done:
                    pts    = calc_points(p["pred_home"], p["pred_away"],
                                         m["score_home"], m["score_away"])
                    pt_lbl = (
                        '<span style="color:#C8A951;font-weight:700;">+3 Exact</span>'  if pts == 3
                        else ('<span style="color:#2d6a4f;">+1 Winner</span>'            if pts == 1
                              else '<span style="color:#888;">0</span>')
                    )
                else:
                    pt_lbl = '<span style="color:#555;">Pending</span>'

                hl     = "color:#C8A951;" if p["username"] == me else ""
                mhtml += (f"<tr><td style='text-align:left;{hl}'>{p['username']}</td>"
                          f"<td>{p['pred_home']} – {p['pred_away']}</td>"
                          f"<td>{pt_lbl}</td></tr>")

            # Users who did NOT predict
            for r in board:
                if r["username"] not in predictors:
                    hl     = "color:#C8A951;" if r["username"] == me else "color:#555;"
                    no_pt  = "0" if is_done else "—"
                    mhtml += (f"<tr><td style='text-align:left;{hl}'>{r['username']}</td>"
                              f"<td style='color:#555;'>—</td>"
                              f"<td style='color:#555;'>{no_pt}</td></tr>")

            mhtml += "</tbody></table>"
            st.markdown(mhtml, unsafe_allow_html=True)
