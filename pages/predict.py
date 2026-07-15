import streamlit as st
from datetime import datetime, timezone
from db import get_matches, get_user_predictions, save_prediction, calc_points, calc_points_knockout
from tz import format_kickoff


def _countdown(kickoff_utc: str) -> str:
    try:
        kickoff = datetime.fromisoformat(kickoff_utc).replace(tzinfo=timezone.utc)
        secs = int((kickoff - datetime.now(timezone.utc)).total_seconds())
        if secs <= 0:
            return ""
        h, rem = divmod(secs, 3600)
        m = rem // 60
        if h >= 48:
            return f"⏱ {h//24}d {h%24}h to lock"
        return f"⏱ {h}h {m:02d}m to lock" if h else f"⏱ {m}m to lock"
    except Exception:
        return ""


def _pts_badge_group(pts):
    if pts == 3:
        return '<span class="badge" style="background:#C8A951;color:#000;">+3 Exact!</span>'
    if pts == 1:
        return '<span class="badge" style="background:#2d6a4f;color:#fff;">+1 Winner</span>'
    return '<span class="badge" style="background:#555;color:#aaa;">0 pts</span>'


def _pts_badge_knockout(base, got_win):
    parts = []
    if base == 2:
        parts.append('<span class="badge" style="background:#C8A951;color:#000;">+2 Exact</span>')
    if got_win:
        parts.append('<span class="badge" style="background:#2d6a4f;color:#fff;">✓ Winner</span>')
    if not parts:
        parts.append('<span class="badge" style="background:#555;color:#aaa;">0 pts</span>')
    return " ".join(parts)


