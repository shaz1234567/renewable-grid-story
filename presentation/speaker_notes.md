# Speaker Notes — 13-Minute Presentation and Live Demo

**Presenter:** Shazab Ali  
**Project:** The Renewable Grid, Hour by Hour  
**Target duration:** 13:00  
**Source code:** <https://github.com/shaz1234567/renewable-grid-story>  
**Deployment:** <https://renewable-grid-story.onrender.com/>

## 0:00–1:00 — Slide 1: Opening

“My project is *The Renewable Grid, Hour by Hour*, a six-view interactive story built from 2025 EIA-930 operating data.”

State the central question: how can a reader understand changes across a day, a year, and multiple regions without losing scale, variability, missingness, or methodological limits?

Preview the argument: absolute output and renewable share tell different stories, and combining renewable sources can smooth some signals without always beating the steadiest component.

## 1:00–2:00 — Slide 2: Audience and narrative design

Identify the audience as students, instructors, and interested public readers with basic chart literacy.

Explain the sequence:

1. whole-system context;
2. one renewable day;
3. annual source patterns;
4. regional comparison;
5. numerical variability; and
6. portfolio complementarity.

Emphasize that this is descriptive visualization—not a forecast, causal dispatch explanation, capacity-factor study, or reliability model.

## 2:00–3:10 — Slide 3: Preparation-code talking points

Use these concise code-level points:

- The source is a fixed Zenodo record of EIA Form 930, version 97.0.0.
- The download stage verifies published MD5 values and records SHA-256 checksums.
- Preparation filters CISO, ERCO, NYIS, and PJM.
- For each field, adjusted values are preferred, then imputed, then raw.
- Solar combines with- and without-integrated-battery reporting; wind does the same.
- Renewables equal solar + wind + hydropower excluding pumped storage.
- Standalone and pumped storage are excluded from the primary mix.
- One-hour average MW sums to MWh; daily curves are available-hour arithmetic means.
- Missing values remain gaps rather than being filled after preparation.

Mention that the processed result is 35,040 rows: 8,760 per authority.

## 3:10–4:00 — Slide 4: Validation

Say clearly: “Validation is not entirely clean.”

- 10 of 11 persisted checks pass.
- Coverage, unique timestamps, hourly continuity, arithmetic, archive integrity, and versioned provenance pass.
- The required-values check fails.
- There are **31 missing renewable and generation-mix rows**, plus 25 missing demand and net-generation rows.
- The app reports missing values beside affected selections.

Mention the 21 automated tests, but distinguish tests from audience evaluation.

## 4:00–4:50 — Slide 5 + live View 1: Generation mix

Switch to the local application at <http://127.0.0.1:8050/#view-1>.

Demo route:

1. Confirm CISO and June 15, 2025.
2. Hover across the stacked mix.
3. Point to the takeaway and missing-data notice.
4. Briefly switch authority or date, then return to the default.

Finding: solar has the largest summed hourly average on the default CISO day, about 35.1% of the positive reported mix. Explain that “positive reported mix” avoids allowing retained negative reports to distort the denominator.

## 4:50–5:40 — Slide 6 + live View 2: Hourly playback

Navigate to `#view-2`.

1. Click Reset.
2. Click Next twice.
3. Click Play, let several points appear, then Pause.
4. Drag the slider toward the last observation.

Explain that the maximum is based on the selected day’s actual record count, supporting 23- and 25-observation daylight-saving days. Playback is clamped at both boundaries.

## 5:40–6:35 — Slide 7 + live View 3: Annual pulse

Navigate to `#view-3`.

1. Show all three sources in absolute mode.
2. Toggle individual source checkboxes.
3. Switch to Normalized.

Say: “Each source is divided by its own annual peak. A value of 100% means that source’s peak, not equal MW and not renewable share.” Use the normalized mode to discuss shape and the absolute mode to discuss magnitude.

## 6:35–7:30 — Slide 8 + live View 4: Regional comparison

Navigate to `#view-4`.

1. Keep CISO and ERCO.
2. Keep solar and the full 2025 period.
3. Toggle Raw MW to Normalized and back.
4. Point out that both series use exactly the same operating dates.

Finding: ERCO’s 2025 hourly mean solar is about 7,723.9 MW versus CISO’s 5,667.9 MW—about 1.36 times as high. Clarify that map points are schematic references, not balancing-authority boundaries.

