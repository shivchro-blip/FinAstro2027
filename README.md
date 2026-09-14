# FinAstro 2027

A Vedic financial-astrology calendar for 2027, rebuilt from the structure of
*Parth Prophecies 2026* but computed rather than transcribed.

The 2026 source is a 437 KB single-file HTML with 233 tables. It is a serious
piece of work, but it carries the defects of a hand-maintained document. The same
event appears at two different times in two different tables: the 13-Jan-2026
Bhadra window opens at **02:00** in the Bhadra section (pp.120–124) and at
**3:59** in the January calendar (pg.270–271), with the same end time in both.
Recomputing it from the source's own stated rule — a Vishti karana is a 6°
step of Moon–Sun elongation — gives 02:00:06, so the section is right and the
calendar is 1h58m54s late. Alongside that: year typos (`17-Apr-25` inside a 2026
calendar), sheared table columns, a table of contents that disagrees with its own
headings, and one flagship claim — the Saturn–Neptune conjunction billed as the
event of the year — that is off by 12 hours 42 minutes.

This project's answer to all of that is a single rule: **nothing is typed twice.**
Every event is computed once into a canonical record, and the JSON, HTML and CSV
are all rendered from that record. Drift becomes structurally impossible.

## Status

Step 3 of the build, plus two late Step-3 extensions delivered during Step 4:
the **tithi and yoga boundary series** (`tithi_ingress`, `yoga_ingress`) and the
**sunrise and sunset series** (`sunrise`, `sunset`). The engine, its regression
harness, and the 2027 astronomy layer are in place. Interpretation is Step 4 and
has not started; the record schema in `finastro/events.py` has no field it could
occupy.

```
$ python3 tests/test_2026_regression.py
112/112 checks passed

$ python3 build_2027.py
4163 records -> build/astronomy_2027.json

$ python3 tests/test_2027_astronomy.py
123/123 checks passed

$ python3 tests/test_node_anchor_unit.py
12/12 checks passed

$ python3 tests/test_rule_layer.py
131/131 checks passed
```

The rule layer now carries **112 rules over 82 of the 141 catalogue-B sections**:
97 executable, 5 resolved on a supplied reading, 9 blocked with the missing input
named, and 1 ambiguous. 3,204 dated rows in the generated year. See
`build/STEP4_DECISIONS.md` §12 for the batch-by-batch record.

The build is deterministic: regenerating the year produces a byte-identical
file, so a real change shows up as a diff and nothing else does. Confirmed by
running the build twice and comparing:

```
sha256  f0ac8a2c01dd4dccbd714ba836c20e18a4667ea3665a499ce8325caff7ce69b6  build/astronomy_2027.json
```

That hash is over the Moshier ephemeris. It will change when the Swiss Ephemeris
data files are used, which is the point of that cross-check and not a regression.

A Step 3 closing report — record counts, every derived convention with its pass
rate, every convention carried without source evidence, every source defect, and
the open questions — is in `build/STEP3_REPORT.md`.

## The two panchang boundary series

A tithi is a 12-degree step of the Moon-Sun elongation and a yoga a 360/27 step
of their sum, both bisected to the second -- the method the source states for
its own Bhadra windows, on a different multiple of the same angle. Eight of the
Bhadra section's sixteen January boundaries are also tithi boundaries, and the
series reproduces all eight within **25 seconds**.

The two are not equally frame-free, and the difference is carried on every
record rather than assumed:

| | Angle | Ayanamsha | Measured |
| --- | --- | --- | --- |
| Tithi | Moon **-** Sun | cancels | identical to the second under Lahiri, KP, Raman, Fagan-Bradley and tropical |
| Yoga | Moon **+** Sun | enters twice | Lahiri 64 s, KP 22 min, Fagan-Bradley 3h17m, Raman 5h24m against the source's own printed edges |

Read tropically the yoga edges do not merely shift: they land on different
yogas altogether (4, 21 and 22 in place of 17, 18 and 27). So the yoga series is
certainty A on the same footing as a sign ingress -- exact given a locked,
evidenced ayanamsha -- and not on the "the ayanamsha cancels" footing the tithi
series has.

Both were validated against the source before any rule was wired to them:

| Fixture | Result |
| --- | --- |
| Bhadra pp.120-124, the 8 coincident boundaries | within 25 s |
| 36 printed tithi edges (B65, B73, B74, B75, B76, B109) | 35 within 68 s, 1 source defect |
| Kshay / Vriddhi tables (B66-B69), 28 rows | 28/28, every tithi named correctly, no extra |
| Vyatipata on weekdays (B96), 9 rows | 9/9, no omission and no extra |
| Yoga edges in B96 and B56 | 14 within 64 s |
| Amavasya ghadi (B106), 4 rows | 4/4 within 2 min, 1 source defect |

