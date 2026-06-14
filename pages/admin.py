import streamlit as st
from db import (get_matches, set_match_result, clear_match_result,
                get_all_predictions_for_match, get_all_users, set_user_role,
                set_user_verified, get_pending_users, calc_points, get_leaderboard)
from tz import format_kickoff
#123

def render(user: dict):
    if user.get("role") != "admin":
        st.error("Access denied.")
        return

    tz_offset    = user.get("tz_offset") or 3
    pending      = get_pending_users()
    pending_badge = f" 🔴 {len(pending)}" if pending else ""

    st.title("Admin Panel")

    tab_results, tab_verify, tab_users = st.tabs([
        "Match Results",
        f"Verify Users{pending_badge}",
        "All Users",
    ])

    # ── Tab 1: Match Results ──────────────────────────────────────────────────
    with tab_results:
        matches  = get_matches()
        done     = [m for m in matches if m["status"] == "completed"]
        locked   = [m for m in matches if m["locked"] and m["status"] != "completed"]
        upcoming = [m for m in matches if not m["locked"]]

        st.subheader("Enter / Update Result")
        st.caption("Select any match that has kicked off and enter the final score.")

        eligible = locked + done
        if not eligible:
            st.info("No matches have kicked off yet.")
        else:
            options = {
                f"[{'✅' if m['status']=='completed' else '🔴'}] "
                f"Group {m['group']} · {m['home']} vs {m['away']} "
                f"({format_kickoff(m['kickoff_utc'], tz_offset)})": m
                for m in eligible
            }
            chosen_label = st.selectbox("Match", list(options.keys()))
            m = options[chosen_label]

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

            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("Save Result", use_container_width=True):
                    set_match_result(m["id"], int(sh), int(sa))
                    st.success(f"Saved: {m['home']} {int(sh)} – {int(sa)} {m['away']}")
                    st.rerun()
            with col_clear:
                if st.button("Clear Result", use_container_width=True):
                    clear_match_result(m["id"])
                    st.warning("Result cleared.")
                    st.rerun()

            # Show predictions for this match
            preds = get_all_predictions_for_match(m["id"])
            if preds and m["status"] == "completed":
                st.markdown("**Predictions for this match:**")
                html = "<table><thead><tr><th style='text-align:left'>Player</th><th>Predicted</th><th>Points</th></tr></thead><tbody>"
                for p in preds:
                    pts    = calc_points(p["pred_home"], p["pred_away"], m["score_home"], m["score_away"])
                    pt_lbl = (f'<b style="color:#C8A951;">+3 Exact</b>' if pts == 3
                              else (f'<b style="color:#2d6a4f;">+1 Winner</b>' if pts == 1
                                    else '<span style="color:#888;">0</span>'))
                    html  += (f"<tr><td style='text-align:left'>{p['username']}</td>"
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
                winner = (m["home"] if m["score_home"] > m["score_away"]
                          else (m["away"] if m["score_away"] > m["score_home"] else "Draw"))
                st.markdown(f"""
                <div class="match-card completed">
                    <div class="match-teams">
                        <span>{m['home_flag']} {m['home']}</span>
                        <span class="match-score">{m['score_home']} – {m['score_away']}</span>
                        <span>{m['away']} {m['away_flag']}</span>
                    </div>
                    <div class="match-meta">
                        Group {m['group']} &nbsp;|&nbsp; {format_kickoff(m['kickoff_utc'], tz_offset)}
                        &nbsp;|&nbsp; {m['venue']}
                        &nbsp;<span class="badge badge-completed">FT</span>
                    </div>
                </div>""", unsafe_allow_html=True)

    # ── Tab 2: Verify Users ───────────────────────────────────────────────────
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
                        st.rerun()
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{pu['id']}", use_container_width=True):
                        set_user_verified(pu["id"], False)
                        st.warning(f"{pu['username']} rejected.")
                        st.rerun()

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
                        st.rerun()

    # ── Tab 3: All Users ──────────────────────────────────────────────────────
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
        st.subheader("Change User Role")
        other_users = [u for u in users if u["username"] != user["username"]]
        if other_users:
            target_name = st.selectbox("User", [u["username"] for u in other_users])
            target_u    = next(u for u in other_users if u["username"] == target_name)
            new_role    = st.radio("New role", ["user", "admin"],
                                   index=0 if target_u["role"] == "user" else 1,
                                   horizontal=True)
            if st.button("Update Role", use_container_width=True):
                set_user_role(target_u["id"], new_role)
                st.success(f"{target_name} is now **{new_role}**")
                st.rerun()
