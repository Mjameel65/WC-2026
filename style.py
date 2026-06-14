"""Shared CSS injected on every page."""

GLOBAL_CSS = """
<style>
/* ── Mobile-first base ───────────────────────────────────────────────── */
:root {
    --primary: #8B0000;
    --gold:    #C8A951;
    --bg:      #0a0a0a;
    --card:    #1a1a1a;
    --text:    #f0f0f0;
    --muted:   #888;
    --live:    #e63946;
    --done:    #2d6a4f;
    --upcoming:#1d3557;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background-color: #111 !important;
}

/* hide default streamlit header */
header[data-testid="stHeader"] { display: none; }

/* compact tabs */
.stTabs [role="tablist"] { gap: 0.25rem; }
.stTabs [role="tab"] {
    background: var(--card);
    border-radius: 6px 6px 0 0;
    color: var(--text);
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important;
    color: #fff !important;
}

/* ── Match card ──────────────────────────────────────────────────────── */
.match-card {
    background: var(--card);
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.7rem;
    border-left: 4px solid var(--muted);
    transition: border-color 0.2s;
}
.match-card.live     { border-left-color: var(--live); }
.match-card.completed{ border-left-color: var(--done); }
.match-card.upcoming { border-left-color: var(--upcoming); }

.match-teams {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 1.05rem;
    font-weight: 600;
    flex-wrap: wrap;
    gap: 0.3rem;
}
.match-score {
    background: #2a2a2a;
    padding: 0.2rem 0.7rem;
    border-radius: 8px;
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--gold);
    min-width: 60px;
    text-align: center;
}
.match-meta {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.35rem;
}
.badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge-live     { background: var(--live);     color: #fff; }
.badge-completed{ background: var(--done);     color: #fff; }
.badge-upcoming { background: var(--upcoming); color: #fff; }

/* ── Standings table ─────────────────────────────────────────────────── */
.st-table { width: 100%; }
table { width: 100%; border-collapse: collapse; }
th {
    background: var(--primary);
    color: #fff;
    padding: 0.4rem 0.6rem;
    text-align: center;
    font-size: 0.8rem;
}
td {
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid #222;
    text-align: center;
    font-size: 0.85rem;
}
tr:nth-child(odd) td  { background: #141414; }
tr:nth-child(even) td { background: #1e1e1e; }
tr.qualify td  { color: var(--gold); }

/* ── Hero banner ─────────────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, var(--primary) 0%, #3d0000 100%);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
}
.hero h1 { font-size: 2rem; margin: 0; color: var(--gold); }
.hero p  { margin: 0.3rem 0 0; color: #ddd; font-size: 0.95rem; }

/* ── Group header ────────────────────────────────────────────────────── */
.group-header {
    background: var(--primary);
    color: var(--gold);
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1.1rem;
    margin: 1rem 0 0.5rem;
}

/* ── Responsive: single column on narrow screens ─────────────────────── */
@media (max-width: 600px) {
    .match-teams { font-size: 0.9rem; }
    .hero h1     { font-size: 1.5rem; }
    .stColumn    { min-width: 100% !important; }
}

/* ── Buttons ────────────────────────────────────────────────────────── */
.stButton > button {
    background: var(--primary) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background: #a00000 !important;
}
</style>
"""


def inject_css():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