## Sunrise and sunset are a location property

The third event class, and the only one that is not a fact about the sky. A
tithi boundary is an angle reaching an exact multiple of 12°: it happens once
and the whole Earth shares the instant, which is why those records carry no
location. The Sun meets **one horizon at one place**. A sunrise record without a
location is not an under-specified Mumbai record — it is not a record of
anything — so the schema refuses it:

```python
LOCATION_REQUIRED = ("sunrise", "sunset")   # finastro/events.py
```

Both venues are generated, 427 civil days each, and neither is a fallback for
the other. The source computes its own rise and set for Mumbai alone and says
so; that is a fact about the source, not a licence to let a New York reader
infer the other from an offset. There is no offset: the two sunrises are ~10½
hours apart and the gap moves all year.

**Certainty B, not A, and the record says why.** A rise depends on which part of
the disc touches the horizon, on refraction, and on the horizon's height. Every
record carries `rise_set_convention=disc_center_no_refraction`, `disc=center`,
`refraction=none` and the lat/lon/alt it was taken from.

The document prints exactly four Mumbai times, to the minute, inside the Bhadra
section's prose rather than in any table. The engine reproduces all four within
**4m43s** — and they do **not** decide the convention, which is measured rather
than waved at:

| Convention | Worst | Mean |
| --- | --- | --- |
| disc centre, no refraction (**used**) | 283 s | 194 s |
| disc centre, with refraction | 114 s | 80 s |
| upper limb, no refraction | 208 s | 127 s |
| upper limb, with refraction | 168 s | 59 s |

Every one has errors of both signs, so none is a fixed offset from the source's.
Four times printed to the minute cannot separate conventions whose spread is 4½
minutes. The convention used is the one the kalāṃśa calibration was fitted
under, because kalāṃśa is the gap between a planet's rise and the Sun's rise and
a gap measured between two different conventions is not a gap. A harness check
pins the two strings together so they cannot drift.

**One row of the document decides it independently, and is recorded as worth
exactly that.** B66 prints 23-Feb-26 Saptami as a Kshay tithi. That Saptami ends
24-Feb 07:02:37; Mumbai sunrise that morning is 07:05:07 without refraction and
07:02:29 with it. Without refraction the tithi holds no sunrise and is Kshay on
23-Feb — the printed row. With refraction it is not, and the next tithi is Kshay
on 24-Feb instead. An **eight-second** margin, pointing the same way as the
kalāṃśa calibration.

That row is also the answer to "how far does the B grade travel". Twenty-seven
of the 28 Kshay/Vriddhi rows, and all 25 Pradosh rows, are identical under all
four conventions. The definition-sensitivity is real and it attaches to the
*published time of a rise*, not to the rules conditioned on one.

**Emitting the series found a defect the old checks could not see.**
`panchang.sunrise` anchored its search at local noon and so returned the *next*
day's rise — a true instant under the wrong date. The 28-row Kshay/Vriddhi
reproduction could not catch it: it only counts sunrises inside a tithi, and a
set of instants shifted by a day covers the same interval. It took emitting them
as dated records. The search is now anchored at the venue's own civil midnight,
and two checks keep it there.

## The rule layer has two kinds of location-awareness, not one

A **weekday** rule has one sky-side condition and two calendars: "Anuradha on
Sunday" asks the same question of the sky at both venues and only the date
differs, so the weekday is applied after a span becomes a day at a venue.

A **sunrise** rule has two conditions. Whether a tithi is Kshay — whether any
sunrise falls inside it — is a different question in Mumbai and in New York, and
can come out yes in one and no in the other with no calendar involved. So
`Rule.per_location` calls the condition once per venue, and a rule declaring a
`horizon/` input is *required* to set it; the constructor raises otherwise.

The difference is not theoretical. Across the generated span, Mumbai has 10
bright-fortnight Kshay tithis and New York 11, with **none in common**: a Kshay
tithi is one whose ~21-hour span falls entirely between two consecutive
sunrises, so two venues half a world apart agreeing would be a coincidence.

## The conventions are derived, not assumed

Every convention in `config/conventions.yaml` was either confirmed by the project
owner or recovered empirically from the 2026 source. The interesting ones:

