import streamlit as st
import plotly.graph_objects as go
from db import get_matches, get_verified_users, get_all_predictions_all_matches, calc_points, calc_points_knockout


_PALETTE = [
    "#C8A951","#2d9e6b","#4e8ef7","#e06c75","#56b6c2",
    "#d19a66","#c678dd","#98c379","#e5c07b","#61afef",
    "#be5046","#5c6370","#abb2bf","#e06c75","#528bff",
    "#7c6f64","#fabd2f","#8ec07c","#83a598","#d3869b",
    "#b8bb26","#fb4934","#fe8019","#689d6a","#458588",
]

OUTCOME_COLOR = {
    "exact":  "#C8A951",
    "winner": "#2d9e6b",
    "wrong":  "#7a1c1c",
    "none":   "#1e1e1e",
}


def _calc_outcome(pts, is_ko):
    if pts is None:
        return "none"
    max_pts = 2 if is_ko else 3
    if pts == max_pts:
        return "exact"
    if pts > 0:
        return "winner"
    return "wrong"


def render(user: dict):
    st.title("Analysis")

    matches   = get_matches()
    done      = [m for m in matches if m["status"] == "completed"]
    all_users = [u["username"] for u in get_verified_users()]

    if not done:
        st.info("No completed matches yet.")
        return
    if not all_users:
        st.info("No users yet.")
        return

    _all = get_all_predictions_all_matches()

    # ── Build points & outcome per user per match ─────────────────────────────
    pts_matrix     = {u: {} for u in all_users}
    outcome_matrix = {u: {} for u in all_users}

    active_matches = []
    for m in done:
        mid   = m["id"]
        is_ko = m.get("stage", "group") != "group"
        preds = _all.get(mid, [])
        pred_by_user = {p["username"]: p for p in preds}

        has_any = False
        for uname in all_users:
            p = pred_by_user.get(uname)
            if p is None:
                pts_matrix[uname][mid]     = None
                outcome_matrix[uname][mid] = "none"
                continue
            has_any = True
            ph, pa = p["pred_home"], p["pred_away"]
            ah, aa = m["score_home"], m["score_away"]
            if is_ko:
                pts, _ = calc_points_knockout(
                    ph, pa, p.get("pred_winner"),
                    ah, aa, m.get("penalty_winner"), m["home"], m["away"],
                )
            else:
                pts = calc_points(ph, pa, ah, aa)
            pts_matrix[uname][mid]     = pts
            outcome_matrix[uname][mid] = _calc_outcome(pts, is_ko)

        if has_any:
            active_matches.append(m)

    if not active_matches:
        st.info("No predictions submitted yet.")
        return

    short_names = {
        u: (u.split()[1] if len(u.split()) > 1 else u)
        for u in all_users
    }

    match_labels = []
    for m in active_matches:
        home = m["home"].split()[-1][:3].upper()
        away = m["away"].split()[-1][:3].upper()
        match_labels.append(f"{home}-{away}")

    # ══════════════════════════════════════════════════════════════════════════
    # Chart 1 — Cumulative points line chart
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("Cumulative Points Race")

    fig_line = go.Figure()
    for i, uname in enumerate(all_users):
        color  = _PALETTE[i % len(_PALETTE)]
        short  = short_names[uname]
        cumulative = []
        total = 0
        for m in active_matches:
            p = pts_matrix[uname].get(m["id"])
            total += p if p is not None else 0
            cumulative.append(total)

        fig_line.add_trace(go.Scatter(
            x=match_labels,
            y=cumulative,
            mode="lines+markers",
            name=short,
            line=dict(color=color, width=2),
            marker=dict(size=6, color=color),
            hovertemplate=f"<b>{short}</b><br>After %{{x}}: <b>%{{y}} pts</b><extra></extra>",
        ))

    fig_line.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f0f0f0", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
            itemwidth=40,
        ),
        xaxis=dict(
            tickangle=-40, tickfont=dict(size=9),
            gridcolor="#1a1a1a", linecolor="#333",
        ),
        yaxis=dict(
            title="Total Points",
            gridcolor="#1a1a1a", linecolor="#333",
            zeroline=False,
        ),
        height=400,
        margin=dict(l=10, r=10, t=80, b=80),
        hovermode="x unified",
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Chart 2 — Rank Race
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("Rank Race")
    st.caption("Position after each completed match — #1 is leading.")

    rank_history = {u: [] for u in all_users}
    for mi in range(len(active_matches)):
        cum = {
            uname: sum(
                (pts_matrix[uname].get(active_matches[j]["id"]) or 0)
                for j in range(mi + 1)
            )
            for uname in all_users
        }
        sorted_names = sorted(all_users, key=lambda u: -cum[u])
        for rank_pos, uname in enumerate(sorted_names, 1):
            rank_history[uname].append(rank_pos)

    fig_rank = go.Figure()
    n_users = len(all_users)
    for i, uname in enumerate(all_users):
        color = _PALETTE[i % len(_PALETTE)]
        short = short_names[uname]
        fig_rank.add_trace(go.Scatter(
            x=match_labels,
            y=rank_history[uname],
            mode="lines+markers",
            name=short,
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            hovertemplate=f"<b>{short}</b><br>After %{{x}}: <b>#%{{y}}</b><extra></extra>",
        ))

    fig_rank.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f0f0f0", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            font=dict(size=10),
            bgcolor="rgba(0,0,0,0)",
            itemwidth=40,
        ),
        xaxis=dict(
            tickangle=-40, tickfont=dict(size=9),
            gridcolor="#1a1a1a", linecolor="#333",
        ),
        yaxis=dict(
            title="Rank",
            autorange="reversed",
            tickmode="linear", tick0=1, dtick=1,
            range=[n_users + 0.5, 0.5],
            gridcolor="#1a1a1a", linecolor="#333",
            zeroline=False,
        ),
        height=400,
        margin=dict(l=10, r=10, t=80, b=80),
        hovermode="x unified",
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Chart 3 — Outcome dot grid (users × matches)
    # ══════════════════════════════════════════════════════════════════════════
    st.subheader("Prediction Outcomes Grid")
    st.caption("🟡 Exact &nbsp; 🟢 Correct winner &nbsp; 🔴 Wrong &nbsp; ⬛ No pick")

    # Build scatter dot chart: one dot per (user, match)
    dot_x, dot_y, dot_colors, dot_hover = [], [], [], []

    outcome_label = {
        "exact":  "Exact ✓",
        "winner": "Winner ✓",
        "wrong":  "Wrong ✗",
        "none":   "No pick",
    }

    for ui, uname in enumerate(all_users):
        short = short_names[uname]
        for mi, m in enumerate(active_matches):
            outcome = outcome_matrix[uname][m["id"]]
            dot_x.append(mi)
            dot_y.append(ui)
            dot_colors.append(OUTCOME_COLOR[outcome])
            dot_hover.append(
                f"<b>{short}</b><br>{match_labels[mi]}<br>{outcome_label[outcome]}"
            )

    fig_grid = go.Figure(go.Scatter(
        x=dot_x,
        y=dot_y,
        mode="markers",
        marker=dict(
            color=dot_colors,
            size=14,
            symbol="square",
            line=dict(width=0),
        ),
        hovertext=dot_hover,
        hovertemplate="%{hovertext}<extra></extra>",
        showlegend=False,
    ))

    fig_grid.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f0f0f0", size=10),
        xaxis=dict(
            tickvals=list(range(len(active_matches))),
            ticktext=match_labels,
            tickangle=-45,
            tickfont=dict(size=9),
            gridcolor="#111",
            zeroline=False,
            range=[-0.5, len(active_matches) - 0.5],
        ),
        yaxis=dict(
            tickvals=list(range(len(all_users))),
            ticktext=[short_names[u] for u in all_users],
            tickfont=dict(size=10),
            gridcolor="#111",
            zeroline=False,
            range=[-0.5, len(all_users) - 0.5],
            autorange="reversed",
        ),
        height=max(300, len(all_users) * 32 + 120),
        margin=dict(l=10, r=10, t=20, b=80),
    )
    st.plotly_chart(fig_grid, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # Accuracy summary cards
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.subheader("Accuracy Summary")

    is_ko_map = {m["id"]: m.get("stage", "group") != "group" for m in active_matches}
    cols = st.columns(min(len(all_users), 8))
    sorted_users = sorted(
        all_users,
        key=lambda u: -sum(v for v in pts_matrix[u].values() if v is not None)
    )
    for idx, uname in enumerate(sorted_users):
        col   = cols[idx % len(cols)]
        short = short_names[uname]
        vals  = outcome_matrix[uname]
        played  = [v for v in vals.values() if v != "none"]
        exact   = sum(1 for v in vals.values() if v == "exact")
        winner  = sum(1 for v in vals.values() if v == "winner")
        wrong   = sum(1 for v in vals.values() if v == "wrong")
        no_pick = sum(1 for v in vals.values() if v == "none")
        correct = exact + winner
        pct     = round(correct / len(played) * 100) if played else 0
        total_pts = sum(v for v in pts_matrix[uname].values() if v is not None)
        is_me   = uname == user["username"]
        bg      = "linear-gradient(135deg,#8B0000,#3d0000)" if is_me else "#1a1a1a"
        border  = "2px solid #C8A951" if is_me else "1px solid #333"

        col.markdown(
            f"<div style='background:{bg};border-radius:10px;padding:.7rem;"
            f"text-align:center;border:{border};margin-bottom:.5rem;'>"
            f"<div style='font-size:.7rem;color:#C8A951;font-weight:700;'>{short}</div>"
            f"<div style='font-size:1.6rem;font-weight:900;color:#fff;line-height:1.1;'>{pct}%</div>"
            f"<div style='font-size:.6rem;color:#aaa;'>{total_pts} pts total</div>"
            f"<div style='font-size:.62rem;color:#C8A951;margin-top:.3rem;'>{exact} exact</div>"
            f"<div style='font-size:.62rem;color:#2d9e6b;'>{winner} winner</div>"
            f"<div style='font-size:.62rem;color:#888;'>{wrong} wrong · {no_pick} skip</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
