import streamlit as st
import pandas as pd
import os
from math import exp

st.set_page_config(page_title="FootyEdge MVP", page_icon="⚽", layout="wide")

# ---- PASSWORD GATE ----
def password_gate():
    st.session_state.setdefault("authed", False)
    correct_pw = os.environ.get("FOOTYEDGE_PASSWORD", "tilly")  # change via Streamlit Secrets
    if st.session_state.get("authed"):
        return True
    st.sidebar.subheader("🔒 Private Access")
    pw = st.sidebar.text_input("Enter password", type="password")
    if pw and pw == correct_pw:
        st.session_state["authed"] = True
        st.sidebar.success("Access granted")
        return True
    if pw and pw != correct_pw:
        st.sidebar.error("Wrong password")
    st.stop()

@st.cache_data
def load():
    teams = pd.read_csv("data/teams.csv")
    players = pd.read_csv("data/players.csv")
    fixtures = pd.read_csv("data/fixtures.csv")
    pstats = pd.read_csv("data/player_stats.csv")
    tform = pd.read_csv("data/team_form.csv")
    return teams, players, fixtures, pstats, tform

teams, players, fixtures, pstats, tform = load()
password_gate(

st.sidebar.title("FootyEdge MVP")
page = st.sidebar.radio("Go to", ["Today", "Player Compare", "FPL Captaincy", "Calibration", "Team Overview"])

# Helper lookups
team_name = dict(zip(teams.team_id, teams.name))

# --- Simple baseline team xG/xGA from rolling form
def team_baselines(home_id, away_id):
    tf = tform.set_index("team_id")
    xg_h = tf.loc[home_id, "rolling10_xGF"]
    xga_h = tf.loc[home_id, "rolling10_xGA"]
    xg_a = tf.loc[away_id, "rolling10_xGF"]
    xga_a = tf.loc[away_id, "rolling10_xGA"]
    # blend for match expectation
    team_xG_home = 0.6*xg_h + 0.4*xga_a # crude blend
    team_xG_away = 0.6*xg_a + 0.4*xga_h
    return team_xG_home, team_xG_away

def fair_prob_from_mu(mu):
    return 1 - exp(-mu)

if page == "Today":
    st.header("Today")
    for _, row in fixtures.iterrows():
        home = team_name[row.home_id]; away = team_name[row.away_id]
        st.subheader(f"{home} vs {away} — {row.date} ({row.status})")
        c1, c2, c3 = st.columns([2,2,3])
        with c1:
            st.caption("Team baselines (rolling form blend)")
            hxg, axg = team_baselines(row.home_id, row.away_id)
            st.metric("Home xG (est)", f"{hxg:.2f}")
            st.metric("Away xG (est)", f"{axg:.2f}")
        with c2:
            st.caption("Home/Away defensive splits")
            tf = tform.set_index("team_id")
            st.write(pd.DataFrame({
                "xGA90 Home/Away":[f"{tf.loc[row.home_id,'xGA90_home']:.2f}/{tf.loc[row.home_id,'xGA90_away']:.2f}",
                                   f"{tf.loc[row.away_id,'xGA90_home']:.2f}/{tf.loc[row.away_id,'xGA90_away']:.2f}"],
                "CS% Home/Away":[f"{int(100*tf.loc[row.home_id,'cs_pct_home'])}%/{int(100*tf.loc[row.home_id,'cs_pct_away'])}%",
                                 f"{int(100*tf.loc[row.away_id,'cs_pct_home'])}%/{int(100*tf.loc[row.away_id,'cs_pct_away'])}%"]
            }, index=[home, away]))
        with c3:
            st.caption("Value Scorers (μ → P → fair odds) — dummy demo")
            # demo using top shooter from each team
            merged = players.merge(pstats, on="player_id")
            home_players = merged[merged.team_id==row.home_id].nlargest(3,"per90_npxG")
            away_players = merged[merged.team_id==row.away_id].nlargest(3,"per90_npxG")
            def scorer_table(df, team_xg):
                out = []
                for _, r in df.iterrows():
                    minutes_factor = 0.9 * r["starts_pct"]
                    share = max(0.15, min(0.45, r["per90_npxG"]/1.0))  # crude share proxy
                    mu = minutes_factor*(team_xg*share)
                    if r["is_pen_taker"]:
                        mu += 0.05  # tiny pen bump for demo
                    p = fair_prob_from_mu(mu)
                    fair_odds = 1.0/max(1e-6,p)
                    out.append([r["name"], r["position"], mu, p, fair_odds])
                return pd.DataFrame(out, columns=["Player","Pos","μ","P(score)","Fair Odds"])
            st.write("**Home**")
            st.dataframe(scorer_table(home_players, hxg))
            st.write("**Away**")
            st.dataframe(scorer_table(away_players, axg))

elif page == "Player Compare":
    st.header("Player Compare")
    p1, p2 = st.columns(2)
    with p1:
        a = st.selectbox("Player A", players.name.tolist(), index=0)
    with p2:
        b = st.selectbox("Player B", players.name.tolist(), index=2)
    pa = players[players.name==a].merge(pstats, on="player_id").iloc[0]
    pb = players[players.name==b].merge(pstats, on="player_id").iloc[0]
    df = pd.DataFrame({
        "Metric":["Shots/90","npxG/90","xA/90","Dribble Success %","Duel Win %","Tackles Won %","Errors→Shot/90","Errors→Goal/90"],
        a:[pa.per90_shots, pa.per90_npxG, pa.per90_xA, 100*pa.dribbles_succ/max(1,pa.dribbles_att), 100*pa.duels_won/max(1,pa.duels), 100*pa.tackles_won/max(1,pa.tackles_att), pa.errors_to_shot, pa.errors_to_goal],
        b:[pb.per90_shots, pb.per90_npxG, pb.per90_xA, 100*pb.dribbles_succ/max(1,pb.dribbles_att), 100*pb.duels_won/max(1,pb.duels), 100*pb.tackles_won/max(1,pb.tackles_att), pb.errors_to_shot, pb.errors_to_goal]
    })
    st.dataframe(df)

elif page == "FPL Captaincy":
    st.header("FPL Captaincy Shortlist (demo)")
    # naive expected points ≈ (npxG + 0.7*xA) * 5 pts per expected G+A
    merged = players.merge(pstats, on="player_id")
    merged["exp_points"] = (merged["per90_npxG"] + 0.7*merged["per90_xA"]) * 5
    st.dataframe(merged[["name","position","is_pen_taker","per90_npxG","per90_xA","exp_points"]].sort_values("exp_points", ascending=False))

elif page == "Calibration":
    st.header("Calibration (placeholder)")
    st.write("After a few gameweeks, this page will show predicted vs actual scoring by probability buckets and apply isotonic scaling if needed.")

elif page == "Team Overview":
    st.header("Team Overview")
    tsel = st.selectbox("Team", teams.name.tolist(), index=0)
    tid = teams[teams.name==tsel].team_id.iloc[0]
    tf = tform[tform.team_id==tid].iloc[0]
    c1,c2,c3 = st.columns(3)
    with c1:
        st.metric("xGD90 Home", f"{tf.xGD90_home:.2f}")
        st.metric("xGD90 Away", f"{tf.xGD90_away:.2f}")
    with c2:
        st.metric("xGA90 Home", f"{tf.xGA90_home:.2f}")
        st.metric("xGA90 Away", f"{tf.xGA90_away:.2f}")
    with c3:
        st.metric("CS% Home", f"{int(100*tf.cs_pct_home)}%")
        st.metric("CS% Away", f"{int(100*tf.cs_pct_away)}%")

    st.subheader("HT/FT Matrix (counts)")
    mat = pd.DataFrame({
        "HT H":["HH","HD","HL"],
        "HT D":["DH","DD","DL"],
        "HT L":["LH","LD","LL"]
    }, index=["FT H","FT D","FT L"])
    vals = pd.DataFrame({
        "HH":[tf.htft_HH, tf.htft_DH, tf.htft_LH],
        "HD":[tf.htft_HD, tf.htft_DD, tf.htft_LD],
        "HL":[tf.htft_HL, tf.htft_DL, tf.htft_LL]
    }, index=["FT H","FT D","FT L"])
    st.dataframe(vals)