**Ayanamsha — Lahiri.** The source puts the Sun entering Capricorn at 14-Jan-2026
15:08 IST. Lahiri computes 15:07, KP computes 12:50, Raman computes the previous
day. The choice is not a matter of taste; it is measurable to the minute.

**Node — mean.** Rahu enters Capricorn at 05-Dec-2026 21:52 in the source. The
mean node gives 22:32; the true node gives 25-Nov, ten days earlier.

**Weekday rules — civil-day overlap.** Four competing conventions were tested by
reproducing 13 weekday-rule tables (75 dated rows):

| Convention | Rows reproduced |
| --- | --- |
| Tithi/nakshatra prevailing at sunrise | 51 / 75 |
| **Any overlap with the local civil day** | **74 / 75** |
| Sunrise-to-sunrise day | 73 / 75 |
| Market-session overlap only | 64 / 75 |

Confirmed independently by the source's own From/Till annotations, which land on
civil-day span boundaries to the minute.

Every weekday-conditioned per-date table in the document is now transcribed into
the harness — 12 families, 64 printed rows — and the convention reproduces
**63/63** of them. The 64th, `Anuradha on Sunday` 28-Jun-26, is a source defect:
the Moon is in Jyeshtha all that day, so no day convention could produce the row.
No rule family systematically fails.

The convention also emits **27 dates the source does not print**, spread across 8
of the 12 families and concentrated in the two Ashtami tables. These are left
exactly as they are: they are the source's omissions unless evidence says
otherwise, and neither duration nor prevailing-at-sunrise discriminates them from
the rows the source does print. The margin is recorded in
`weekday_rule.extras`, not tuned away.

**Combustion — classical kalāṃśa.** Three hypotheses were tested against all 23
combust/rise dates:

| Hypothesis | Verdict |
| --- | --- |
| Fixed ecliptic-elongation orbs | Rejected — Mercury's events span 10.0°–15.4° |
| Modern heliacal visibility (`swe.heliacal_ut`) | Rejected — Venus off by 9–10 days |
| Classical kalāṃśa | Confirmed |

Kalāṃśa is the gap between planet and Sun at the horizon, expressed in degrees of
time. Measured that way the source's dates give near-constant values per planet
(Jupiter 9.42 and 9.44; Saturn 12.84 and 12.63), each sitting a uniform ~2.3°
below the classical table — a rise/set convention offset, not a different method.
The thresholds are calibrated from the source so the output reproduces it rather
than approximating it.

**Total Days — `dd + mm == yy`.** Reproduces 12/12 with no extras. Arithmetic, so
certainty A.

**Dignity — witnessed for five of the seven planets, across two charts.** The
source labels dignity inline in its journey and navamsa tables, and every label it
prints was swept out of the file and checked against the config block: Mars,
Mercury, Venus and Jupiter have all four states labelled, Saturn only
`Capricorn (Own)`. Nothing outside the Parashari table is labelled anywhere, so the
source neither contradicts the scheme nor extends it.

The labels do not all come from the same chart, and that matters more than it
looks. Mars, Mercury and Venus are witnessed in **rashi (D1)** journey tables;
Jupiter and Saturn are witnessed in **navamsa (D9)** tables. The two frames give
different answers for the same planet at the same instant, so the block is a
single Parashari table assembled from two different readings of the sky:

| Planet | Frame | Section |
| --- | --- | --- |
| Mars | rashi (D1) | *Journey of Mars p.5* |
| Mercury | rashi (D1) | *Journey of Mercury p.8* |
| Venus | rashi (D1) | *Journey of Venus p.12-13* |
| Jupiter | navamsa (D9) | *Jupiter in Navmansh (D9) p.22* |
| Saturn | navamsa (D9) | *Saturn in Navmansh (D9) p.25* |

Saturn settles which frame the D9 tables are using. *Journey of Saturn p.23* says
"Saturn remains in Pisces throughout the year", and Pisces carries Saturn no
dignity at all — yet *Saturn in Navmansh (D9) p.25* prints `Capricorn (Own)`. Read
in the rashi frame that row would be blank. Jupiter agrees: its D9 table prints
`Sagittarius (Own, Trine)`, `Capricorn (Debilitated)` and `Pisces (Own)` while its
rashi sign is Cancer throughout, which would have printed `Exalted` for all three.
Four of the five D9 rows discriminate; the fifth is Jupiter's Cancer window, which
the source itself labels Vargottam, so rashi and navamsa agree there by
construction and it is evidence for neither.

So the engine emits dignity per chart and under a distinct name — `dignity` from
`sign`, `navamsa_dignity` from `navamsa` — and never collapses them into one
field. The one omission the config records, Saturn in Libra, is likewise a D9 row,
and is checked in the D9 frame: against the rashi sign it could never fire, because
Saturn's rashi sign never reaches Libra in either year.

