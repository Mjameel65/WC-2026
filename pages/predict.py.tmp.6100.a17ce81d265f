import streamlit as st
from db import get_matches, get_user_predictions, save_prediction, calc_points
from tz import format_kickoff


def _pts_badge(pts):
    if pts == 3:
        return '<span class="badge" style="background:#C8A951;color:#000;">+3 Exact!</span>'
    if pts == 1:
        return '<span class="badge" style="background:#2d6a4f;color:#fff;">+1 Winner</span>'
    return '<span class="badge" style="background:#555;color:#aaa;">0 pts</span>'


def render(user: dict):
    tz_offset  = user.get("tz_offset") or 3
    tz_name    = user.get("tz_name", "Jordan (UTC+3)")
    matches    = get_matches()
    user_preds = get_user_predictions(user["id"])

    st.title("Predictions")
    st.caption(
        f"Times in **{tz_name}**. "
        "**3 pts** exact score · **1 pt** correct outcome · **0** otherwise. "
        "Locked at kick-off."
    )

    open_m = [m for m in matches if not m["locked"]]
    live_m = [m for m in matches if m["locked"] and m["status"] == "live"]
    done_m = [m for m in matches if m["status"] == "completed"]

    # ── Open ─────────────────────────────────────────────────────────────────
    st.subheader(f"Open for Prediction ({len(open_m)})")
    if not open_m:
        st.info("No upcoming matches to predict yet.")
    for m in open_m:
        existing = user_preds.get(m["id"])
        with st.expander(
            f"Group {m['group']} · {m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}"
            f"  —  {format_kickoff(m['kickoff_utc'], tz_offset)}",
            expanded=False,
        ):
            st.caption(m["venue"])
            c1, cdash, c2 = st.columns([2, 0.5, 2])
            with c1:
                st.markdown(f"**{m['home_flag']} {m['home']}**")
                ph = st.number_input("Home", 0, 20,
                                     value=existing[0] if existing else 0,
                                     key=f"ph_{m['id']}", label_visibility="collapsed")
            with cdash:
                st.markdown("<div style='text-align:center;padding-top:.5rem;font-size:1.3rem;'>–</div>",
                            unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{m['away_flag']} {m['away']}**")
                pa = st.number_input("Away", 0, 20,
                                     value=existing[1] if existing else 0,
                                     key=f"pa_{m['id']}", label_visibility="collapsed")
            lbl = "Update" if existing else "Submit"
            if st.button(lbl, key=f"btn_{m['id']}", use_container_width=True):
                save_prediction(user["id"], m["id"], int(ph), int(pa))
                st.success(f"Saved: {m['home']} {int(ph)} – {int(pa)} {m['away']}")
                st.rerun()
            if existing:
                st.caption(f"Your prediction: **{existing[0]} – {existing[1]}**")

    # ── Live / locked ─────────────────────────────────────────────────────────
    if live_m:
        st.subheader(f"In Progress — Locked ({len(live_m)})")
        for m in live_m:
            ex = user_preds.get(m["id"])
            ps = f"{ex[0]} – {ex[1]}" if ex else "No prediction"
            st.markdown(f"""
            <div class="match-card live">
                <div class="match-teams">
                    <span>{m['home_flag']} {m['home']}</span>
                    <span class="match-score">LIVE</span>
                    <span>{m['away']} {m['away_flag']}</span>
                </div>
                <div class="match-meta">
                    Group {m['group']} &nbsp;|&nbsp; {m['venue']}
                    &nbsp;|&nbsp; Your pick: <b>{ps}</b>
                    &nbsp;<span class="badge badge-live">&#9679; LOCKED</span>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Completed ─────────────────────────────────────────────────────────────
    st.subheader(f"Completed ({len(done_m)})")
    if not done_m:
        st.caption("No completed matches yet.")
    for m in reversed(done_m):
        ex = user_preds.get(m["id"])
        if ex:
            pts   = calc_points(ex[0], ex[1], m["score_home"], m["score_away"])
            badge = _pts_badge(pts)
            ps    = f"{ex[0]} – {ex[1]}"
        else:
            badge = '<span class="badge" style="background:#444;color:#aaa;">No pick</span>'
            ps    = "—"
        st.markdown(f"""
        <div class="match-card completed">
            <div class="match-teams">
                <span>{m['home_flag']} {m['home']}</span>
                <span class="match-score">{m['score_home']} – {m['score_away']}</span>
                <span>{m['away']} {m['away_flag']}</span>
            </div>
            <div class="match-meta">
                Group {m['group']} &nbsp;|&nbsp; {m['venue']}
                &nbsp;|&nbsp; Your pick: <b>{ps}</b> &nbsp;{badge}
            </div>
        </div>""", unsafe_allow_html=True)
