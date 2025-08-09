
# FootyEdge MVP (Demo)

This is a **Streamlit** skeleton wired with **dummy data**. Replace CSVs with API-backed tables later.

## Run locally
```bash
pip install streamlit pandas
streamlit run app.py
```

## Pages
- **Today:** fixtures, baseline xG estimates, value scorers (demo logic).
- **Player Compare:** head-to-head with key per-90s and errors→shot/goal.
- **FPL Captaincy:** crude expected points ranking.
- **Calibration:** placeholder (will populate after matches).
- **Team Overview:** home/away defensive splits + HT/FT matrix.

## Data
See `DATA_DICTIONARY.md` for columns and derivations.
