import streamlit as st
from db import (get_matches, get_all_users, get_all_predictions_for_match,
                get_leaderboard, calc_points)
from tz import format_kickoff


def render(user: dict):
    tz_offset = user.get("tz_offset") or 3

    st.title("User Scores")
    st.caption("Full breakdown of every user's predictions vs actual match results.")

    matches   = get_matches()
    done      = [m for m in matches if m["status"] == "completed"]
    all_users = [u["username"] for u in get_all_users()]
    board     = {r["username"]: r for r in get_leaderboard()}

    if not done:
        st.info("No completed matches yet. Scores will appear here once results are in.")
        return

    # ── Points summary cards ──────────────────────────────────────────────────
    st.subheader("Points Summary")
    cols = st.columns(len(all_users))
    for col, uname in zip(cols, all_users):
        r     = board.get(uname, {})
        pts   = r.get("points",  0)
        exact = r.get("exact",   0)
        win   = r.get("winner",  0)
        wrong = r.get("wrong",   0)
        is_me = uname == user["username"]
        bg    = "linear-gradient(135deg,#8B0000,#3d0000)" if is_me else "#1a1a1a"
        col.markdown(f"""
        <div style='background:{bg};border-radius:12px;padding:1rem;text-align:center;
                    border:1px solid {"#C8A951" if is_me else "#333"};'>
            <div style='font-size:.75rem;color:#C8A951;font-weight:700;
                        text-transform:uppercase;letter-spacing:.06em;margin-bottom:.3rem;'>
                {uname.split()[1] if len(uname.split())>1 else uname}
            </div>
            <div style='font-size:2.2rem;font-weight:900;color:#C8A951;line-height:1;'>{pts}</div>
            <div style='font-size:.7rem;color:#aaa;margin-top:.2rem;'>points</div>
            <div style='display:flex;justify-content:center;gap:.8rem;margin-top:.5rem;'>
                <div style='font-size:.7rem;color:#fff;'>
                    <span style='font-weight:700;color:#C8A951;'>{exact}</span> exact
                </div>
                <div style='font-size:.7rem;color:#fff;'>
                    <span style='font-weight:700;color:#2d9e6b;'>{win}</span> winner
                </div>
                <div style='font-size:.7rem;color:#fff;'>
                    <span style='font-weight:700;color:#888;'>{wrong}</span> wrong
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Match-by-match grid ───────────────────────────────────────────────────
    st.subheader("Match-by-Match Breakdown")

    # Build prediction lookup: {match_id: {username: (ph, pa)}}
    pred_map = {}
    for m in done:
        preds = get_all_predictions_for_match(m["id"])
        pred_map[m["id"]] = {p["username"]: (p["pred_home"], p["pred_away"]) for p in preds}

    for m in done:
        preds = pred_map.get(m["id"], {})
        ah, aa = m["score_home"], m["score_away"]

        if ah > aa:
            outcome_str = f"**{m['home']}** wins"
        elif aa > ah:
            outcome_str = f"**{m['away']}** wins"
        else:
            outcome_str = "**Draw**"

        st.markdown(f"""
        <div class="match-card completed" style="margin-bottom:.4rem;">
            <div class="match-teams">
                <span>{m['home_flag']} {m['home']}</span>
                <span class="match-score">{ah} – {aa}</span>
                <span>{m['away']} {m['away_flag']}</span>
            </div>
            <div class="match-meta">
                Group {m['group']} &nbsp;|&nbsp;
                {format_kickoff(m['kickoff_utc'], tz_offset)} &nbsp;|&nbsp;
                {m['venue']}
                &nbsp;<span class="badge badge-completed">FT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Per-user result row
        ncols   = len(all_users)
        user_cols = st.columns(ncols)

        for col, uname in zip(user_cols, all_users):
            pred = preds.get(uname)
            is_me = uname == user["username"]
            short = uname.split()[1] if len(uname.split()) > 1 else uname

            if pred is None:
                col.markdown(f"""
                <div style='background:#111;border-radius:8px;padding:.5rem .7rem;
                            border:1px solid #333;text-align:center;'>
                    <div style='font-size:.7rem;color:#888;font-weight:600;'>{short}</div>
                    <div style='font-size:1rem;color:#555;margin:.2rem 0;'>— vs —</div>
                    <div style='font-size:.7rem;color:#555;'>No pick</div>
                    <div style='font-size:1.1rem;font-weight:800;color:#555;margin-top:.2rem;'>0 pts</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                ph, pa = pred
                pts    = calc_points(ph, pa, ah, aa)
                if pts == 3:
                    pt_color = "#C8A951"
                    pt_label = "Exact ✓"
                    border   = "#C8A951"
                    bg_card  = "#1a1500"
                elif pts == 1:
                    pt_color = "#2d9e6b"
                    pt_label = "Winner ✓"
                    border   = "#2d9e6b"
                    bg_card  = "#0a1a10"
                else:
                    pt_color = "#888"
                    pt_label = "Wrong ✗"
                    border   = "#333"
                    bg_card  = "#111"

                me_border = "#C8A951" if is_me else border
                col.markdown(f"""
                <div style='background:{bg_card};border-radius:8px;padding:.5rem .7rem;
                            border:2px solid {me_border};text-align:center;'>
                    <div style='font-size:.7rem;color:#aaa;font-weight:600;'>{short}</div>
                    <div style='font-size:1.1rem;font-weight:700;color:#fff;margin:.2rem 0;'>
                        {ph} – {pa}
                    </div>
                    <div style='font-size:.65rem;color:{pt_color};font-weight:600;'>{pt_label}</div>
                    <div style='font-size:1.3rem;font-weight:900;color:{pt_color};margin-top:.1rem;'>
                        +{pts}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:1rem'></div>", unsafe_allow_html=True)

    # ── Running total row ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Total Points")

    rank_sorted = sorted(all_users, key=lambda u: -board.get(u, {}).get("points", 0))
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}

    total_cols = st.columns(len(all_users))
    for col, uname in zip(total_cols, all_users):
        r      = board.get(uname, {})
        pts    = r.get("points", 0)
        rank_i = rank_sorted.index(uname)
        medal  = medals.get(rank_i, f"#{rank_i+1}")
        is_me  = uname == user["username"]
        short  = uname.split()[1] if len(uname.split()) > 1 else uname
        bg     = "linear-gradient(135deg,#8B0000,#3d0000)" if is_me else "#1a1a1a"
        border = "2px solid #C8A951" if is_me else "1px solid #333"

        col.markdown(f"""
        <div style='background:{bg};border-radius:10px;padding:.8rem;
                    text-align:center;border:{border};'>
            <div style='font-size:1.4rem;'>{medal}</div>
            <div style='font-size:.75rem;color:#aaa;font-weight:600;margin:.2rem 0;'>{short}</div>
            <div style='font-size:2rem;font-weight:900;color:#C8A951;'>{pts}</div>
            <div style='font-size:.65rem;color:#888;'>pts from {len(done)} match(es)</div>
        </div>
        """, unsafe_allow_html=True)
