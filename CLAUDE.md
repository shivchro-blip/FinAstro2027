# FinAstro 2027: notes for Claude Code sessions

Read `PROJECT_KNOWLEDGE.md` first. It holds the sources, conventions, user decisions, code map, findings and rebuild commands for all gold and silver work. Finished, ready-to-open reports are in `reports/` (start with `reports/index.html`); refresh them with `tools/refresh_all.py`, never by editing the copies. The original 2027 calendar build is described in `README.md` and `build/NEXT_SESSION.md`.

## Decisions to respect

- Implement a rule only when a source states it. Do not extrapolate; for example, there is no Moon mirror of the gold Sun rules for silver.
- **Vedic sources are in scope:** TA, KD, the 2026 document, the user's notes, Brihat Samhita, BPHS for Shadbala, and the NYSE monthly solar-return technique ("Investing in Stock Market with Vedic Astrology", Vol. II; shared 24 Nov 2026). Reference charts: NYSE (17 May 1792, New York) and USA (4 Jul 1776, Sibly time) in `tools/nyse_charts.py`; their Vimshottari dashas (Maha → Antar → Pratyantar → Sookshma → Prana) with transits in `tools/dasha_transits.py` and `tools/dasha_combinations.py`.
- **Bayer and the Western sources are out of scope:** McWhirter, Williams, Weingarten, Timing Solutions, and the 'Moon and Silver' guide.
- Reports use US Eastern time (America/New_York). Calculations use sidereal Lahiri, mean node and whole-sign drishti.
- Stock market work uses the S&P 500 and the BSE Sensex (user's choice, 23 Nov 2026), each scored in its own exchange time; the rule set is every catalogue rule tagged "general".
- Analysis uses market prices and astrology only; news and fundamentals are not used or recorded (user, 24 Nov 2026).
- **Dashas are parked** (user, 24 Nov 2026): tested at every level and as classical combinations, no S&P edge. They are kept as reference reports but not used in the combined model or the day-by-day pages (`USE_DASHA = False` in `tools/forward_daybyday.py`). Work continues with the Solar return method.
- Call the NYSE solar-return astrologer's material **Solar return** in reports, never "the author" (user, 24 Nov 2026).
- **Outside forecasts** (Western-style or unsourced) are checked and scored, never added to the rules: the earlier infographics model, and **Global Predictions** (a WhatsApp forecaster the user follows; tracked in `tools/global_predictions.py`).
- Silver has no sign in Brihat Samhita Ch.41. Model v1.0 reports "Insufficient data" for silver.
- Back every new rule or claim with a backtest using the method in `PROJECT_KNOWLEDGE.md` §6, and state results plainly, including when nothing works.
- Log every analysis in `build/pdfref/analysis_log.json` and regenerate the trackers.
- Work on branch `claude/affectionate-goldberg-fhy3zb`. Open a PR and merge only when the user asks.

## Commands

    python tools/refresh_all.py [--prices]                       # rebuild everything and run the tests
    python -m pytest -q tests/test_pdfref.py tests/test_shadbala.py
