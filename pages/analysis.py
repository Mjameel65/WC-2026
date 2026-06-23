import streamlit as st
import plotly.graph_objects as go
from db import get_matches, get_verified_users, get_all_predictions_all_matches, calc_points, calc_points_knockout


def render(user: dict):
    st.title("Analysis")
    st.caption("Points earned per user per match.")

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

    # ── Build points matrix & filter to matches with at least one prediction ──
    # points[uname][match_id] = points earned (None = no pick)
    points_data = {u: {} for u in all_users}

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
                points_data[uname][mid] = None
                continue
            has_any = True
            ph, pa = p["pred_home"], p["pred_away"]
            ah, aa = m["score_home"], m["score_away"]
            if is_ko:
                base, _ = calc_points_knockout(
                    ph, pa, p.get("pred_winner"),
                    ah, aa, m.get("penalty_winner"),
                    m["home"], m["away"],
                )
                points_data[uname][mid] = base
            else:
                points_data[uname][mid] = calc_points(ph, pa, ah, aa)

        if has_any:
            active_matches.append(m)

    if not active_matches:
        st.info("No predictions submitted yet.")
        return

    # ── Match x-axis labels ───────────────────────────────────────────────────
    match_labels = []
    for m in active_matches:
        home = m["home"].split()[-1][:3].upper()
        away = m["away"].split()[-1][:3].upper()
        match_labels.append(f"{home} v {away}")

    # ── Colour palette per user ───────────────────────────────────────────────
    palette = [
        "#C8A951", "#2d9e6b", "#4e8ef7", "#e06c75",
        "#56b6c2", "#d19a66", "#c678dd", "#98c379",
    ]

    short_names = [
        u.split()[1] if len(u.split()) > 1 else u
        for u in all_users
    ]

    # ── Grouped bar chart ─────────────────────────────────────────────────────
    fig = go.Figure()

    for i, (uname, short) in enumerate(zip(all_users, short_names)):
        color = palette[i % len(palette)]
        bar_values  = []
        bar_colors  = []
        hover_texts = []

        for m in active_matches:
            mid = m["id"]
            pts = points_data[uname].get(mid)
            is_ko = m.get("stage", "group") != "group"
            max_pts = 2 if is_ko else 3

            if pts is None:
                bar_values.append(0)
                bar_colors.append("#2a2a2a")
                hover_texts.append("No pick")
            elif pts == max_pts:
                bar_values.append(pts)
                bar_colors.append("#C8A951")   # gold — exact
                hover_texts.append(f"Exact ✓  +{pts} pts")
            elif pts > 0:
                bar_values.append(pts)
                bar_colors.append("#2d9e6b")   # green — winner
                hover_texts.append(f"Winner ✓  +{pts} pts")
            else:
                bar_values.append(0.15)        # tiny stub so bar is visible
                bar_colors.append("#5c2222")   # dark red — wrong
                hover_texts.append("Wrong ✗  0 pts")

        fig.add_trace(go.Bar(
            name=short,
            x=match_labels,
            y=bar_values,
            marker_color=bar_colors,
            text=[f"+{v}" if v > 0.15 else "✗" for v in bar_values],
            textposition="outside",
            textfont=dict(size=10, color="#f0f0f0"),
            hovertext=hover_texts,
            hovertemplate=f"<b>{short}</b><br>%{{x}}<br>%{{hovertext}}<extra></extra>",
            legendgroup=short,
            showlegend=True,
        ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f0f0f0", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="center", x=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            tickangle=-40,
            tickfont=dict(size=10),
            gridcolor="#1a1a1a",
            linecolor="#333",
        ),
        yaxis=dict(
            title="Points",
            range=[0, 4],
            tickvals=[0, 1, 2, 3],
            gridcolor="#1a1a1a",
            linecolor="#333",
        ),
        height=480,
        margin=dict(l=10, r=10, t=60, b=80),
        bargap=0.18,
        bargroupgap=0.05,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Accuracy summary cards ────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Accuracy Summary")

    cols = st.columns(len(all_users))
    for col, uname in zip(cols, all_users):
        vals    = [points_data[uname].get(m["id"]) for m in active_matches]
        played  = [v for v in vals if v is not None]
        is_ko_map = {m["id"]: m.get("stage", "group") != "group" for m in active_matches}
        exact   = sum(1 for m in active_matches if points_data[uname].get(m["id"]) == (2 if is_ko_map[m["id"]] else 3))
        winner  = sum(1 for m in active_matches
                      if points_data[uname].get(m["id"]) not in (None, 0)
                      and points_data[uname].get(m["id"]) != (2 if is_ko_map[m["id"]] else 3))
        wrong   = sum(1 for v in vals if v == 0)
        no_pick = sum(1 for v in vals if v is None)
        correct = exact + winner
        pct     = round(correct / len(played) * 100) if played else 0
        short   = uname.split()[1] if len(uname.split()) > 1 else uname
        is_me   = uname == user["username"]
        bg      = "linear-gradient(135deg,#8B0000,#3d0000)" if is_me else "#1a1a1a"
        border  = "2px solid #C8A951" if is_me else "1px solid #333"

        col.markdown(
            f"<div style='background:{bg};border-radius:10px;padding:.8rem;"
            f"text-align:center;border:{border};'>"
            f"<div style='font-size:.72rem;color:#C8A951;font-weight:700;'>{short}</div>"
            f"<div style='font-size:2rem;font-weight:900;color:#fff;line-height:1.1;'>{pct}%</div>"
            f"<div style='font-size:.65rem;color:#aaa;margin-bottom:.3rem;'>accuracy</div>"
            f"<div style='font-size:.68rem;color:#C8A951;'>{exact} exact</div>"
            f"<div style='font-size:.68rem;color:#2d9e6b;'>{winner} winner</div>"
            f"<div style='font-size:.68rem;color:#888;'>{wrong} wrong · {no_pick} no pick</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
