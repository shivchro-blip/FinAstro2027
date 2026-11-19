# Build Specification — Kindle_Ch06A_Bhadra.html

Extraction basis: `Kindle_Ch06_Moon_Traders_Clock.html` (primary reference — Ch06A sits
immediately after it), cross-checked against `Kindle_Ch02_Two_Skies.html` and
`Kindle_Ch07_Dignity_Strength_Speed.html`. All three files live in this directory
(`C:\Shiva\FinAstro_Guide\raw\`). All quotes below are verbatim (exact whitespace,
attribute order, entity/character choice) unless explicitly marked as paraphrase.

Verified by: reading each file in full (Ch06: 471 lines / 50,490 bytes; Ch02: 418
lines / 45,505 bytes; Ch07: 397 lines / 47,935 bytes); a scripted diff of the three
`<style>` blocks; scripted character/entity frequency counts; and targeted greps for
`scope=`, `<a href`, `class="honest"`, `class="callout…"`, and stray `&`.

---

## 1. FILE ENVELOPE

### Doctype, `<html>`, encoding, line endings

```html
<!DOCTYPE html>
<html lang="en">
```

Identical, byte-for-byte, in Ch06, Ch02, and Ch07.

**Encoding:** UTF-8, no BOM (verified: first three bytes are `3c 21 44` — `<!D`, not
`ef bb bf`).

**Line endings:** LF only (`\n`). Verified on Ch06: 470 `\n` bytes, 0 `\r\n`
sequences.

**File ends:** with a single trailing newline after `</html>` — the last 20 bytes of
Ch06 are `p>\n\n</body>\n</html>\n` (a blank line separates the closing `<p>` from
`</body>`).

### `<head>` contents

Ch06 and Ch02 agree on element order — `meta charset` → `meta viewport` → `title` →
`link` (Google Fonts):

```html
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>The Celestial Ledger — Chapter 6: The Moon — The Trader's Clock</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
```

**Ch07 disagrees on order** — it puts `<title>` and `<link>` *before* the two
`<meta>` tags:

```html
<head>
<title>The Celestial Ledger — Chapter 7: Dignity, Strength &amp; Speed</title>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<style>
```

**Verdict where they disagree:** majority convention (Ch06 + Ch02, 2 of 3) is
`charset` → `viewport` → `title` → `link`. Treat Ch07's reordering as a **Ch07-local
quirk** — follow Ch06's order for Ch06A.

The `<link>` href is byte-identical across all three files, including two literal,
un-escaped `&` characters inside the query string (`&family=Inter…` and
`&display=swap`) — see Section 9, this is a book-wide (not Ch06-local) minor markup
defect, tolerated by browsers but not spec-valid. Reproduce the href exactly as-is
for consistency with every other chapter file rather than "fixing" it.

**Title pattern:** `The Celestial Ledger — Chapter {N}: {Chapter Title}` (em dash
literal, U+2014, in the `<title>` of all three files — including Ch07, whose body
otherwise uses HTML entities for dashes/quotes; see Section 9). For Ch06A, since it
is an interstitial chapter rather than a numbered one, the exact title-tag text is
**UNDETERMINED from the existing files** — there is no precedent anywhere in this
directory for a lettered sub-chapter (checked: no `Ch0\dA`/`Ch0\dB` filename or
title exists among the 21 numbered chapters + conclusion + appendices). Decide the
title wording with the user; do not invent a "Chapter 6A" numbering convention
unsupported by any existing file.

### Opening/closing `<body>`

```html
<body>

<div class="hero">
```

…and at the end:

```html
<p class="bridge">End of Chapter 6. The clock is set, and its limits are honest.<br/>Next: <strong>Chapter 7 — "Dignity, Strength &amp; Speed,"</strong> which makes precise the "state" of a planet that Chapters 4–6 kept invoking — exaltation and debilitation, retrogradation, combustion, and stations — and why a planet's <em>condition</em>, not just its identity, drives its market effect.</p>

</body>
</html>
```

(Both Ch02 and Ch07 follow the identical `</p>` → blank line → `</body>` → `</html>`
shape.)

### Filename convention

Pattern observed across all 25 files in this directory:

```
Kindle_Ch{NN}_{TitleSlug}.html            e.g. Kindle_Ch06_Moon_Traders_Clock.html
Kindle_Ch{NN}_{TitleSlug}_v2.html         e.g. Kindle_Ch00_Building_Blocks_v2.html, Kindle_Ch04_Significators_v2.html
Kindle_Appendices_{A-C|D-F}.html
Kindle_Conclusion_Unified_Model.html
```

`{NN}` is always two digits, zero-padded (`00`…`20`). `{TitleSlug}` is a short,
Title-Case-with-underscores fragment of the chapter's title (not the full title —
e.g. Ch06's title is "The Moon — The Trader's Clock" but its slug is
`Moon_Traders_Clock`; Ch07's title is "Dignity, Strength & Speed" and its slug is
`Dignity_Strength_Speed`, dropping the ampersand and comma).

Per the user's own naming, **`Kindle_Ch06A_Bhadra.html`** fits this pattern's
letters/digits/underscore shape, but the `06A` chapter-number-plus-letter form has
**no precedent** in this directory. This is noted, not corrected — the filename was
specified by the requester, not inferred.

---

## 2. STYLESHEET

### Ch06's entire `<style>` block, verbatim

```css
:root{
  --paper:#fbf9f4; --paper2:#f4efe4; --card:#ffffff; --ink:#26211c; --ink-soft:#4f463c; --ink-faint:#857a6c;
  --line:#e6dfce; --line-soft:#efe9dc;
  --gold:#9a7113; --gold-soft:#fbf2da; --gold-line:#e7cf94;
  --teal:#0c7d68; --teal-soft:#e3f3ef;
  --coral:#b23a2e; --coral-soft:#f8e9e6;
  --violet:#6244a8; --violet-soft:#efeafa;
  --green:#2f7d4f; --green-soft:#e6f3ea;
  --blue:#1f6aa6; --blue-soft:#e7f0f8;
  --slate:#566273; --slate-soft:#eaeef3;
  --serif:'Playfair Display',Georgia,'Times New Roman',serif;
  --body:Georgia,'Iowan Old Style','Palatino Linotype',serif;
  --sans:'Inter',system-ui,-apple-system,sans-serif;
  --r:10px; --r-sm:7px;
}
*{box-sizing:border-box;margin:0;padding:0;}
html{ -webkit-text-size-adjust:100%; }
body{ background:var(--paper); color:var(--ink); font-family:var(--body); font-size:18px; line-height:1.72; max-width:780px; margin:0 auto; padding:30px 26px 90px; }
p{ margin:0 0 14px; } strong{ color:var(--ink); font-weight:600; } em{ font-style:italic; }

.hero{ text-align:center; padding:22px 0 30px; border-bottom:2px solid var(--gold-line); margin-bottom:34px; }
.hero .kicker{ font-family:var(--sans); font-size:11px; font-weight:600; letter-spacing:.26em; text-transform:uppercase; color:var(--gold); }
.hero h1{ font-family:var(--serif); font-weight:900; font-size:40px; line-height:1.12; margin:14px 0 0; }
.hero h1 em{ color:var(--gold); font-style:italic; }
.hero .sub{ font-style:italic; color:var(--ink-soft); font-size:17px; max-width:580px; margin:16px auto 0; }
.hero .ornament{ color:var(--gold); letter-spacing:.5em; margin-top:18px; font-size:14px; }

.lesson{ margin:0 0 50px; }
.lesson-head{ display:flex; align-items:baseline; gap:12px; border-bottom:1px solid var(--line); padding-bottom:8px; margin-bottom:18px; }
.lesson-no{ font-family:var(--sans); font-size:12px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; color:var(--gold); white-space:nowrap; }
.lesson-title{ font-family:var(--serif); font-weight:700; font-size:25px; line-height:1.2; }
.lesson-title em{ color:var(--gold); font-style:italic; }
h3.sec{ font-family:var(--serif); font-style:italic; font-weight:600; font-size:21px; color:var(--gold); margin:28px 0 10px; }
h4.lab{ font-family:var(--sans); font-size:11px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; color:var(--ink-faint); margin:22px 0 9px; }

.callout{ border-left:4px solid var(--gold); background:var(--gold-soft); border-radius:0 var(--r-sm) var(--r-sm) 0; padding:14px 18px; margin:18px 0; font-size:16.5px; line-height:1.62; }
.callout .ct{ display:block; font-family:var(--sans); font-size:11px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:5px; color:var(--gold); }
.callout.teal{ border-color:var(--teal); background:var(--teal-soft);} .callout.teal .ct{ color:var(--teal);}
.callout.coral{ border-color:var(--coral); background:var(--coral-soft);} .callout.coral .ct{ color:var(--coral);}
.callout.violet{ border-color:var(--violet); background:var(--violet-soft);} .callout.violet .ct{ color:var(--violet);}
.callout.green{ border-color:var(--green); background:var(--green-soft);} .callout.green .ct{ color:var(--green);}
.callout.slate{ border-color:var(--slate); background:var(--slate-soft);} .callout.slate .ct{ color:var(--slate);}
.honest{ border-left:4px solid var(--violet); background:var(--violet-soft); border-radius:0 var(--r-sm) var(--r-sm) 0; padding:14px 18px; margin:18px 0; font-size:16px; }
.honest .ct{ display:block; font-family:var(--sans); font-size:11px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:5px; color:var(--violet); }

.keyrule{ text-align:center; font-family:var(--serif); font-style:italic; font-size:20px; line-height:1.5; color:var(--gold); border-top:1px solid var(--gold-line); border-bottom:1px solid var(--gold-line); padding:18px 14px; margin:22px 0; }
.keyrule .small{ display:block; font-family:var(--sans); font-style:normal; font-size:10px; font-weight:600; letter-spacing:.18em; text-transform:uppercase; color:var(--ink-faint); margin-bottom:8px; }
.keyrule b{ font-style:normal; color:var(--ink); }

.tag{ display:inline-block; font-family:var(--sans); font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:1px 7px; border-radius:4px; vertical-align:middle; }
.tag.cl{ background:var(--blue-soft); color:var(--blue); } .tag.fw{ background:var(--gold-soft); color:var(--gold); } .tag.vf{ background:var(--violet-soft); color:var(--violet); }
.tag.ob{ background:var(--teal-soft); color:var(--teal); } .tag.as{ background:var(--slate-soft); color:var(--slate); }

.cards{ display:flex; flex-wrap:wrap; gap:12px; margin:16px 0; }
.card{ flex:1 1 220px; background:var(--card); border:1px solid var(--line); border-top:3px solid var(--gold); border-radius:var(--r-sm); padding:14px 16px; }
.card.up{ border-top-color:var(--green);} .card.down{ border-top-color:var(--coral);} .card.teal{ border-top-color:var(--teal);} .card.violet{ border-top-color:var(--violet);} .card.slate{ border-top-color:var(--slate);}
.card .ic{ font-size:24px; line-height:1; } .card .ti{ font-family:var(--serif); font-weight:700; font-size:18px; margin:6px 0 2px; } .card .ti em{ color:var(--gold); font-style:italic; font-weight:400; font-size:14px; }
.card .mt{ font-family:var(--sans); font-size:11px; font-weight:600; letter-spacing:.05em; text-transform:uppercase; color:var(--ink-faint); margin-bottom:6px; } .card p{ font-size:15px; line-height:1.55; margin:0; color:var(--ink-soft); }

/* ===== DETAILED PLANET PROFILE ===== */
.planet{ background:var(--card); border:1px solid var(--line); border-radius:var(--r); margin:18px 0; overflow:hidden; box-shadow:0 1px 3px rgba(0,0,0,.04); }
.planet-head{ display:flex; align-items:center; gap:16px; padding:16px 20px; background:linear-gradient(180deg,var(--gold-soft),#fff); border-bottom:1px solid var(--line); }
.planet-head.up{ background:linear-gradient(180deg,var(--green-soft),#fff);} .planet-head.down{ background:linear-gradient(180deg,var(--coral-soft),#fff);} .planet-head.violet{ background:linear-gradient(180deg,var(--violet-soft),#fff);} .planet-head.neutral{ background:linear-gradient(180deg,var(--blue-soft),#fff);}
.pl-glyph{ font-size:38px; line-height:1; color:var(--gold); flex-shrink:0; width:46px; text-align:center; }
.pl-id{ flex:1; }
.pl-name{ font-family:var(--serif); font-weight:700; font-size:23px; line-height:1.1; }
.pl-name em{ color:var(--gold); font-style:italic; font-weight:400; font-size:16px; }
.pl-arch{ font-family:var(--sans); font-size:12.5px; color:var(--ink-faint); margin-top:3px; letter-spacing:.02em; }
.pl-class{ font-family:var(--sans); font-size:10px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:4px 10px; border-radius:999px; white-space:nowrap; align-self:flex-start; }
.pl-class.ben{ background:var(--green-soft); color:var(--green); } .pl-class.mal{ background:var(--coral-soft); color:var(--coral); } .pl-class.neu{ background:var(--blue-soft); color:var(--blue); }
.planet-body{ padding:16px 20px 18px; }
.pl-sketch{ font-size:16.5px; margin-bottom:12px; }
.pl-data{ display:grid; grid-template-columns:1fr 1fr; gap:7px 22px; margin:12px 0; font-family:var(--sans); font-size:13.5px; line-height:1.5; }
.pl-data .row{ border-bottom:1px solid var(--line-soft); padding-bottom:6px; color:var(--ink-soft); }
.pl-data .full{ grid-column:1 / -1; }
.pl-k{ display:block; font-size:10px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--gold); margin-bottom:1px; }
.pl-rules{ background:var(--gold-soft); border-radius:var(--r-sm); padding:9px 13px; font-family:var(--sans); font-size:13.5px; margin-top:8px; }
.pl-rules .pl-k{ color:var(--gold); }
.pl-market{ font-size:15px; font-style:italic; color:var(--ink-soft); border-left:3px solid var(--gold-line); padding-left:12px; margin-top:11px; }
@media (max-width:600px){ .pl-data{ grid-template-columns:1fr; } }

.tw{ overflow-x:auto; border:1px solid var(--line); border-radius:var(--r-sm); margin:16px 0; }
table{ width:100%; border-collapse:collapse; font-family:var(--sans); }
thead tr{ background:var(--gold-soft); }
th{ font-size:10.5px; font-weight:700; letter-spacing:.07em; text-transform:uppercase; color:var(--gold); text-align:left; padding:9px 11px; white-space:nowrap; }
td{ font-size:13px; padding:8px 11px; border-top:1px solid var(--line-soft); vertical-align:top; color:var(--ink-soft); }
td.g{ color:var(--gold); font-weight:600; white-space:nowrap; }
td.up{ color:var(--green); font-weight:600;} td.dn{ color:var(--coral); font-weight:600;}
tbody tr:nth-child(even){ background:#fcfaf5; }

.qa{ border:1px solid var(--line); border-radius:var(--r-sm); overflow:hidden; margin:20px 0; }
.qa-h{ background:var(--paper2); padding:9px 15px; font-family:var(--sans); font-size:11px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--gold); border-bottom:1px solid var(--line); }
.qa-i{ padding:12px 15px; border-bottom:1px solid var(--line-soft); } .qa-i:last-child{ border-bottom:none; }
.qa-q{ font-size:16px; } .qa-q b{ color:var(--gold); font-family:var(--sans); font-size:12px; font-weight:700; margin-right:8px; }
.qa-a{ font-size:16px; color:var(--ink-soft); margin-top:5px; } .qa-a b{ color:var(--teal); font-family:var(--sans); font-size:12px; font-weight:700; margin-right:8px; }

.recap{ display:flex; align-items:center; gap:18px; background:var(--gold-soft); border:1px solid var(--gold-line); border-radius:var(--r-sm); padding:16px 20px; margin:20px 0; }
.recap .n{ font-family:var(--serif); font-weight:900; font-size:38px; color:var(--gold); line-height:1; flex-shrink:0; }
.recap .l{ font-family:var(--sans); font-size:10px; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:var(--ink-faint); }
.recap .t{ font-family:var(--serif); font-weight:700; font-size:18px; margin:2px 0; } .recap .d{ font-size:14px; color:var(--ink-soft); }

.ladder{ counter-reset:rk; list-style:none; padding:0; margin:14px 0; }
.ladder li{ counter-increment:rk; display:flex; gap:14px; align-items:flex-start; padding:9px 0; border-bottom:1px solid var(--line-soft); font-size:15.5px; }
.ladder li:last-child{ border-bottom:none; }
.ladder li::before{ content:counter(rk); flex-shrink:0; width:26px; height:26px; background:var(--gold); color:#fff; border-radius:50%; font-family:var(--sans); font-weight:700; font-size:13px; display:flex; align-items:center; justify-content:center; }
.ladder b{ color:var(--ink); }

.checklist{ list-style:none; padding:0; margin:14px 0; }
.checklist li{ display:flex; gap:13px; align-items:flex-start; padding:11px 0; border-bottom:1px solid var(--line-soft); font-size:16px; }
.checklist li:last-child{ border-bottom:none; }
.checklist .box{ flex-shrink:0; width:22px; height:22px; border:2px solid var(--gold); border-radius:5px; margin-top:2px; }
.checklist b{ color:var(--ink); }

.takeaways{ counter-reset:tk; list-style:none; padding:0; margin:14px 0; }
.takeaways li{ counter-increment:tk; position:relative; padding:10px 0 10px 46px; border-bottom:1px solid var(--line-soft); font-size:16.5px; }
.takeaways li:last-child{ border-bottom:none; }
.takeaways li::before{ content:counter(tk); position:absolute; left:0; top:9px; width:30px; height:30px; border:1.5px solid var(--gold); color:var(--gold); border-radius:50%; font-family:var(--serif); font-weight:700; font-size:16px; display:flex; align-items:center; justify-content:center; }

.gloss{ background:var(--card); border:1px solid var(--line); border-radius:var(--r-sm); padding:6px 18px; margin:16px 0; }
.gloss dt{ font-family:var(--serif); font-weight:700; font-size:16px; color:var(--gold); margin:12px 0 1px; }
.gloss dd{ margin:0 0 4px; font-size:15.5px; color:var(--ink-soft); }

.bridge{ text-align:center; font-style:italic; color:var(--ink-faint); font-size:15px; border-top:1px solid var(--line); padding-top:22px; margin-top:34px; }
hr.soft{ border:none; border-top:1px solid var(--line); margin:30px 0; }
@media (max-width:600px){ body{font-size:17px;padding:20px 16px 70px;} .hero h1{font-size:31px;} .lesson-title{font-size:21px;} }
```

### Diff against Ch02 and Ch07 (scripted line diff, not eyeballed)

**CSS custom properties (`--var`) — Ch06's full `:root` values**, with the two
that vary between files:

| Variable | Ch06 | Ch02 | Ch07 |
|---|---|---|---|
| `--slate` | `#566273` | `#445a6e` | `#566273` (matches Ch06) |
| `--slate-soft` | `#eaeef3` | `#e8edf2` | `#eef1f5` |

All other custom properties (`--paper`, `--paper2`, `--card`, `--ink*`, `--line*`,
`--gold*`, `--teal*`, `--coral*`, `--violet*`, `--green*`, `--blue*`, `--serif`,
`--body`, `--sans`, `--r`, `--r-sm`) are **byte-identical** across all three files.
`--slate`/`--slate-soft` are evidently re-picked per chapter with no fixed value —
treat as **safe to reuse Ch06's exact values** for Ch06A, since it is the adjacent
file and there is no evidence of a single "correct" book-wide slate.

**Rules present in Ch06 but absent from both Ch02 and Ch07** (a true Ch06-local
addition, not shared even with its immediate successor Ch07):

```css
/* ===== DETAILED PLANET PROFILE ===== */
.planet{ ... }
.planet-head{ ... }
.planet-head.up{...} .planet-head.down{...} .planet-head.violet{...} .planet-head.neutral{...}
.pl-glyph{ ... }
.pl-id{ ... }
.pl-name{ ... }
.pl-name em{ ... }
.pl-arch{ ... }
.pl-class{ ... }
.pl-class.ben{...} .pl-class.mal{...} .pl-class.neu{...}
.planet-body{ ... }
.pl-sketch{ ... }
.pl-data{ ... }
.pl-data .row{ ... }
.pl-data .full{ ... }
.pl-k{ ... }
.pl-rules{ ... }
.pl-rules .pl-k{ ... }
.pl-market{ ... }
@media (max-width:600px){ .pl-data{ grid-template-columns:1fr; } }
```

This entire ~22-line block (full CSS quoted above) is the "planet profile card"
component used twice in Ch06's markup (the Moon profile in Lesson 6.1, and the
"Sky Today" worked example in Lesson 6.4). **Neither Ch02 nor Ch07 defines it at
all** — it is not merely unused elsewhere, the CSS rules themselves don't exist in
those two files' `<style>` blocks. If Ch06A needs a planet/nakshatra-profile card
(plausible for a Bhadra-karana chapter that may profile a nakshatra or a
yoga/karana in the same visual language), copy this block in from Ch06 — do not
expect to find it by looking at Ch07, the chapter immediately after.

**Rules present in Ch02 or Ch07 but absent from Ch06:**

- `.tag.ob` (the "Observed" epistemic tag) is **absent from Ch02's CSS entirely** —
  Ch02 defines only four tag classes (`cl`, `fw`, `vf`, `as`), not five. Ch06 and
  Ch07 both define all five (`cl`, `fw`, `vf`, `ob`, `as`). This is a **Ch02-local
  gap**, not something missing from Ch06 — Ch06 already has everything Ch07 has
  here (the two files' `.tag.*` blocks are identical up to the line-wrap point;
  see the raw diff below).
- `.card.blue{ border-top-color:var(--blue);}` exists only in Ch02's `.card`
  variant list; Ch06 and Ch07 both use the same 5-variant set (`up`, `down`,
  `teal`, `violet`, `slate` — no `blue`). Ch02-local addition.
- `td.s{ color:var(--slate); font-weight:600; white-space:nowrap; }` exists only
  in Ch02's table-cell classes. Absent from Ch06 and Ch07.
- The **checklist item-marker CSS differs in all three files** — see the dedicated
  callout in Section 4 below; each file's `.checklist` rule is structurally
  different, not just re-colored.

**Raw diff output** (Ch06 CSS vs Ch02 CSS; `<` = Ch06, `>` = Ch02), confirming the
above precisely:

```diff
11c11
<   --slate:#566273; --slate-soft:#eaeef3;
---
>   --slate:#445a6e; --slate-soft:#e8edf2;
53c53
< .tag.ob{ background:var(--teal-soft); color:var(--teal); } .tag.as{ background:var(--slate-soft); color:var(--slate); }
---
> .tag.as{ background:var(--slate-soft); color:var(--slate); }
57c57
< .card.up{...} .card.down{...} .card.teal{...} .card.violet{...} .card.slate{...}
---
> .card.up{...} .card.down{...} .card.teal{...} .card.violet{...} .card.blue{...} .card.slate{...}
61,82d60
< [the entire /* DETAILED PLANET PROFILE */ block, quoted in full above]
89c67
< td.up{...} td.dn{...}
---
> td.up{...} td.dn{...} td.s{ color:var(--slate); font-weight:600; white-space:nowrap; }
91a70,74
> .checklist{...} (Ch02's flex-card checklist variant, quoted in Section 4)
108,113d90
< .checklist{...} (Ch06's box-marker checklist variant, quoted in Section 4)
```

**Ch06 CSS vs Ch07 CSS diff** — only three real differences: the `--slate-soft`
value, the `.checklist` block (structurally different marker mechanism), and the
Ch06-only planet-profile block. `.tag.*` order differs cosmetically (Ch07 puts all
five tag rules on one line; Ch06 splits them across two) but the *set* of five tags
is identical.

### Classes defined in Ch06's stylesheet but never used in Ch06's own markup

Scripted check (regex over `class="…"` attributes in Ch06's body against every
class token appearing in Ch06's `<style>` block):

- **`td.dn`** — the coral/down table-cell class is defined but no `<td>` in Ch06
  uses it (Ch06's tables only ever use `td.g`; no table row needs a "down" cell).
- **`.pl-class.mal`** (malefic pill) — defined, but Ch06's two `.planet` cards both
  use `pl-class ben` (benefic) or `pl-class neu` (neutral); `mal` never appears.

Additionally (found by manual inspection, not caught by the plain class-token
script since the token itself is used elsewhere on a different element):
**`.planet-head.down`** and **`.planet-head.violet`** are defined but never applied
— Ch06's two `.planet-head` elements use only `up` (Lesson 6.1, the Moon is
benefic-when-waxing) and `neutral` (Lesson 6.4, the "Sky Today" live read).

### Classes used in Ch06's markup with no rule in its own stylesheet

**None.** The scripted check found zero orphan classes — every class token that
appears in Ch06's body markup has a matching rule somewhere in Ch06's own `<style>`
block.

---

## 3. STRUCTURAL SKELETON

Top-to-bottom element order of `Kindle_Ch06_Moon_Traders_Clock.html`, `<body>` to
`</body>`:

1. `<div class="hero">` — kicker / `<h1>` / sub / ornament. Chapter title block.
2. `<p>` — one un-classed lede paragraph, no wrapper.
3. `<div class="callout slate">` — the book's five-label epistemic-tag key,
   chapter-specific framing text ("now with a fifth label").
4. `<!-- ═══════════ 6.1 ═══════════ -->` (HTML comment, exact glyphs below)
5. `<div class="lesson">` … `</div>` — Lesson 6.1, containing (in order): a
   `.lesson-head`, two `<p>`, one `.planet` card, one `.keyrule`, one `.qa` block,
   one `.recap`.
6. `<hr class="soft"/>`
7. `<!-- ═══════════ 6.2 ═══════════ -->`
8. `<div class="lesson">` … Lesson 6.2 — `.lesson-head`, `<p>`, `.cards` (2 cards),
   `<p>`, five `h3.sec` subsections interleaved with `<p>`, a `.tw`/`table`, a
   `.callout teal`, a `.keyrule`, `.qa`, `.recap`.
9. `<hr class="soft"/>`
10. `<!-- ═══════════ 6.3 ═══════════ -->`
11. Lesson 6.3 — `.lesson-head`, `<p>`, four `h3.sec` subsections, one
    `ol.ladder` (5 items), `.keyrule`, `.qa`, `.recap`.
12. `<hr class="soft"/>`
13. `<!-- ═══════════ 6.4 ═══════════ -->`
14. Lesson 6.4 — `.lesson-head`, `<p>`, two `h3.sec` subsections, a `.honest`
    block, a `.tw`/table, another `h3.sec`, a `.planet` card (the "Sky Today"
    variant), `<p>`, another `h3.sec`, `<p>`, a `.callout coral`, `.keyrule`,
    `.qa`, `.recap`.
15. `<hr class="soft"/>`
16. `<!-- ═══════════ 6.5 ═══════════ -->`
17. Lesson 6.5 — `.lesson-head`, `<p>`, six `h4.lab` + `<p>` pairs ("Rule 1 · …"
    through "Rule 6 · …"), `.callout green`, `.keyrule`, `.qa`, `.recap`.
18. `<hr class="soft"/>`
19. `<!-- ═══════════ 6.6 ═══════════ -->`
20. Lesson 6.6 — `.lesson-head`, `<p>`, `.cards` (6 trap cards), `.keyrule`,
    `.qa`, `.recap`.
21. `<hr class="soft"/>`
22. `<h3 class="sec" style="font-size:24px;text-align:center;">Chapter 6 — Locked
    In</h3>` — **not** wrapped in `.lesson`, sits directly under `<body>`.
23. `<p style="text-align:center;color:var(--ink-soft);">` — one intro sentence.
24. `<ol class="takeaways">` — 5 items.
25. `<h4 class="lab" style="margin-top:30px;">The Practitioner's Checklist …`
26. `<ul class="checklist">` — 7 items.
27. `<h4 class="lab" style="margin-top:30px;">A small glossary — the words you
    met</h4>`
28. `<div class="gloss"><dl>` … 15 `<dt>`/`<dd>` pairs … `</dl></div>`
29. `<p class="bridge">` — closing transition to next chapter.
30. `</body></html>`

**Lesson-separator HTML comments**, quoted exactly (note the specific box-drawing
glyph and spacing — eleven `═` before and after the space-padded number, on both
sides):

```html
<!-- ═══════════ 6.1 ═══════════ -->
```

```html
<!-- ═══════════ 6.2 ═══════════ -->
```

(…and so on through `6.6`.) This exact comment shape — `<!-- ═══════════ N.M
═══════════ -->` — is used identically in Ch02 (`2.1`…`2.6`) and Ch07
(`7.1`…`7.6`). **Universal convention, all three files agree.**

One divergence: **Ch02 also comments its closing summary/checklist sections** as
pseudo-lessons —

```html
<!-- ═══════════ 2.7 SUMMARY ═══════════ -->
```
```html
<!-- ═══════════ 2.8 CHECKLIST ═══════════ -->
```

Neither Ch06 nor Ch07 has an equivalent comment before their "Chapter N — Locked
In" section — it appears directly after the last `<hr class="soft"/>` with no
preceding comment. **Majority (2 of 3, Ch06 + Ch07): no comment before the closing
summary.** Treat Ch02's `2.7`/`2.8` comments as a local one-off; do not add
`<!-- 6A.7 SUMMARY -->`-style comments to Ch06A unless the user wants them.

The `<hr class="soft"/>` separator itself:

```html
<hr class="soft"/>
```

Self-closing XHTML-style slash, used identically (6 times in Ch06, once between
each pair of lessons, once more before the closing summary) in all three files.

---

## 4. COMPONENT PATTERNS

### Hero block

```html
<div class="hero">
  <div class="kicker">The Celestial Ledger · Volume I · Chapter Six</div>
  <h1>The Moon <em>— The Trader's Clock</em></h1>
  <div class="sub">The first deep dive into short-term timing. The fastest body in the sky, the closest celestial analogue to market sentiment — and the most-studied, most-humbling claim in all of financial astrology.</div>
  <div class="ornament">☽ ✦ ☽</div>
</div>
```

**The `.kicker` text has no fixed convention across the three files** — this is a
real inconsistency, not a quirk of one outlier:

- Ch06: `The Celestial Ledger · Volume I · Chapter Six` (spells out the chapter
  number as a word)
- Ch02: `The Celestial Ledger · Volume I` (no chapter reference at all in the
  kicker — the chapter number appears only in `<title>` and in the `.sub` text)
- Ch07: `The Celestial Ledger · Volume I · Part I` (references the *Part*, not the
  chapter number)

No majority exists (each of the three does something different). **This is an
open decision for the user**, not something inferable from the corpus — recommend
following Ch06's pattern verbatim (`… · Chapter Six`) since Ch06A sits directly
after it and shares Part I, but flag this as a choice rather than a discovered
rule.

The `.ornament` line also varies by symbol, all three using **three glyphs
separated by a space**, but not the same glyph set:

- Ch06: `☽ ✦ ☽` (Moon glyphs bracketing a star — chapter-specific)
- Ch02: `✦ ✦ ✦` (plain, literal Unicode)
- Ch07: `&#10022; &#10022; &#10022;` (same ✦ glyph, but numeric-entity-encoded,
  consistent with Ch07's entity-heavy body — see Section 9)

### The claim-type key callout

Ch06's exact key callout:

```html
<div class="callout slate">
  <span class="ct">The claim-type key — now with a fifth label</span>
  Through this book you meet small, honest labels that tell you <em>how sure we are</em> of a thing. <span class="tag cl">Classical</span> an established rule of the tradition · <span class="tag as">Astronomical</span> a verifiable astronomical fact · <span class="tag ob">Observed</span> an empirical finding or caveat from the research literature · <span class="tag fw">Framework</span> this book's market interpretation · <span class="tag vf">Verify</span> to confirm. This is the chapter where the <span class="tag as">Astronomical</span> label earns its place — the Moon's two clocks are matters of fact, not interpretation. Live lunar figures computed with <strong>Swiss Ephemeris for 22 June 2026</strong>.
</div>
```

Wrapper color: Ch06 and Ch07 both use `callout slate` for this opening key; **Ch02
uses `callout teal`** instead (`<div class="callout teal">`, ct text "A promise
renewed"). Majority (2 of 3) = slate; Ch02 is the outlier.

Ch02 only names four labels in its key text (no "Observed" — consistent with Ch02
never defining `.tag.ob` in its CSS, see Section 2). Ch07's key ("The five labels,
still in force") names all five, matching Ch06.

### Callout variants

CSS defines six palettes for `.callout`: bare/gold (default), `.teal`, `.coral`,
`.violet`, `.green`, `.slate` — identically in all three files. **Actual usage per
file differs sharply** (grep-verified counts):

| Variant | Ch06 uses it for… | Ch02 uses it for… | Ch07 uses it for… |
|---|---|---|---|
| bare (gold) | *never* | generic emphasis (×3, e.g. "the hazard, stated plainly") | generic emphasis (×2) |
| `.teal` | cross-cutting synthesis ("Two Clocks, One Moon") | the opening key ("A promise renewed") + one synthesis callout | *never* |
| `.coral` | warning ("Clock, Not Compass") | all 5 numbered "Caution N ·" boxes in the edge-cases lesson | *never* |
| `.violet` | *never* | one "honest-skeptic note" (doing the job Ch06/Ch07 give to `.honest` instead) | *never* |
| `.green` | positive sequence/procedure ("The Day-Trader's Sequence") | *never* | *never* |
| `.slate` | the opening key | one astronomical-fact callout | the opening key + one "Stations Are the Tradeable State" callout |

No two files share the same palette-to-purpose mapping beyond "slate = opening
key" (2 of 3). Treat color choice as authorial/contextual, not mechanical: pick
`teal` for a synthesizing/reconciling point, `coral` for a warning, `green` for a
procedural sequence, bare gold for plain emphasis — following Ch06's own usage,
since that is the file Ch06A must visually match.

Example of each variant actually present in Ch06:

```html
<div class="callout teal">
  <span class="ct">Callout · Two Clocks, One Moon</span>
  <strong>Phase &amp; tithi run on the synodic (Sun-angle) clock — zodiac-free. Sign &amp; nakshatra run on the sidereal (star) clock — sidereal-only.</strong> Always know which clock a given lunar factor is on; mixing them (e.g., comparing a phase cycle to a nakshatra cycle as if identical) manufactures phantom patterns.
</div>
```

```html
<div class="callout coral">
  <span class="ct">Callout · Clock, Not Compass</span>
  The Moon gives you the <strong>tempo and mood</strong> of a session and a sense of <em>when</em> a shift may come. It does not give <strong>direction.</strong> "Active planet Saturn today" suggests a heavy, cautious <em>mood</em> — it does <strong>not</strong> mean "sell." Direction comes from price structure and the higher-timeframe trend; the Moon only times the emotional weather.
</div>
```

```html
<div class="callout green">
  <span class="ct">Callout · The Day-Trader's Sequence</span>
  <strong>Higher-timeframe trend → today's nakshatra/active planet → sign block &amp; Moon aspects → phase bias &amp; new/full flags → confirm against price → fixed risk.</strong> The Moon enters to <em>schedule attention</em>, never to issue a buy or sell by itself.
</div>
```

### Honest block

```html
<div class="honest">
  <span class="ct">The honest-skeptic summary</span>
  <span class="tag ob">Observed</span> There may be a faint full-/new-Moon return tilt detectable in large datasets, but it is <strong>nowhere near a tradable edge on its own</strong>, and a practitioner who bets on it as a rule will be disappointed. It is a reason to <em>watch</em> the phase as a soft sentiment variable — not to trade it.
</div>
```

Used once in Ch06. **Important variant note:** Ch02 defines `.honest`/`.honest .ct`
in its CSS identically to Ch06 (confirmed byte-identical in the stylesheet diff)
but **never uses `class="honest"` anywhere in its own markup** — Ch02 does the
same rhetorical job (a caveated, skeptical aside) with `<div class="callout
violet">` instead. Ch07 uses genuine `.honest` three times. So: two of three files
(Ch06, Ch07) use `.honest` as intended; Ch02's copy of the rule is dead CSS.

### Keyrule block

```html
<div class="keyrule"><span class="small">The rule to lock in</span>The Moon is the <b>fastest</b> body and the <b>mind</b> of the chart — so it times the <b>intraday mood</b>, and only that. It is the clock of the session, never the compass of the trend.</div>
```

Appears exactly once per lesson, at the end of every lesson, in all three files —
universal, no variants found.

### Cards / card block

```html
<div class="cards">
  <div class="card teal"><div class="ic">🌗</div><div class="ti">The Synodic Month <em>~29.53 days</em></div><div class="mt">The cycle of light</div><p>The cycle of <strong>phase</strong>, measured by the Moon's angle to the <em>Sun</em> — new → waxing → full → waning → new.</p></div>
  <div class="card violet"><div class="ic">✶</div><div class="ti">The Sidereal Month <em>~27.32 days</em></div><div class="mt">The cycle of position</div><p>The cycle through the <em>zodiac and the nakshatras</em>, measured against the <strong>stars</strong> — the cycle of placement.</p></div>
</div>
```

And a "trap" variant (icon changes tone, color signals severity — `down` = coral/
negative, `violet`/`teal` = neutral caution):

```html
<div class="card down"><div class="ic">📉</div><div class="ti">1 · Weak evidence</div><div class="mt">Don't build a system on phase</div><p><span class="tag ob">Observed</span> The published lunar-phase effect is tiny, fragile, and inconsistently replicated. As a <em>standalone</em> signal it is not tradable — use the Moon for mood-rhythm and timing-of-attention, never as a mechanical rule.</p></div>
```

### Lesson wrapper, lesson-head, lesson-no, lesson-title

```html
<div class="lesson">
  <div class="lesson-head"><div class="lesson-no">Lesson 6.1</div><div class="lesson-title">Why the Moon <em>Is the Clock</em></div></div>
  ...
</div>
```

Both `.lesson-no` and `.lesson-title` are `<div>`s on one line, identically in
Ch02 and Ch07 — universal convention for numbered chapters. **The Appendix D file
uses a different, span-based, multi-line form** for its equivalent header (not one
of the three chapters under comparison, but relevant if Ch06A ever needs to match
appendix style instead):

```html
<div class="lesson-head">
  <span class="lesson-no">Appendix D</span>
  <span class="lesson-title">Consolidated <em>Glossary</em></span>
</div>
```

Do not use the appendix's span/multi-line form for a chapter file — use Ch06's
div/single-line form.

### `h3.sec` and `h4.lab` subheadings

```html
<h3 class="sec">Phase — the cycle of light</h3>
```
```html
<h4 class="lab">Rule 1 · Read the higher timeframe first</h4>
```

`h3.sec` is used for topical subsections within a lesson (identical usage across
all three files). `h4.lab` is used two ways in Ch06: as small-caps rule headers
within Lesson 6.5 (`Rule 1 · …`), and — with an inline `style="margin-top:30px;"`
— as the two closing-section headers ("The Practitioner's Checklist…", "A small
glossary…"). Both usages recur identically in Ch02 and Ch07.

### `ol.ladder`

Ch06's form — **no wrapping `<span>`** around each item's content:

```html
<ol class="ladder">
  <li><b>Tithi</b> — the lunar day (Moon's 12° elongation steps from the Sun).</li>
  <li><b>Vara</b> — the weekday, each ruled by a planet.</li>
  <li><b>Nakshatra</b> — the Moon's mansion for the day.</li>
  <li><b>Yoga</b> — a Sun–Moon angular combination.</li>
  <li><b>Karana</b> — a half-tithi.</li>
</ol>
```

Ch07 matches this exactly (bare `<li><b>…</b> text</li>`, no span). **Ch02 wraps
every item's content in an extra `<span>`:**

```html
<ol class="ladder">
  <li><span><b>Label every chart.</b> No position is ever stated without its frame: …</span></li>
  ...
</ol>
```

Majority (2 of 3, Ch06 + Ch07): no wrapping span. Ch02's `<span>` wrapper is inert
(no CSS targets `.ladder li > span` specifically) — cosmetically harmless but
inconsistent. **Follow Ch06's unwrapped form.**

### Data table markup

```html
<div class="tw">
  <table>
    <thead><tr><th>Moon aspecting…</th><th>The mood-tint it is read as</th></tr></thead>
    <tbody>
      <tr><td class="g">Moon–Jupiter</td><td>optimism, expansion, ease</td></tr>
      <tr><td class="g">Moon–Saturn</td><td>caution, heaviness, fear</td></tr>
      <tr><td class="g">Moon–Mars</td><td>agitation, volatility, impulsiveness</td></tr>
      <tr><td class="g">Moon–Rahu</td><td>nervous, speculative froth</td></tr>
      <tr><td class="g">Moon–Venus</td><td>ease, comfort-buying</td></tr>
    </tbody>
  </table>
</div>
```

- Wrapper: `<div class="tw">` (enables `overflow-x:auto` for mobile) — universal
  across all three files, every table.
- **No `scope` attribute anywhere** — checked across the entire `raw/` directory
  (25 files, `scope=` grep returns zero matches). Accessibility semantics rely
  entirely on visual convention (first column styled `td.g`, gold), not markup.
  Do not add `scope="col"`/`scope="row"` to Ch06A's tables — it would be the only
  file in the book doing so.
- Cell classes seen in Ch06: `td.g` (label/gold column, used on essentially every
  first `<td>`), `td.up` (green, bullish), `td.dn` (coral, defined but — per
  Section 2 — never actually triggered in Ch06's own tables). `td.s` (slate) is a
  Ch02-only addition, absent from Ch06's CSS.

### QA block

```html
<div class="qa">
  <div class="qa-h">💬 Check yourself · Lesson 6.1</div>
  <div class="qa-i"><div class="qa-q"><b>Q1</b>Why does the tradition make the Moon the significator of the mind and the crowd?</div><div class="qa-a"><b>A</b>Because it is the <strong>fastest, most restless</strong> body — it changes daily, like the reactive mind (<em>manas</em>) and the public's daily mood.</div></div>
  <div class="qa-i"><div class="qa-q"><b>Q2</b>...</div><div class="qa-a"><b>A</b>...</div></div>
  <div class="qa-i"><div class="qa-q"><b>Q3</b>...</div><div class="qa-a"><b>A</b>...</div></div>
</div>
```

Always exactly **three** Q/A pairs, one per lesson, in Ch06. (Not independently
verified as a hard rule across the whole book, but true for all six lessons in
Ch06 and all six in Ch02 and Ch07 — 18/18 lessons checked have exactly 3 pairs.)
`💬` is a literal emoji character, not an entity, in Ch06 (consistent with Ch06's
literal-Unicode convention — see Section 9); Ch07 encodes the same emoji as
`&#128172;`.

### Recap block, and what the number in `div.n` counts

```html
<div class="recap"><div class="n">6</div><div><div class="l">Lesson 6.5 — Locked In</div><div class="t">The disciplined routine</div><div class="d">Six rules and one sequence — trend first, Moon last, price confirming, risk fixed — that turn the lunar clock into a filter for attention, not a trade trigger.</div></div></div>
```

**Values found, all three chapters, in lesson order:**

| Lesson | Ch06 `.n` | Ch02 `.n` | Ch07 `.n` |
|---|---|---|---|
| .1 | `☽` | `✦` | `&#10022;` (✦) |
| .2 | `2` | `2` | `5` |
| .3 | `5` | `2` | `6` |
| .4 | `📊` | `2` | `&#10022;` (✦) |
| .5 | `6` | `2` | `6` |
| .6 | `⚠` | `2` | `7` |

**The counting rule is not cleanly inferable — state this plainly rather than
inventing a formula:**

- **Every chapter's first lesson (`.1`) uses a symbol, never a number.** This part
  *is* a solid, 3-for-3 convention — use a symbolic glyph (matching the chapter's
  theme, as Ch06 does with `☽`) for Ch06A's opening lesson's recap.
- In Ch06 and Ch07, the number **often** matches a count of something explicitly
  enumerated in that lesson: Ch06 6.3 → 5 (the Panchanga's five limbs, an
  `ol.ladder` with 5 `<li>`s); Ch06 6.5 → 6 (six `h4.lab` "Rule N ·" headers);
  Ch07 7.2 → 5 (five dimensions of state, five `h3.sec` subsections); Ch07 7.3 → 6
  (Shadbala's six-row table); Ch07 7.5 → 6 (an `ol.ladder` with 6 items); Ch07
  7.6 → 7 (an `ol.ladder` with 7 items).
- **This pattern breaks at least once, inside Ch06 itself:** Lesson 6.6 has
  exactly 6 trap cards in its `.cards` block, which by the pattern above should
  give `.n` = `6` — but Ch06 uses the symbol `⚠` instead. Lesson 6.4 similarly has
  no single clean enumerable list (it is a discursive, evidence/citation-heavy
  lesson) and uses `📊` — consistent with "use a symbol when nothing enumerable
  exists," but 6.6 contradicts that, since it *does* have a countable list of 6.
- **Ch02's `.n` is `2` for every lesson after 2.1**, which is simply Ch02's own
  chapter number repeated — it does not track a per-lesson count at all (Lesson
  2.5, for instance, presents *five* numbered rules but shows `.n` = `2`). This
  looks like an unmaintained placeholder rather than a deliberate convention.

**Conclusion: UNDETERMINED as a mechanical rule.** The safest approach for Ch06A:
use a chapter-appropriate symbol for the opening lesson's recap (matching the
✦/☽-style convention), and for interior lessons, count the lesson's own primary
enumerated list (rule set, ladder, or table rows) *when one exists and is the
lesson's clear organizing device* — falling back to a symbol when the lesson is
discursive rather than list-structured, as Ch06 itself does in 6.4 (but
inconsistently in 6.6). This is an authorial judgment call, not a formula to
apply blindly.

### `hr.soft` separator

```html
<hr class="soft"/>
```

Self-closing, XHTML-style. One between every pair of lessons and once more before
the closing "Chapter N — Locked In" section. Identical in all three files.

### Chapter-close heading, `ol.takeaways`, `ul.checklist`

```html
<h3 class="sec" style="font-size:24px;text-align:center;">Chapter 6 — Locked In</h3>
<p style="text-align:center;color:var(--ink-soft);">You have learned the trader's clock in full — its mechanism, its tradition, its evidence, and its discipline. Here are the five things to carry forward.</p>
<ol class="takeaways">
  <li><strong>The Moon is the trader's clock</strong> — fastest body, significator of <em>manas</em> (mind), and the proxy for sentiment and liquidity. It governs the intraday and day-to-day layer, never the primary trend.</li>
  ...
</ol>
```

`ol.takeaways` items are plain `<li><strong>…</strong> …</li>`, no wrapping span,
identically in all three files — no variant found.

**`ul.checklist` — the item marker is genuinely different in all three files** (the
user's premise names `span.bx` / `span.box-span`; neither name is exactly right
for Ch06, so stating the actual class found in each file matters):

Ch06 uses **`span.box`** (not "box-span") — an empty span with no text content,
styled as a blank checkbox by CSS border/dimensions alone:

```html
<li><span class="box"></span><div><b>1. Higher timeframe established?</b> Do you know the primary and intermediate trend the Moon is operating <em>inside</em>?</div></li>
```

Ch02 uses **`span.bx`** — a *filled* span, containing the literal item-number as
its text content, doubling as both the marker and the numeral:

```html
<li><span class="bx">1</span><span><b>Angle or placement?</b> Is this an aspect / cycle question (zodiac-free) or a sign / house / nakshatra question (zodiac-critical)? If angle-only, stop worrying about the zodiac.</span></li>
```

Ch07 uses **neither** — no marker `<span>` exists in the markup at all. The
checkmark is pure CSS, injected via `.checklist li::before{ content:'\2713'; ...}`:

```html
<li><b>Dignity set?</b> Exalted / own / friendly / neutral / enemy / debilitated — and the <em>quality</em> of expression calibrated (not the direction)?</li>
```

All three are visually similar (a small square/checkmark to the left of text) but
structurally incompatible — copying one file's checklist `<li>` markup into
another file's stylesheet would render wrong (Ch02's `.bx` text-number would show
up as an empty CSS-only box if pasted under Ch07's rules, etc.). **For Ch06A, use
Ch06's exact form** (`<span class="box"></span>` + a `<div>` whose bold text opens
with the digit and period, e.g. `<b>1. …</b>`) since that is the file it must
match, and copy Ch06's `.checklist`/`.checklist .box` CSS rule verbatim (already
quoted in Section 2) — do not reuse Ch02's or Ch07's checklist CSS by mistake.

### Gloss `dl`

```html
<div class="gloss"><dl>
  <dt>Synodic month (~29.53 days)</dt><dd>The cycle of phase — the Moon's angle to the Sun (new → full → new). Zodiac-independent. The cycle of light.</dd>
  ...
</dl></div>
```

Wrapped in `<div class="gloss"><dl>…</dl></div>` in all three chapter files
(Ch06/Ch02/Ch07 agree). **The Appendix D glossary uses a different wrapper** — see
Section 8.

### `p.bridge`

```html
<p class="bridge">End of Chapter 6. The clock is set, and its limits are honest.<br/>Next: <strong>Chapter 7 — "Dignity, Strength &amp; Speed,"</strong> which makes precise the "state" of a planet that Chapters 4–6 kept invoking — exaltation and debilitation, retrogradation, combustion, and stations — and why a planet's <em>condition</em>, not just its identity, drives its market effect.</p>
```

One `<br/>` splits an "End of Chapter N…" sentence from a "Next: **Chapter
N+1**…" sentence, identically in all three files — universal convention, and the
mechanism by which Ch06A must be wired into the book's forward/backward
narrative (see Section 9 for what specifically needs to change on both sides of
the seam).

---

## 5. EPISTEMIC TAG SYSTEM

Exact span markup (identical in all three files, for the five tags that exist):

```html
<span class="tag cl">Classical</span>
<span class="tag as">Astronomical</span>
<span class="tag ob">Observed</span>
<span class="tag fw">Framework</span>
<span class="tag vf">Verify</span>
```

**Per chapter:**

| | Tags named in the chapter's own opening "key" callout | Tags actually used in the chapter's body |
|---|---|---|
| Ch06 | cl, as, ob, fw, vf (all 5) | cl, as, ob, fw (4 — **vf never appears in the body**) |
| Ch02 | cl, fw, as, vf (4 — no "ob" mentioned, and no `.tag.ob` CSS rule exists in this file) | cl, fw, as (3 — **vf named in the key but never used in the body either**) |
| Ch07 | cl, as, fw, ob, vf (all 5) | cl, as, fw, ob (4 — **vf never appears in the body**, same gap as Ch06) |

**Flag:** in all three files, `vf` ("Verify") is defined in CSS and named in the
opening key, but is **never actually applied to a span in the body** of any of the
three chapters. This is a 3-for-3 pattern, not a Ch06 quirk — the "Verify" tag
appears to exist as a promised-but-rarely-invoked fifth category across the book
generally, at least in this sample. Do not treat its absence from Ch06A as an
error if it turns out unneeded; but if Ch06A's content includes a
convention-dependent figure (an ayanamsa value, an uncertain date, anything Ch02's
own key describes as "Verify"-worthy), this is precedent for actually using it,
which none of the three sampled chapters do.

No tag is used in any of the three chapters' bodies that is absent from that same
chapter's own key callout — no reverse-direction flag needed.

---

## 6. CROSS-REFERENCE STYLE

**All cross-references in this directory are plain text, never hyperlinks.**
Verified: a search for `<a href` across every file in `raw/` returns zero matches.
The only `<a>`/`href`-bearing tag anywhere is the single Google Fonts `<link>` in
every file's `<head>`.

Three real examples, quoted verbatim:

```html
If the chart confirms a reactive, range-respecting day, the lunar read added color; if price ignores it, the chart wins (Chapter 3).
```

```html
The strongest folkloric use of phase is as a <strong>turning-point window</strong>: new and full Moons (and especially eclipses — Chapter 10) are watched as moments when sentiment may crest or break.
```

```html
Next: <strong>Chapter 7 — "Dignity, Strength &amp; Speed,"</strong> which makes precise the "state" of a planet that Chapters 4–6 kept invoking …
```

Pattern: a parenthetical `(Chapter N)` for a passing reference, or a full
`<strong>Chapter N — "Title,"</strong>` construction for the `.bridge` paragraph's
forward-pointer specifically. Appendix citations follow the same plain-text rule —
a real example from Ch06 itself:

```html
Demand pre-registered, out-of-sample tests (Chapter 18).
```

and from Ch07's checklist:

```html
Station dates in particular shift with the ephemeris and must be looked up precisely (Appendix A).
```

For Ch06A: reference other chapters and appendices the same way — plain
parenthetical text, never a hyperlink, even though this is web-viewable HTML.

---

## 7. TABLE OF CONTENTS / NAVIGATION

**No file in this directory (`raw/`) contains a book-level table of contents,
index, or chapter-enumerating navigation list.** Checked: `Kindle_Ch00_Building_
Blocks_v2.html` (the most likely candidate, as front matter) contains no
"Table of Contents"/"Contents" heading or list; no other file was found via
search either. Each chapter is a fully standalone HTML file with no links to any
other file (consistent with Section 6 — there are no hyperlinks anywhere in this
directory).

Because there is no TOC to update, **inserting Ch06A between Ch06 and Ch07
requires no navigation-file change** — only the two chapters' own `.bridge`
paragraphs need editing (Ch06's "Next: Chapter 7…" sentence would need to become
"Next: Chapter 6A…", and Ch06A's own bridge would need to point on to Chapter 7).
This is a **content decision for the user**, not something this read-only
extraction should perform — flagging it here as the one concrete cross-file edit
that Ch06A's insertion implies, beyond writing the new file itself.

(Note: a `build/index.html` exists one level up from `raw/`, and appears to be a
separately-generated shell/reader page rather than a hand-authored TOC in this
book's own convention — it was not read in depth, since the task scope is the
`raw/` directory's own three reference chapters. If the user also maintains that
build output, it may need separate updating; UNDETERMINED whether it
auto-regenerates from `raw/` or needs manual editing, since that question falls
outside the three files this spec was asked to analyze.)

---

## 8. GLOSSARY AND APPENDIX CONVENTIONS

Ch06's in-chapter glossary, quoted in full:

```html
<div class="gloss"><dl>
  <dt>Synodic month (~29.53 days)</dt><dd>The cycle of phase — the Moon's angle to the Sun (new → full → new). Zodiac-independent. The cycle of light.</dd>
  <dt>Sidereal month (~27.32 days)</dt><dd>The cycle of position — the Moon through the zodiac and nakshatras, measured against the stars. The cycle of place.</dd>
  <dt>Phase</dt><dd>The waxing/waning state of the Moon; waxing reads as the stronger, building, optimism-leaning half, waning as the weaker.</dd>
  <dt>Tithi</dt><dd>A lunar "day" — the time for the Moon to gain 12° of elongation from the Sun; thirty to a synodic month, in two pakshas (Shukla waxing, Krishna waning).</dd>
  <dt>Paksha</dt><dd>A fortnight of fifteen tithis — Shukla (bright/waxing) or Krishna (dark/waning).</dd>
  <dt>Active planet</dt><dd>The Vimshottari lord of the day's Moon-nakshatra, read as the planet whose flavor colors the session's mood.</dd>
  <dt>Void-of-course Moon</dt><dd>Western horary term: the stretch after the Moon's last major aspect in a sign before it changes sign — low-conviction, "nothing comes of the matter." Not a Vedic concept.</dd>
  <dt>Panchanga</dt><dd>The Hindu almanac's five limbs — tithi, vara (weekday), nakshatra, yoga, and karana.</dd>
  <dt>Yoga</dt><dd>A Sun–Moon angular combination; one of the five Panchanga limbs.</dd>
  <dt>Karana</dt><dd>A half-tithi; one of the five Panchanga limbs.</dd>
  <dt>Muhurta</dt><dd>Electional timing — the choosing of an auspicious moment, assembled from the Panchanga (Chapter 14).</dd>
  <dt>Janma Rashi / Janma Nakshatra</dt><dd>The birth Moon-sign and birth Moon-nakshatra; central to Vedic reading and to the dasha clock.</dd>
  <dt>Paksha bala</dt><dd>"Strength by fortnight" — the classical scheme giving the waxing Moon benefic power and the waning Moon weakness.</dd>
  <dt>Lunar-phase effect</dt><dd>The researched claim that returns differ around new vs. full Moon; published but tiny, fragile, and inconsistently replicated.</dd>
  <dt>Hasta</dt><dd>The 13th nakshatra (the "open hand"); themes of skill, dexterity, and precision; lord, the Moon. The day-Moon's mansion on 22 June 2026.</dd>
</dl></div>
```

Appendix D's glossary, a representative excerpt (structure, not full content):

```html
<h3 class="sec">D.1 Astrological &amp; Jyotish terms</h3>
<dl class="gloss">
  <dt>Antardasha</dt><dd>a sub-period within a mahadasha; the second level of the Vimshottari timeline (Ch 12).</dd>
  <dt>Arudha pada</dt><dd>in Jaimini, a sign's "image" or perceived manifestation, derived by a counting rule (Ch 0, library Cluster D).</dd>
  ...
  <dt>Yoga</dt><dd>a defined planetary combination (e.g., <em>Dhana yoga</em> for wealth) (Ch 5).</dd>
</dl>
```

**Structural difference, confirmed:** an in-chapter glossary (Ch06/Ch02/Ch07) wraps
its `<dl>` in `<div class="gloss">…</div>` — i.e. `<div class="gloss"><dl>`. The
Appendix D glossary puts the `gloss` class directly on the `<dl>` itself, with no
wrapping `<div>` — i.e. `<dl class="gloss">`. Both render identically (the CSS
selectors `.gloss`, `.gloss dt`, `.gloss dd` match either placement equally, since
`.gloss dt`/`.gloss dd` are descendant selectors), but the markup shape is not the
same. **Do not copy Appendix D's `<dl class="gloss">` form into Ch06A** — Ch06A is
a chapter, and all three sampled chapters agree on `<div class="gloss"><dl>`.

Additionally, Appendix D's `dd` entries end each entry with a parenthetical
chapter citation in the abbreviated form `(Ch N)` (e.g. `(Ch 12)`, `(Ch 0, App
B.2)`) rather than the chapters' own spelled-out `(Chapter N)` form. This is a
**deliberate appendix-vs-chapter convention split**, not an error — appendix
entries are terse by design (cross-referencing dozens of terms), while in-chapter
prose spells "Chapter" out. Keep Ch06A's own glossary using the spelled-out form,
matching Ch06/Ch02/Ch07.

**Insertion point for new alphabetized terms in Appendix D:** the D.1 list is
strictly alphabetical, one `<dt>`/`<dd>` pair per line, no blank lines between
entries. A new term is inserted as a new `<dt>`/`<dd>` line in alphabetical
position. For example, a term beginning with "B" (as "Bhadra" would) goes between
the existing `Ayanamsa` and `Bhava` entries:

```html
  <dt>Ayanamsa</dt><dd>the angular gap between the tropical and sidereal zodiacs (~24.23° Lahiri today), growing ~1°/72 yr by precession. Lahiri and KP ayanamsas differ by ~6′ (Ch 2).</dd>
  <dt>[NEW TERM HERE, alphabetically between "Ayanamsa" and "Bhava"]</dt><dd>[definition] (Ch 6A).</dd>
  <dt>Bhava</dt><dd>a house; one of twelve life-arenas measured from the ascendant. The "wealth houses" (2, 11; also 5, 9) and "loss houses" (8, 12) recur in market work (Ch 5).</dd>
```

Whether any Ch06A-specific term (e.g. "Bhadra," "Karana," if not already covered —
note **`Karana` is already a defined term in Ch06's own in-chapter glossary**, so
check for duplication before adding it again to Appendix D) needs a new Appendix D
entry is a content decision outside this extraction's scope — flagged, not
resolved, per the instruction to write "UNDETERMINED" rather than invent content.

---

## 9. GAPS AND CAUTIONS

Concrete things a new-chapter author would get wrong by imitating Ch06 blindly,
each with the offending/contrasting markup quoted:

1. **Ch07's entire body uses HTML entities where Ch06 and Ch02 use literal
   Unicode characters.** This is the single biggest silent trap: copying a
   sentence structure from Ch07 (correctly rendering, but written as
   `&mdash;`/`&rsquo;`/`&ldquo;`/`&rdquo;`/`&deg;`/`&rarr;`) into a file that
   otherwise follows Ch06's literal-character convention will look inconsistent
   at the source level even though both render the same in a browser. Measured
   counts:

   | | `&mdash;` entity | literal — | `&rsquo;` entity | literal curly `'` | `&deg;` entity | literal ° |
   |---|---|---|---|---|---|---|
   | Ch06 | 0 | 122 | 0 | 0 | 0 | 11 |
   | Ch02 | 0 | 71 | 0 | 0 | 0 | 51 |
   | Ch07 | 112 | 1 | 27 | 0 | 27 | 0 |

   **Ch06 and Ch02 write em dashes, degree signs, and arrows as literal UTF-8
   characters, and apostrophes/quotes as plain straight ASCII (`'`, `"`) — never
   curly.** Ch07 writes almost everything as an HTML entity, including curly
   typographic quotes it never uses as literal characters. **Follow Ch06's
   literal-character, straight-quote convention for Ch06A** — it is the file
   Ch06A must match, and it is also the majority (2 of 3) convention.

   One inconsistency exists *inside* Ch07 itself: its `<title>` tag uses a
   literal em dash even though the rest of the file uses `&mdash;` throughout:

   ```html
   <title>The Celestial Ledger — Chapter 7: Dignity, Strength &amp; Speed</title>
   ```

   (Literal `—` in the title; `&amp;` — itself an entity for a literal `&` — a
   few words later.) This single-line mix is a genuine defect in Ch07, not a
   convention to imitate.

2. **`&amp;` vs literal `&` is used correctly and consistently within each
   file** wherever an ampersand appears in prose (e.g. Ch07's own title, "Dignity,
   Strength &amp; Speed"), **except** inside the Google Fonts `<link>` href, where
   **all three files** use raw, un-escaped `&` characters in the query string:

   ```html
   <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,900;1,400;1,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
   ```

   This is technically invalid HTML (an attribute value should escape `&` as
   `&amp;`), but it is universal across the whole directory and browsers parse it
   fine. Reproduce it exactly as-is for consistency — "fixing" it in Ch06A alone
   would make that one file inconsistent with all 24 others.

3. **The `.checklist` marker mechanism is not portable between files** (detailed
   in Section 4) — Ch06 uses `span.box` (empty, CSS-styled square), Ch02 uses
   `span.bx` (contains the literal digit), Ch07 uses no span at all (a pure
   `::before{content:'\2713'}` checkmark). Pasting a `<li>` from one file under
   another file's `<style>` block will not render as intended. Ch06A must use
   Ch06's exact `span.box` + numbered-`<b>` form and Ch06's `.checklist` CSS.

4. **The `.planet` component (Section 2) does not exist in Ch07's or Ch02's
   stylesheets at all** — if Ch06A's content calls for a similar profile card
   (e.g. profiling Bhadra karana, a nakshatra, or a yoga the way Ch06 profiles
   the Moon), the CSS must be copied from Ch06, not assumed to be a book-wide
   base component available everywhere.

5. **The `.tag.ob` ("Observed") class does not exist in Ch02's stylesheet** — a
   chapter that copies its base `<style>` block from Ch02 rather than Ch06 would
   silently be unable to render an Observed-tagged span (it would fall back to
   unstyled inline text). Always base Ch06A's stylesheet on **Ch06's** copy, which
   has the full five-tag set.

6. **No file in this directory uses `scope` attributes on table headers**, and no
   file uses semantic table accessibility markup beyond plain `<th>`/`<td>`. This
   is consistent book-wide, not a Ch06 shortfall to "fix" — do not add `scope=`
   attributes to Ch06A's tables, it would be the only file in the book doing so.

7. **No hyperlinks exist anywhere in this directory** (Section 6/7) — every
   cross-reference, including appendix citations, is plain parenthetical text.
   Do not add `<a href="#...">` internal anchors to Ch06A even though the file
   will sit inside a larger book; that would be a new convention with zero
   precedent in the other 24 files.

8. **The hero `.kicker` text has three different conventions across three files**
   (Section 4) — there is no single pattern to copy mechanically; it is an open
   authorial decision each chapter makes independently.

9. **The `recap`'s `.n` numeral is not a mechanically-derivable count** (Section
   4) — Ch06 itself breaks its own apparent pattern in Lesson 6.6. Do not write
   code or a fixed rule to auto-generate this value for Ch06A's lessons; pick it
   editorially per lesson, the way the existing chapters evidently did.

10. **No unclosed tags or other raw HTML malformation were found in Ch06, Ch02,
    or Ch07** beyond the two items above (the un-escaped `&` in the font href,
    and Ch07's single literal-em-dash-in-a-sea-of-entities inconsistency in its
    own `<title>`). All `<div>`/`<p>`/`<li>`/`<table>` structures in the three
    sampled files close correctly and nest correctly, as far as manual reading
    plus the scripted class/CSS diffs could confirm. No stale internal reference
    (e.g. a "Chapter N" pointer to content that no longer exists at that number)
    was found in Ch06, Ch02, or Ch07 specifically — but inserting Ch06A does
    create exactly one **necessary** edit outside the new file itself: Ch06's own
    closing `.bridge` paragraph currently reads "Next: Chapter 7 …" and, once
    Ch06A exists between them, either that sentence or Ch06A's own bridge (or
    both) will need updating so the forward-reference chain stays accurate. This
    extraction does not perform that edit — it only flags that it will be needed
    (Section 7).

---

*End of build specification. This document itself is `CH06A_BUILD_SPEC.md`,
written to `C:\Shiva\FinAstro_Guide\raw\` — the only file this extraction created
or modified. No other file in the directory was altered.*
