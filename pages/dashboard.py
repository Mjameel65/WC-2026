import streamlit as st
from datetime import datetime, timezone, timedelta, date
from db import get_matches, get_verified_users, get_all_predictions, calc_points
from tz import format_kickoff, local_date


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3

    st.title("Users Predictions")
    st.caption("All users' predictions — read only.")

    matches  = get_matches()
    users    = [u["username"] for u in get_verified_users()]
    all_pred = get_all_predictions()

    if not matches:
        st.info("No matches found.")
        return

    # ── Date helpers ──────────────────────────────────────────────────────────
    now_local = datetime.now(timezone.utc) + timedelta(hours=tz_offset)
    today     = now_local.date()
    yesterday = today - timedelta(days=1)
    tomorrow  = today + timedelta(days=1)

    # All dates that have at least one match (in user's local time)
    match_dates = sorted({date.fromisoformat(local_date(m["kickoff_utc"], tz_offset)) for m in matches})
    min_date    = match_dates[0]  if match_dates else today
    max_date    = match_dates[-1] if match_dates else today

    # ── Filter controls ───────────────────────────────────────────────────────
    f_col, d_col = st.columns([3, 2])

    with f_col:
        quick = st.radio(
            "quick_filter",
            ["Yesterday", "Today", "Tomorrow", "All"],
            index=1,
            horizontal=True,
            label_visibility="collapsed",
        )

    with d_col:
        custom_date = st.date_input(
            "📅 Specific date",
            value=None,
            min_value=min_date,
            max_value=max_date,
            label_visibility="visible",
        )

    # custom_date takes priority; otherwise use quick filter
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

    # Apply date filter
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

    st.markdown("---")

    # ── Match list ────────────────────────────────────────────────────────────
    for m in filtered:
        preds     = all_pred.get(m["id"], {})
        is_locked = m["locked"]
        is_done   = m["status"] == "completed"

        # ── Match header ──────────────────────────────────────────────────────
        if is_done:
            status_badge = '<span class="badge badge-completed">FT</span>'
            card_class   = "completed"
        elif is_locked:
            status_badge = '<span class="badge" style="background:#8B0000;color:#fff;">LIVE</span>'
            card_class   = "live"
        else:
            status_badge = '<span class="badge" style="background:#1d3557;color:#fff;">Upcoming</span>'
            card_class   = ""

        score_str = (f"{m['score_home']} – {m['score_away']}" if is_done else "vs")

        st.markdown(f"""
        <div class="match-card {card_class}" style="margin-bottom:.3rem;">
            <div class="match-teams">
                <span>{m['home_flag']} {m['home']}</span>
                <span class="match-score">{score_str}</span>
                <span>{m['away']} {m['away_flag']}</span>
            </div>
            <div class="match-meta">
                Group {m['group']} &nbsp;|&nbsp;
                {format_kickoff(m['kickoff_utc'], tz_offset)} &nbsp;|&nbsp;
                {m['venue']} &nbsp;{status_badge}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Predictions grid ──────────────────────────────────────────────────
        if not users:
            st.caption("No users yet.")
            continue

        cols = st.columns(len(users))
        for col, uname in zip(cols, users):
            pred  = preds.get(uname)
            short = uname.split()[1] if len(uname.split()) > 1 else uname
            is_me = uname == user["username"]

            if pred is None:
                col.markdown(f"""
                <div style='background:#111;border-radius:8px;padding:.5rem .6rem;
                            border:1px solid #2a2a2a;text-align:center;margin-bottom:.5rem;'>
                    <div style='font-size:.68rem;color:{"#C8A951" if is_me else "#888"};
                                font-weight:600;'>{short}</div>
                    <div style='font-size:.95rem;color:#444;margin:.25rem 0;'>– –</div>
                    <div style='font-size:.65rem;color:#444;'>No pick</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                ph, pa, pw = pred if len(pred) == 3 else (*pred, None)
                is_ko = m.get("stage", "group") != "group"
                if is_done:
                    if is_ko:
                        from db import calc_points_knockout
                        base, got_win = calc_points_knockout(
                            ph, pa, pw,
                            m["score_home"], m["score_away"], m.get("penalty_winner"),
                            m["home"], m["away"],
                        )
                        if base == 2:
                            bg, border, pt_color, label = "#1a1500", "#C8A951", "#C8A951", "Exact ✓"
                        elif got_win:
                            bg, border, pt_color, label = "#0a1a10", "#2d9e6b", "#2d9e6b", "Winner ✓"
                        else:
                            bg, border, pt_color, label = "#111", "#333", "#666", "Wrong ✗"
                        pts_html   = f"<div style='font-size:1.1rem;font-weight:900;color:{pt_color};'>+{base}</div>"
                        label_html = f"<div style='font-size:.62rem;color:{pt_color};font-weight:600;'>{label}</div>"
                    else:
                        pts = calc_points(ph, pa, m["score_home"], m["score_away"])
                        if pts == 3:
                            bg, border, pt_color, label = "#1a1500", "#C8A951", "#C8A951", "Exact ✓"
                        elif pts == 1:
                            bg, border, pt_color, label = "#0a1a10", "#2d9e6b", "#2d9e6b", "Winner ✓"
                        else:
                            bg, border, pt_color, label = "#111",    "#333",    "#666",    "Wrong ✗"
                        pts_html   = f"<div style='font-size:1.1rem;font-weight:900;color:{pt_color};'>+{pts}</div>"
                        label_html = f"<div style='font-size:.62rem;color:{pt_color};font-weight:600;'>{label}</div>"
                else:
                    bg, border, pt_color = "#111", "#444", "#aaa"
                    pts_html   = ""
                    label_html = "<div style='font-size:.62rem;color:#555;'>Pending</div>"
                pw_html = (f"<div style='font-size:.58rem;color:#888;'>→ {pw}</div>" if (is_ko and pw and ph == pa) else "")

                me_border = f"2px solid #C8A951" if is_me else f"1px solid {border}"
                col.markdown(f"""
                <div style='background:{bg};border-radius:8px;padding:.5rem .6rem;
                            border:{me_border};text-align:center;margin-bottom:.5rem;'>
                    <div style='font-size:.68rem;font-weight:600;
                                color:{"#C8A951" if is_me else "#aaa"};'>{short}</div>
                    <div style='font-size:1.05rem;font-weight:700;color:#fff;margin:.2rem 0;'>
                        {ph} – {pa}
                    </div>
                    {pw_html}
                    {label_html}
                    {pts_html}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:.8rem'></div>", unsafe_allow_html=True)