Two absences are recorded rather than papered over. The Sun passes through all
twelve signs in *Sun Transgression (Sankranti) p.2* — Aries, Leo and Libra among
them — and carries **no dignity label anywhere in the document**; that table has no
dignity column at all. The Moon gets no journey or navamsa table, so it never had
the chance. Both are carried from Parashari and are untested by the source, which
`dignity.source_witness` now says in the config instead of leaving it to be assumed.

Saturn's D9 pass through Libra (*Saturn in Navmansh (D9) p.25*, 21-Mar-26 15:00 to
17-Apr-26 14:57) is printed bare while the same table labels `Capricorn (Own)`
twice — a real omission, which the engine corrects and flags rather than copies.

## Precision is measured, not asserted

`precision_days` in the config is the calibration scatter divided by the body's
daily rate of change. Mercury gets ±2 days because 13 calibration points span
1.66° at roughly 0.45°/day. Mars gets ±2 days because there are only two
calibration points. Jupiter gets ±1 because its two points agree to 0.02°.

Stations are checked to 5 minutes rather than 1, because at a station the
longitude is stationary to second order and a sub-arcsecond ephemeris difference
moves the clock time by minutes. The source's own slow-planet stations drift by
up to an hour for exactly this reason.

## Layout

```
config/conventions.yaml        every locked decision, with its evidence
finastro/config.py             loads the above
finastro/ephem.py              sidereal positions, ingresses, stations, eclipses
finastro/timezones.py          IST primary, Eastern secondary, DST via IANA
finastro/panchang.py           tithi/nakshatra/yoga/karana, sunrise/sunset,
                               the weekday-rule engine
finastro/combustion.py         kalāṃśa asta/udaya
finastro/events.py             the canonical record; layers kept separate
build_2027.py                  generates the 2027 astronomy layer
tests/test_2026_regression.py  locks the conventions against the source
tests/test_2027_astronomy.py   sanity-checks the generated 2027 output
tests/test_node_anchor_unit.py the node-anchor branch the real span can't reach
build/astronomy_2027.json      4163 records, astronomy only
build/astronomy_2027_summary.txt  counts per class and the backend used
```

## Running it

```bash
pip install -r requirements.txt
python3 tests/test_2026_regression.py
```

### Ephemeris backend

The code prefers real Swiss Ephemeris data files and falls back to the built-in
Moshier ephemeris, reporting which it used. Moshier is accurate to well under an
arcsecond for the Sun, Moon and planets across 1900–2100, so every date and
minute produced so far is sound. For the production run, download the SE files
and point at them:

```bash
export SE_EPHE_PATH=/path/to/ephe
```

Then diff the output against the Moshier run. Given what the source document got
wrong, a final cross-check costs little and is worth doing.

## Time handling

IST (UTC+05:30, no DST) is primary. Eastern is resolved through the IANA zone
`America/New_York`, so the EDT/EST label and the −9:30 or −10:30 gap from IST are
always correct without hardcoding the 2027 switch dates of 14-Mar and 07-Nov.

Where the Eastern calendar date differs, both dates are shown and the record
carries `day_shift = -1`. Window starts and ends are converted independently, so
a window spanning a DST change correctly shows two different Eastern offsets.

Mumbai and New York are evaluated **separately** for sunrise- and weekday-
dependent rules, and emit their own rows. This is not cosmetic: across 13 rule
families in 2026 the two locations produce 103 and 119 qualifying dates with only
90 in common — and for the Kshay and Vriddhi families, which turn on where a
sunrise falls rather than on which day it lands, the two venues share no tithi
at all.

## Epistemics

Astronomy and interpretation are kept in separate layers of the record and never
merged into one field. Astronomical data carries a certainty grade (A computed
exact, B definition-sensitive, C dependent on an undocumented source rule);
interpretation carries a claim tag (Classical, Framework, Observed, Historical,
Verify) and a confidence that starts at `untested` and is only raised by a
pre-registered backtest.

The 2026 probability labels are preserved as `source_probability` — they are
what the source asserted, not a calibrated result, and are not treated as one.
The field is an annotation, not a computable column: 44 labels exist, 19 survive
a three-part transfer test, and they reach roughly 26 of thousands of 2027 rows,
so nothing filters, weights or aggregates on it. Where the source gave one rule
two different labels — which it does in every case where it repeats a rule text
verbatim — the set is emitted rather than a chosen value, flagged
`source_probability_disputed`. `source_probability` never feeds `confidence`.
See `source_probability` in `config/conventions.yaml` and
`build/STEP4_DECISIONS.md`.