def render(user: dict):
    tz_offset  = user.get("tz_offset") or 3
    tz_name    = user.get("tz_name", "Jordan (UTC+3)")
    matches    = get_matches()
    user_preds = get_user_predictions(user["id"])

    st.title("Predictions")

    open_m = [m for m in matches if not m["locked"]]
    live_m = [m for m in matches if m["locked"] and m["status"] == "live"]
    done_m = [m for m in matches if m["status"] == "completed"]

    group_open = [m for m in open_m if m.get("stage", "group") == "group"]
    ko_open    = [m for m in open_m if m.get("stage", "group") != "group"]

    # ── Scoring rules caption ─────────────────────────────────────────────────
    if ko_open or any(m.get("stage","group") != "group" for m in live_m + done_m):
        st.caption(
            f"Times in **{tz_name}**. "
            "**Group stage:** +3 exact · +1 winner · 0 wrong.  "
            "**Knockout:** +2 exact score · +1 per user who got winner wrong (if you got winner right)."
        )
    else:
        st.caption(
            f"Times in **{tz_name}**. "
            "**3 pts** exact score · **1 pt** correct outcome · **0** otherwise. Locked at kick-off."
        )

    # ── Open group matches ────────────────────────────────────────────────────
    if group_open:
        st.subheader(f"Open — Group Stage ({len(group_open)})")
        for m in group_open:
            existing = user_preds.get(m["id"])
            ex_h = existing[0] if existing else 0
            ex_a = existing[1] if existing else 0
            cd = _countdown(m["kickoff_utc"])
            with st.expander(
                f"Group {m['group']} · {m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}"
                f"  —  {format_kickoff(m['kickoff_utc'], tz_offset)}"
                + (f"  {cd}" if cd else ""),
                expanded=False,
            ):
                st.caption(m["venue"])
                c1, cdash, c2 = st.columns([2, 0.5, 2])
                with c1:
                    st.markdown(f"**{m['home_flag']} {m['home']}**")
                    ph = st.number_input("Home", 0, 20, value=ex_h,
                                         key=f"ph_{m['id']}", label_visibility="collapsed")
                with cdash:
                    st.markdown("<div style='text-align:center;padding-top:.5rem;font-size:1.3rem;'>–</div>",
                                unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**{m['away_flag']} {m['away']}**")
                    pa = st.number_input("Away", 0, 20, value=ex_a,
                                         key=f"pa_{m['id']}", label_visibility="collapsed")
                lbl = "Update" if existing else "Submit"
                if st.button(lbl, key=f"btn_{m['id']}", use_container_width=True):
                    save_prediction(user["id"], m["id"], int(ph), int(pa))
                    st.success(f"Saved: {m['home']} {int(ph)} – {int(pa)} {m['away']}")
                if existing:
                    st.caption(f"Your prediction: **{ex_h} – {ex_a}**")

    # ── Open knockout matches ─────────────────────────────────────────────────
    if ko_open:
        st.subheader(f"Open — Knockout Stage ({len(ko_open)})")
        st.caption("Score prediction = 90-min result. Also pick who wins if it's a draw (penalties).")
        for m in ko_open:
            existing   = user_preds.get(m["id"])
            ex_h       = existing[0] if existing else 0
            ex_a       = existing[1] if existing else 0
            ex_winner  = existing[2] if existing else None
            stage_lbl  = {"R32":"Round of 32","R16":"Round of 16","QF":"QF","SF":"SF","3rd":"3rd Place","F":"Final"}.get(m["stage"], m["stage"])
            cd = _countdown(m["kickoff_utc"])
            with st.expander(
                f"{stage_lbl} · {m['home_flag']} {m['home']} vs {m['away']} {m['away_flag']}"
                f"  —  {format_kickoff(m['kickoff_utc'], tz_offset)}"
                + (f"  {cd}" if cd else ""),
                expanded=False,
            ):
                st.caption(m["venue"])
                c1, cdash, c2 = st.columns([2, 0.5, 2])
                with c1:
                    st.markdown(f"**{m['home_flag']} {m['home']}**")
                    ph = st.number_input("Home", 0, 20, value=ex_h,
                                         key=f"ph_{m['id']}", label_visibility="collapsed")
                with cdash:
                    st.markdown("<div style='text-align:center;padding-top:.5rem;font-size:1.3rem;'>–</div>",
                                unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**{m['away_flag']} {m['away']}**")
                    pa = st.number_input("Away", 0, 20, value=ex_a,
                                         key=f"pa_{m['id']}", label_visibility="collapsed")

                # Show penalty winner selector when predicted score is a draw
                pred_winner = None
                if int(ph) == int(pa):
                    st.markdown("🔁 **Draw predicted — who wins on penalties?**")
                    pw_opts = [m["home"], m["away"]]
                    pw_idx  = pw_opts.index(ex_winner) if ex_winner in pw_opts else 0
                    pred_winner = st.radio(
                        "Penalty winner", pw_opts, index=pw_idx,
                        horizontal=True, key=f"pw_{m['id']}",
                        label_visibility="collapsed",
                    )
                else:
                    pred_winner = m["home"] if int(ph) > int(pa) else m["away"]

                lbl = "Update" if existing else "Submit"
                if st.button(lbl, key=f"btn_{m['id']}", use_container_width=True):
                    save_prediction(user["id"], m["id"], int(ph), int(pa), pred_winner)
                    st.success(f"Saved: {m['home']} {int(ph)} – {int(pa)} {m['away']}"
                               + (f" · Winner: {pred_winner}" if int(ph) == int(pa) else ""))
                if existing:
                    pw_show = f" · Winner pick: **{ex_winner}**" if ex_winner else ""
                    st.caption(f"Your prediction: **{ex_h} – {ex_a}**{pw_show}")

    if not open_m:
        st.info("No upcoming matches to predict yet.")

    # ── Live / locked ─────────────────────────────────────────────────────────
    if live_m:
        st.subheader(f"In Progress — Locked ({len(live_m)})")
        for m in live_m:
            ex    = user_preds.get(m["id"])
            is_ko = m.get("stage", "group") != "group"
            if ex:
                pw_show = f" · Winner: {ex[2]}" if (is_ko and ex[2]) else ""
                ps = f"{ex[0]} – {ex[1]}{pw_show}"
            else:
                ps = "No prediction"
            stage_lbl = {"R32":"R32","R16":"R16","QF":"QF","SF":"SF","3rd":"3rd","F":"Final"}.get(m.get("stage","group"), m["group"])
            st.markdown(f"""
            <div class="match-card live">
                <div class="match-teams">
                    <span>{m['home_flag']} {m['home']}</span>
                    <span class="match-score">LIVE</span>
                    <span>{m['away']} {m['away_flag']}</span>
                </div>
                <div class="match-meta">
                    {stage_lbl} &nbsp;|&nbsp; {m['venue']}
                    &nbsp;|&nbsp; Your pick: <b>{ps}</b>
                    &nbsp;<span class="badge badge-live">&#9679; LOCKED</span>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Completed ─────────────────────────────────────────────────────────────
    st.subheader(f"Completed ({len(done_m)})")
    if not done_m:
        st.caption("No completed matches yet.")
    for m in reversed(done_m):
        ex    = user_preds.get(m["id"])
        is_ko = m.get("stage", "group") != "group"
        stage_lbl = {"R32":"R32","R16":"R16","QF":"QF","SF":"SF","3rd":"3rd","F":"Final"}.get(m.get("stage","group"), f"Group {m['group']}")

        if ex:
            if is_ko:
                base, got_win = calc_points_knockout(
                    ex[0], ex[1], ex[2],
                    m["score_home"], m["score_away"], m.get("penalty_winner"),
                    m["home"], m["away"],
                )
                badge = _pts_badge_knockout(base, got_win)
                pw_show = f" · Winner: {ex[2]}" if ex[2] else ""
                ps    = f"{ex[0]} – {ex[1]}{pw_show}"
            else:
                pts   = calc_points(ex[0], ex[1], m["score_home"], m["score_away"])
                badge = _pts_badge_group(pts)
                ps    = f"{ex[0]} – {ex[1]}"
        else:
            badge = '<span class="badge" style="background:#444;color:#aaa;">No pick</span>'
            ps    = "—"

        pw_meta = f" · Pen: {m['penalty_winner']}" if m.get("penalty_winner") else ""
        st.markdown(f"""
        <div class="match-card completed">
            <div class="match-teams">
                <span>{m['home_flag']} {m['home']}</span>
                <span class="match-score">{m['score_home']} – {m['score_away']}</span>
                <span>{m['away']} {m['away_flag']}</span>
            </div>
            <div class="match-meta">
                {stage_lbl} &nbsp;|&nbsp; {m['venue']}
                &nbsp;|&nbsp; Your pick: <b>{ps}</b> &nbsp;{badge}{pw_meta}
            </div>
        </div>""", unsafe_allow_html=True)
