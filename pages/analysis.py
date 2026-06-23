import streamlit as st
import plotly.graph_objects as go
from db import get_matches, get_verified_users, get_all_predictions_all_matches, calc_points, calc_points_knockout


def render(user: dict):
    st.title("Analysis")
    st.caption("Prediction accuracy per user per match.")

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

    # ── Build outcome matrix ──────────────────────────────────────────────────
    # outcomes[user][match_id] = "exact" | "winner" | "wrong" | "none"
    outcomes = {u: {} for u in all_users}

    for m in done:
        mid   = m["id"]
        is_ko = m.get("stage", "group") != "group"
        preds = _all.get(mid, [])
        pred_by_user = {p["username"]: p for p in preds}

        for uname in all_users:
            p = pred_by_user.get(uname)
            if p is None:
                outcomes[uname][mid] = "none"
                continue

            ph, pa = p["pred_home"], p["pred_away"]
            ah, aa = m["score_home"], m["score_away"]

            if is_ko:
                base, _ = calc_points_knockout(
                    ph, pa, p.get("pred_winner"),
                    ah, aa, m.get("penalty_winner"),
                    m["home"], m["away"],
                )
                if base == 2:
                    outcomes[uname][mid] = "exact"
                elif base > 0:
                    outcomes[uname][mid] = "winner"
                else:
                    outcomes[uname][mid] = "wrong"
            else:
                pts = calc_points(ph, pa, ah, aa)
                if pts == 3:
                    outcomes[uname][mid] = "exact"
                elif pts == 1:
                    outcomes[uname][mid] = "winner"
                else:
                    outcomes[uname][mid] = "wrong"

    # ── Build heatmap data ────────────────────────────────────────────────────
    color_map = {"exact": 2, "winner": 1, "wrong": 0, "none": -1}
    label_map = {"exact": "Exact ✓", "winner": "Winner ✓", "wrong": "Wrong ✗", "none": "No pick"}

    match_labels = []
    for m in done:
        home = m["home"].split()[-1][:3].upper()
        away = m["away"].split()[-1][:3].upper()
        match_labels.append(f"{home}-{away}")

    # rows = users, columns = matches
    z        = []
    text     = []
    for uname in all_users:
        row_z    = []
        row_text = []
        for m in done:
            outcome = outcomes[uname][m["id"]]
            row_z.append(color_map[outcome])
            row_text.append(label_map[outcome])
        z.append(row_z)
        text.append(row_text)

    short_names = [
        u.split()[1] if len(u.split()) > 1 else u
        for u in all_users
    ]

    colorscale = [
        [0.00, "#1a1a1a"],   # -1 → no pick (dark grey)
        [0.25, "#1a1a1a"],
        [0.25, "#5c2222"],   # 0  → wrong (dark red)
        [0.50, "#5c2222"],
        [0.50, "#2d6a4f"],   # 1  → winner (green)
        [0.75, "#2d6a4f"],
        [0.75, "#C8A951"],   # 2  → exact (gold)
        [1.00, "#C8A951"],
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        x=match_labels,
        y=short_names,
        text=text,
        texttemplate="%{text}",
        textfont={"size": 9, "color": "white"},
        colorscale=colorscale,
        zmin=-1, zmax=2,
        showscale=False,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{text}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#f0f0f0"),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9),
            gridcolor="#222",
        ),
        yaxis=dict(
            tickfont=dict(size=11),
            autorange="reversed",
        ),
        height=max(300, len(all_users) * 55 + 120),
        margin=dict(l=10, r=10, t=20, b=80),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='display:flex;gap:1.5rem;justify-content:center;margin-top:-.5rem;'>"
        "<span style='color:#C8A951;font-size:.8rem;'>■ Exact score</span>"
        "<span style='color:#2d6a4f;font-size:.8rem;'>■ Correct winner</span>"
        "<span style='color:#5c2222;font-size:.8rem;'>■ Wrong</span>"
        "<span style='color:#444;font-size:.8rem;'>■ No pick</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ── Per-user accuracy summary ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("Accuracy Summary")

    cols = st.columns(len(all_users))
    for col, uname in zip(cols, all_users):
        user_outcomes = outcomes[uname]
        total   = len(done)
        exact   = sum(1 for v in user_outcomes.values() if v == "exact")
        winner  = sum(1 for v in user_outcomes.values() if v == "winner")
        wrong   = sum(1 for v in user_outcomes.values() if v == "wrong")
        no_pick = sum(1 for v in user_outcomes.values() if v == "none")
        correct = exact + winner
        pct     = round(correct / total * 100) if total else 0
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