## 7:30–8:30 — Slide 9 + live View 5: Variability

Navigate to `#view-5`.

Read selected CISO solar metrics:

- mean: 5,667.9 MW;
- maximum: 18,912 MW;
- sample standard deviation: 6,818.2 MW; and
- CV: 1.203.

Explain CV as sample standard deviation divided by the absolute mean. It compares relative spread, but it is not predictability, ramping difficulty, forecast error, or reliability. If the mean is zero—as with available NYIS solar values—the implemented result is “undefined.”

## 8:30–9:40 — Slide 10 + live View 6: Portfolio

Before revealing the comparison, ask the class:

> If solar, wind, and hydropower are combined, will the portfolio always have the lowest coefficient of variation?

Pause briefly for responses, then navigate to `#view-6`.

1. Show all three selected sources.
2. Point to the combined daily-mean line.
3. Point to the CV comparison chart.
4. Toggle one source off, then use Reset sources.

Finding: CISO 2025 CVs are solar 1.203, wind 0.595, hydropower 0.463, and combined 0.590. The portfolio is lower than solar and wind, but not lower than hydropower. The outcome depends on covariance, source choice, region, and period.

## 9:40–10:40 — Slide 11: Main annual findings

Return to slides.

- ERCO: 182.821 million MWh renewables, the largest absolute output; 37.583% share.
- CISO: 90.819 million MWh; the largest share at 48.744%.
- NYIS: 31.137 million MWh; 23.500%.
- PJM: 72.299 million MWh; 8.255%.

Explain why this matters: PJM exceeds NYIS in absolute renewable energy but has a much lower share because its net generation is much larger. A single ranking cannot answer both scale and composition questions.

## 10:40–11:35 — Slide 12: Evaluation and limitations

Completed evidence:

- 21 automated tests;
- internal desktop and mobile rendering checks;
- playback and normalized-control checks; and
- six reproducible screenshots.

Human evaluation:

- one visual review identified overlapping chart titles and legends;
- the accepted revision separated title/legend zones, improved responsive spacing, and added a colorblind-safe palette; and
- a broader target-audience comprehension session remains pending.

Key limitations: one year, four authorities, 31 renewable/mix gaps, authority-specific reporting, no capacity normalization, schematic map, and descriptive CV.

## 11:35–12:25 — Slide 13: Answer and contribution

Answer the class question: no, a portfolio does not automatically have the lowest CV.

Summarize the project contribution:

- a coherent six-view explanatory sequence;
- reproducible source-to-figure workflow;
- explicit equations and boundary behavior;
- honest disclosure of failed validation and pending human testing.

State that the Render URL has been verified and that the local app remains the presentation backup.

## 12:25–13:00 — Close and questions

Close with:

“The key lesson is that renewable output has to be read in context: by hour, season, place, scale, and variability. The interface makes those comparisons available while keeping the missing data and analytical limits visible.”

Invite questions.

## Live-demo route checklist

- [ ] Start app: `python app.py`
- [ ] Open <http://127.0.0.1:8050>
- [ ] View 1: hover CISO June 15 mix
- [ ] View 2: Reset → Next → Play/Pause → slider
- [ ] View 3: source checkboxes → Normalized → Absolute
- [ ] View 4: CISO/ERCO solar → Normalized → Raw MW
- [ ] View 5: read CISO solar metrics and CV
- [ ] Ask interactive class question
- [ ] View 6: toggle source → inspect CV → Reset sources
- [ ] Return to slides for annual findings and limitations

## Backup checklist

- [ ] Run `pytest` before presenting.
- [ ] Run `python scripts/build_academic_package.py`.
- [ ] Confirm all six files exist under `report/screenshots/`.
- [ ] Keep `report/final_report.pdf` open locally.
- [ ] Keep `presentation/slides.pptx` open locally.
- [ ] Keep the six screenshots open or available if the app fails.
- [ ] Test the local server and browser at the presentation venue.
- [ ] Disable notifications and unnecessary browser extensions.
- [ ] Carry a local copy of the repository in case the free Render service is waking or venue networking fails.
- [ ] If rendering is slow, narrate the screenshots in View 1–6 order.
- [ ] If controls fail, describe tested behavior without claiming a live result.
- [ ] Do not claim human feedback until both sessions are actually completed.