Financial astrology is a speculative interpretive framework. Nothing this
project generates is investment advice.

## Known gaps

Carried in `open_questions` in the config: **speed-class thresholds** — resolved
for the inner planets, still open for the slow ones, see below — the 2–7 day lag
on the source's Mercury latitude rows, aspect orb policy, confirmation of
Purnimanta month reckoning, sector mapping, and sign-off on the label scheme.

**The speed-class thresholds calibrate for the inner planets and not the slow
ones.** An earlier report that no threshold exists was a **method artefact** and
is retracted in `build/STEP4_DECISIONS.md` §12.8: it read the speed *at* the
printed boundary dates instead of computing crossing instants, and near a speed
maximum the whole above-threshold window is only a few days wide, so the samples
"overlapped" whether or not a threshold existed. Done the kalāṃśā way — propose a
threshold, compute the crossings, score them against the printed dates — the
thresholds are **Mercury 1.7449**, **Venus 1.2240** and **Mars 0.6583** deg/day.
They are absolute and planet-specific, not fractions of each planet's maximum
(that reading is rejected: it forces a Fast window's two crossings to be
equidistant from the speed maximum, and Mars's are not).

Jupiter and Saturn have **no** threshold, and the reason is a doctrine rather
than a failure: the source carries **B30 "Demoted and Shadow Speed of Saturn"
p.26**, which defines its interval by **longitude** (Saturn at 20°31′ of Pisces,
crossed retrograde on 27-Jul-2026 and direct again on 15-Mar-2027 — both
reproduced to the arcminute by the engine) and supplies no speed level. So those
two stay blocked with a **slow-planet speed doctrine** named as the missing
input.

**Vedha direction: 109/111, and both exceptions are Saturn.** The rule —
Fast/Atichari→Left, Normal→Front, Retrograde→Right — holds **without exception**
on Mars (21/21), Mercury (45/45), Venus (30/30) and Jupiter (7/7); only Saturn
(B136) has two rows against it, and those two rows use inconsistent offsets even
with each other. It stays a correlation because two printed rows do contradict
it. **Atichari** is the nakshatra-residency frame's name for the period the speed
frame calls **Fast**: every Atichari row begins and ends on a nakshatra ingress.
The Vedha families are unblocked for Mercury, Venus and Mars — but nothing has
been ported, because the astronomy layer emits no **speed-crossing** series, so a
rule cannot build Fast/Normal spans from it. That is new Step-3 work of the same
kind as the tithi, yoga and sunrise series.

**Shar is settled, and it is the ecliptic latitude and not the declination.**
B118 and B119 print North/South periods; the latitude sign reproduces B119's 27
printed 2026 ends **26 of 27** within 1.5 days, the declination sign reproduces
**0 of 27**, and B118's Mars prints one change where the latitude crosses once
(0.76 d) while the declination crosses 104 days away. Grade B, because latitude
has no ingress series and a boundary is known only to the gap between records —
negligible for the Moon, months for Pluto.

**Atichari is not a speed class name at all** — it is the nakshatra-residency
frame's label for the same period the speed frame calls **Fast**. Every Atichari
row in B132/B133/B134 begins and ends on a nakshatra ingress (Venus's eleven run
to 12-Apr-26 14:22, exactly when she leaves Revati), so the two tables are one
period described in two frames rather than two names for one threshold.

**B81 is labelled for the wrong planet, and the tables cannot show it.** "Saturn
and Mercury Both Retrograde" prints a 2026 window during which Saturn and Mercury
are never both retrograde — the printed row is **Venus's** retrograde window to
within four minutes, and the true Saturn∩Mercury window is the row B83 prints.
Because in 2026 both Venus's and Saturn's retrograde stretches happen to contain
Mercury's, the error is invisible without an independent computation. Ported as
the exact condition with the row flagged; nothing widened. Three further source
defects are recorded in §12.7 (B82's carry-in-only window, B114's unmatched
printed end, B115's narrower printed table).

Deliberately excluded: the rainfall formula (dropped), Sankranti muhurta
(deferred until the 15/30/45 division rule is available). The "Big Volatile" list
is flagged C — all 51 source dates carry a real configuration, but the list is
over-determined and the source's weighting is not recoverable, so reconstructions
are emitted as candidates and never as fact. It is ported as a **recorded
absence** with its C flag and `source_selection_rule` named as the missing input,
not reconstructed.
