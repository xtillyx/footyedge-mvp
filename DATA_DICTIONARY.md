
# FootyEdge MVP — Data Dictionary (v0.1)

## Tables

### teams.csv
- team_id: int
- name: str
- league: str

### players.csv
- player_id: int
- team_id: int (FK -> teams)
- name: str
- position: str
- is_pen_taker: bool
- set_piece_role: str

### fixtures.csv
- fix_id: int
- date: YYYY-MM-DD
- home_id: int (FK -> teams)
- away_id: int (FK -> teams)
- venue: str
- status: str (NS/FT etc.)

### player_stats.csv (per 90 unless indicated)
- player_id: int (FK -> players)
- season: str
- per90_shots: float
- per90_npxG: float
- per90_xA: float
- dribbles_att: float
- dribbles_succ: float
- duels: float
- duels_won: float
- aerials_won: float
- headers_goals_pct: int
- set_piece_goals_pct: int
- tackles_att: float
- tackles_won: float
- interceptions: float
- blocks: float
- errors_to_shot: float (per 90)
- errors_to_goal: float (per 90)
- minutes_played: int (season total)
- starts_pct: float (0-1)

### team_form.csv
- team_id: int (FK -> teams)
- rolling10_xGF: float
- rolling10_xGA: float
- ppda_proxy: float
- set_piece_share_xG: float
- xGD90_home: float
- xGD90_away: float
- xGA90_home: float
- xGA90_away: float
- cs_pct_home: float (0-1)
- cs_pct_away: float (0-1)
- late_gf_per_match: float
- late_ga_per_match: float
- late_gf_share: float (0-1)
- late_ga_share: float (0-1)
- htft_HH ... htft_LL: ints (9 cells)

### odds.csv (placeholder)
- fix_id: int (FK -> fixtures)
- book: str
- market: str
- selection: str
- decimal_odds: float
- pulled_at: timestamp

## Derived
- Team xG (baseline): blend of rolling10_xGF and opponent's rolling10_xGA
- Player μ (expected goals): minutes_factor * (team_xG * player_share) (+ small pen bump if pen taker in demo)
- P(score) = 1 - exp(-μ)
- Fair odds = 1 / P(score)

## Notes
- All demo numbers are fake; adapters will map real API fields to these columns.
- Errors leading to shot/goal will map from provider fields when available.
