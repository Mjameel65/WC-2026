import streamlit as st
from db import (get_matches, get_teams, set_match_result, clear_match_result,
                get_all_predictions_for_match, get_all_users, set_user_role,
                set_user_verified, get_pending_users, calc_points,
                calc_points_knockout, get_leaderboard, set_user_startup_points,
                add_knockout_match, reset_user_password, save_prediction)
from tz import format_kickoff

STAGES = ["R32", "R16", "QF", "SF", "3rd", "F"]
STAGE_LABELS = {
    "R32": "Round of 32", "R16": "Round of 16",
    "QF":  "Quarter-Final", "SF": "Semi-Final",
    "3rd": "Third Place",   "F":  "Final",
}


def render(user: dict):
    if user.get("role") != "admin":
        st.error("Access denied.")
        return

    tz_offset    = user.get("tz_offset") or 3
    pending      = get_pending_users()
    pending_badge = f" 🔴 {len(pending)}" if pending else ""

    st.title("Admin Panel")

    tab_results, tab_knockout, tab_setpred, tab_verify, tab_users, tab_startup = st.tabs([
        "Match Results",
        "Add Knockout Match",
        "Set Prediction",
        f"Verify Users{pending_badge}",
        "All Users",
        "Startup Points",
    ])

    # ── Tab 1: Match Results ──────────────────────────────────────────────────
    with tab_results:
        matches  = get_matches()
        done     = [m for m in matches if m["status"] == "completed"]
        locked   = [m for m in matches if m["locked"] and m["status"] != "completed"]
        upcoming = [m for m in matches if not m["locked"]]

        if locked:
            st.warning(f"⚠️ {len(locked)} match{'es' if len(locked)>1 else ''} overdue — result not entered yet:")
            for m in locked:
                st.markdown(
                    f"&nbsp;&nbsp;🔴 **{m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}** "
                    f"· {m['group']} · {format_kickoff(m['kickoff_utc'], tz_offset)}"
                )
            st.markdown("---")

        st.subheader("Enter / Update Result")

        eligible = locked + done
        if not eligible:
            st.info("No matches have kicked off yet.")
        else:
            options = {
                f"[{'✅' if m['status']=='completed' else '🔴'}] "
                f"{m['group']} · {m['home']} vs {m['away']} "
                f"({format_kickoff(m['kickoff_utc'], tz_offset)})": m
                for m in eligible
            }
            chosen_label = st.selectbox("Match", list(options.keys()))
            m = options[chosen_label]
            is_knockout  = m.get("stage", "group") != "group"

            c1, cdash, c2 = st.columns([2, 0.4, 2])
            with c1:
                st.markdown(f"**{m['home_flag']} {m['home']}**")
                sh = st.number_input("Home score", 0, 30,
                                     value=m["score_home"] if m["score_home"] is not None else 0,
                                     key="admin_sh")
            with cdash:
                st.markdown("<div style='text-align:center;padding-top:.5rem;font-size:1.3rem;'>–</div>",
                            unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{m['away_flag']} {m['away']}**")
                sa = st.number_input("Away score", 0, 30,
                                     value=m["score_away"] if m["score_away"] is not None else 0,
                                     key="admin_sa")

            # Penalty winner — shown only for knockout when scores are equal
            penalty_winner = None
            if is_knockout and int(sh) == int(sa):
                st.info("⚽ Draw after 90 min — select the penalty/ET winner:")
                pw_options = [m["home"], m["away"]]
                current_pw = m.get("penalty_winner")
                pw_idx = pw_options.index(current_pw) if current_pw in pw_options else 0
                penalty_winner = st.radio(
                    "Penalty winner", pw_options, index=pw_idx,
                    horizontal=True, key="admin_pw"
                )

            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("Save Result", use_container_width=True):
                    pw = penalty_winner if (is_knockout and int(sh) == int(sa)) else None
                    set_match_result(m["id"], int(sh), int(sa), pw)
                    st.success(f"Saved: {m['home']} {int(sh)} – {int(sa)} {m['away']}"
                               + (f" (penalties: {pw})" if pw else ""))
            with col_clear:
                if st.button("Clear Result", use_container_width=True):
                    clear_match_result(m["id"])
                    st.warning("Result cleared.")

            # Show predictions for this match
            preds = get_all_predictions_for_match(m["id"])
            if preds and m["status"] == "completed":
                st.markdown("**Predictions for this match:**")
                if is_knockout:
                    html = "<table><thead><tr><th style='text-align:left'>Player</th><th>Predicted</th><th>Winner pick</th><th>Base</th><th>Got winner?</th></tr></thead><tbody>"
                    for p in preds:
                        base, got_win = calc_points_knockout(
                            p["pred_home"], p["pred_away"], p.get("pred_winner"),
                            m["score_home"], m["score_away"], m.get("penalty_winner"),
                            m["home"], m["away"],
                        )
                        base_lbl = f'<b style="color:#C8A951;">+2 Exact</b>' if base == 2 else '<span style="color:#888;">0</span>'
                        win_lbl  = '✅' if got_win else '❌'
                        pw_lbl   = p.get("pred_winner") or "—"
                        html += (f"<tr><td style='text-align:left'>{p['username']}</td>"
                                 f"<td>{p['pred_home']} – {p['pred_away']}</td>"
                                 f"<td>{pw_lbl}</td>"
                                 f"<td>{base_lbl}</td><td>{win_lbl}</td></tr>")
                    html += "</tbody></table>"
                else:
                    html = "<table><thead><tr><th style='text-align:left'>Player</th><th>Predicted</th><th>Points</th></tr></thead><tbody>"
                    for p in preds:
                        pts    = calc_points(p["pred_home"], p["pred_away"], m["score_home"], m["score_away"])
                        pt_lbl = (f'<b style="color:#C8A951;">+3 Exact</b>' if pts == 3
                                  else (f'<b style="color:#2d6a4f;">+1 Winner</b>' if pts == 1
                                        else '<span style="color:#888;">0</span>'))
                        html += (f"<tr><td style='text-align:left'>{p['username']}</td>"
                                 f"<td>{p['pred_home']} – {p['pred_away']}</td>"
                                 f"<td>{pt_lbl}</td></tr>")
                    html += "</tbody></table>"
                st.markdown(html, unsafe_allow_html=True)
            elif preds:
                st.caption(f"{len(preds)} prediction(s) submitted (result not yet saved).")

        st.markdown("---")
        st.subheader("All Results Summary")
        if not done:
            st.caption("No completed matches yet.")
        else:
            for m in done:
                pw_str = f" · Penalties: **{m['penalty_winner']}**" if m.get("penalty_winner") else ""
                st.markdown(f"""
                <div class="match-card completed">
                    <div class="match-teams">
                        <span>{m['home_flag']} {m['home']}</span>
                        <span class="match-score">{m['score_home']} – {m['score_away']}</span>
                        <span>{m['away']} {m['away_flag']}</span>
                    </div>
                    <div class="match-meta">
                        {m['group']} &nbsp;|&nbsp; {format_kickoff(m['kickoff_utc'], tz_offset)}
                        &nbsp;|&nbsp; {m['venue']}{pw_str}
                        &nbsp;<span class="badge badge-completed">FT</span>
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── Tab 2: Add Knockout Match ─────────────────────────────────────────────
    with tab_knockout:
        st.subheader("Add Knockout Stage Match")
        st.caption("Use this after the group stage ends (June 27) once qualified teams are confirmed.")

        all_teams  = get_teams()
        all_matches = get_matches()
        team_names  = sorted([t["name"] for t in all_teams])
        team_map    = {t["name"]: t["id"] for t in all_teams}

        from db import get_conn
        import psycopg2.extras
        conn = get_conn()
        cur  = conn.cursor()
        cur.execute("SELECT id, key, name FROM venues ORDER BY name")
        venues = cur.fetchall()
        conn.close()
        venue_options = {v["name"]: v["id"] for v in venues}

        st.markdown("**Existing knockout matches:**")
        ko_matches = [m for m in all_matches if m.get("stage", "group") != "group"]
        if not ko_matches:
            st.caption("None added yet.")
        else:
            for m in ko_matches:
                pw = f" · Pen: {m['penalty_winner']}" if m.get("penalty_winner") else ""
                score = f"{m['score_home']}–{m['score_away']}" if m["score_home"] is not None else "TBD"
                st.markdown(
                    f"**{STAGE_LABELS.get(m['stage'], m['stage'])}** · "
                    f"{m['home_flag']} {m['home']} {score} {m['away']} {m['away_flag']}"
                    f" · {format_kickoff(m['kickoff_utc'], tz_offset)}{pw}"
                )

        st.markdown("---")
        st.markdown("**Add new match:**")

        ko_col1, ko_col2 = st.columns(2)
        with ko_col1:
            stage_lbl  = st.selectbox("Stage", list(STAGE_LABELS.values()), key="ko_stage")
            stage_key  = [k for k, v in STAGE_LABELS.items() if v == stage_lbl][0]
            home_name  = st.selectbox("Home team", team_names, key="ko_home")
        with ko_col2:
            kickoff_d  = st.date_input("Kickoff date (UTC)", key="ko_date")
            kickoff_t  = st.time_input("Kickoff time (UTC)", key="ko_time")
            away_name  = st.selectbox("Away team", team_names, key="ko_away")

        venue_name = st.selectbox("Venue", list(venue_options.keys()), key="ko_venue")

        if st.button("➕ Add Knockout Match", use_container_width=True):
            if home_name == away_name:
                st.error("Home and Away teams must be different.")
            else:
                kickoff_str = f"{kickoff_d}T{kickoff_t.strftime('%H:%M')}"
                add_knockout_match(
                    stage_key,
                    team_map[home_name],
                    team_map[away_name],
                    kickoff_str,
                    venue_options[venue_name],
                )
                st.success(f"Added: {home_name} vs {away_name} — {STAGE_LABELS[stage_key]} — {kickoff_str} UTC")

    # ── Tab 3: Set Prediction (admin override) ────────────────────────────────
    with tab_setpred:
        st.subheader("Set / Override Prediction")
        st.caption("Enter or overwrite a prediction for any user on any match, regardless of lock status.")

        all_matches  = get_matches()
        all_users_sp = get_all_users()
        verified_sp  = [u for u in all_users_sp if u.get("verified") or u.get("verified") == 1]

        if not verified_sp:
            st.info("No verified users yet.")
        else:
            sp_uname   = st.selectbox("User", [u["username"] for u in verified_sp], key="sp_user")
            sp_user_obj = next(u for u in verified_sp if u["username"] == sp_uname)

            match_opts = [
                f"[{m.get('group','?')}] {m['home']} vs {m['away']}  ({m['kickoff_utc'][:10]})"
                for m in all_matches
            ]
            sp_match_idx = st.selectbox("Match", range(len(match_opts)),
                                        format_func=lambda i: match_opts[i], key="sp_match")
            sp_match = all_matches[sp_match_idx]
            is_ko_sp = sp_match.get("stage", "group") != "group"

            c1, c2 = st.columns(2)
            with c1:
                sp_home = st.number_input(f"{sp_match['home']} goals", min_value=0, max_value=20,
                                          value=1, step=1, key="sp_home")
            with c2:
                sp_away = st.number_input(f"{sp_match['away']} goals", min_value=0, max_value=20,
                                          value=0, step=1, key="sp_away")

            sp_winner = None
            if is_ko_sp and sp_home == sp_away:
                sp_winner = st.radio(
                    "Penalty winner (draw score — knockout)",
                    [sp_match["home"], sp_match["away"]],
                    horizontal=True, key="sp_winner",
                )
            elif is_ko_sp:
                sp_winner = sp_match["home"] if sp_home > sp_away else sp_match["away"]

            if st.button("Save Prediction", use_container_width=True, key="sp_save"):
                save_prediction(sp_user_obj["id"], sp_match["id"], sp_home, sp_away, sp_winner)
                st.success(
                    f"Saved: **{sp_uname}** → {sp_match['home']} {sp_home}–{sp_away} {sp_match['away']}"
                    + (f" (pen: {sp_winner})" if sp_winner and sp_home == sp_away else "")
                )

    # ── Tab 4: Verify Users ───────────────────────────────────────────────────
    with tab_verify:
        st.subheader("Pending Verification")
        pending = get_pending_users()
        if not pending:
            st.success("No users waiting for verification.")
        else:
            for pu in pending:
                col_info, col_approve, col_reject = st.columns([3, 1, 1])
                with col_info:
                    st.markdown(f"""
                    <div style='background:#1a1a1a;border-radius:8px;padding:.6rem 1rem;
                                border-left:4px solid #C8A951;'>
                        <div style='font-weight:700;color:#fff;'>{pu['username']}</div>
                        <div style='font-size:.8rem;color:#888;'>{pu['email']}</div>
                        <div style='font-size:.75rem;color:#555;'>Registered: {str(pu['created_at'])[:16]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{pu['id']}", use_container_width=True):
                        set_user_verified(pu["id"], True)
                        st.success(f"{pu['username']} approved!")
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{pu['id']}", use_container_width=True):
                        set_user_verified(pu["id"], False)
                        st.warning(f"{pu['username']} rejected.")

        st.markdown("---")
        st.subheader("Verified Users")
        all_users = get_all_users()
        verified  = [u for u in all_users if str(u.get("verified", "0")) in ("1", "True")]
        for vu in verified:
            col_info, col_revoke = st.columns([4, 1])
            with col_info:
                role_color = "#8B0000" if vu["role"] == "admin" else "#1d3557"
                st.markdown(f"""
                <div style='background:#111;border-radius:8px;padding:.5rem 1rem;
                            margin-bottom:.4rem;border:1px solid #222;'>
                    <span style='font-weight:600;color:#fff;'>{vu['username']}</span>
                    &nbsp;<span class='badge' style='background:{role_color};color:#fff;font-size:.65rem;'>{vu['role']}</span>
                    &nbsp;<span style='color:#888;font-size:.8rem;'>{vu['email']}</span>
                </div>
                """, unsafe_allow_html=True)
            with col_revoke:
                if vu["username"] != user["username"]:
                    if st.button("Revoke", key=f"revoke_{vu['id']}", use_container_width=True):
                        set_user_verified(vu["id"], False)
                        st.warning(f"Access revoked for {vu['username']}.")

    # ── Tab 4: All Users ──────────────────────────────────────────────────────
    with tab_users:
        st.subheader("All Users")
        users = get_all_users()
        board = {r["username"]: r for r in get_leaderboard()}

        html = ("<table><thead><tr>"
                "<th style='text-align:left'>Username</th>"
                "<th style='text-align:left'>Email</th>"
                "<th>Status</th><th>Role</th><th>Pts</th><th>Picks</th><th>Joined</th>"
                "</tr></thead><tbody>")
        for u in users:
            lb      = board.get(u["username"], {})
            is_ver  = str(u.get("verified", "0")) in ("1", "True")
            ver_badge = ("<span class='badge' style='background:#2d6a4f;color:#fff;'>Verified</span>"
                         if is_ver else
                         "<span class='badge' style='background:#8B0000;color:#fff;'>Pending</span>")
            html += (f"<tr>"
                     f"<td style='text-align:left'>{u['username']}</td>"
                     f"<td style='text-align:left;font-size:.8rem;color:#888;'>{u['email']}</td>"
                     f"<td>{ver_badge}</td>"
                     f"<td><span class='badge' style='background:{'#8B0000' if u['role']=='admin' else '#1d3557'};color:#fff;'>"
                     f"{u['role']}</span></td>"
                     f"<td>{lb.get('points',0)}</td>"
                     f"<td>{lb.get('total_pred',0)}</td>"
                     f"<td style='font-size:.75rem;color:#888;'>{str(u['created_at'])[:10]}</td>"
                     f"</tr>")
        html += "</tbody></table>"
        st.markdown(html, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("Reset User Password")
        other_users = [u for u in users if u["username"] != user["username"]]
        if other_users:
            rp_name = st.selectbox("User", [u["username"] for u in other_users], key="rp_user")
            rp_user = next(u for u in other_users if u["username"] == rp_name)
            rp_col1, rp_col2 = st.columns(2)
            with rp_col1:
                new_pw  = st.text_input("New password", type="password", key="rp_pw")
            with rp_col2:
                conf_pw = st.text_input("Confirm password", type="password", key="rp_conf")
            if st.button("Reset Password", use_container_width=True, key="rp_btn"):
                if not new_pw:
                    st.error("Password cannot be empty.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                elif new_pw != conf_pw:
                    st.error("Passwords do not match.")
                else:
                    reset_user_password(rp_user["id"], new_pw)
                    st.success(f"Password for **{rp_name}** has been reset.")

        st.markdown("---")
        st.subheader("Change User Role")
        if other_users:
            target_name = st.selectbox("User", [u["username"] for u in other_users], key="role_user")
            target_u    = next(u for u in other_users if u["username"] == target_name)
            new_role    = st.radio("New role", ["user", "admin"],
                                   index=0 if target_u["role"] == "user" else 1,
                                   horizontal=True)
            if st.button("Update Role", use_container_width=True):
                set_user_role(target_u["id"], new_role)
                st.success(f"{target_name} is now **{new_role}**")

    # ── Tab 5: Startup Points ─────────────────────────────────────────────────
    with tab_startup:
        st.subheader("Startup Points")
        st.caption(
            "For users who registered after matches were already played, "
            "set a one-time points bonus so they can compete from the next match onwards."
        )

        completed_matches = [m for m in get_matches() if m["status"] == "completed"]
        st.info(f"**{len(completed_matches)} matches** have been played so far.")

        all_users  = get_all_users()
        board      = {r["username"]: r for r in get_leaderboard()}

        for u in all_users:
            lb            = board.get(u["username"], {})
            startup_pts   = lb.get("startup_points", 0)
            match_pts     = lb.get("match_points", 0)

            with st.expander(f"{u['username']}  —  {match_pts} match pts + {startup_pts} startup pts = **{match_pts + startup_pts} total**"):
                new_pts = st.number_input(
                    "Startup points",
                    min_value=0, max_value=500,
                    value=startup_pts,
                    key=f"sp_{u['id']}",
                )
                if st.button("Save", key=f"sp_save_{u['id']}", use_container_width=True):
                    set_user_startup_points(u["id"], int(new_pts))
                    st.success(f"Startup points for {u['username']} set to {int(new_pts)}")
