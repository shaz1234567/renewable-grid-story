# Evaluation and Revision Log

**Project:** The Renewable Grid, Hour by Hour  
**Researcher:** Shazab Ali  
**Human-testing status:** **Pending — no human feedback has been collected or claimed.**

## Evidence available now

### Automated evaluation

The repository contains 17 collected tests:

- 2 application/layout tests;
- 2 callback/control-helper tests;
- 1 archive-hash test;
- 8 figure and analytical-behavior tests;
- 1 metric test;
- 1 preparation test; and
- 1 validation test.

These tests cover the six-view structure, required controls, playback boundary clamping, source reset/filtering, archive hashes, empty selections, stacked generation traces, selected-source routing, independent normalization, matched regional dates, date-range filtering, CV safety at a zero mean, portfolio totals, MWh summation, source-field precedence, renewable aggregation, and validation behavior.

### Internal browser evaluation

Internal checks covered:

- desktop rendering of the full six-view page;
- mobile rendering and responsive reflow;
- View 2 Previous, Play/Pause, Next, Reset, and slider behavior;
- View 3 normalized-source controls; and
- View 4 raw-MW versus separately normalized regional controls.

The six reproducible images under `report/screenshots/` document the default chart outputs. Internal browser checks establish that implemented controls render and respond; they do not substitute for target-audience comprehension testing.

### Data validation

The persisted validation report passes 10 of 11 checks. The failed required-values check records 25 missing demand rows, 25 missing net-generation rows, and **31 missing renewables and 31 missing generation-mix rows**. Arithmetic, coverage, timestamp continuity, source exclusion, archive integrity, and provenance checks pass. This limitation must remain visible in reporting.

## Revisions already supported by implementation evidence

| Evidence | Implemented response | Status |
|---|---|---|
| Hourly playback must not overrun a day | Clamp Previous/Next/interval values to the selected day’s first and last observation | Implemented and automated-test covered |
| DST days can differ from 24 local observations | Derive playback maximum from selected-day record count | Implemented |
| Raw scale can obscure shape | Offer independently normalized annual and regional modes with explicit percent-of-peak axes | Implemented and automated-test covered |
| Normalization can be misread | Keep absolute/raw-MW mode and label normalized output as percent of each series’ own peak | Implemented |
| Empty/invalid selections can mislead | Return annotated empty figures and filter unknown source identifiers | Implemented and automated-test covered |
| CV can divide by zero | Report CV as undefined when the mean is zero or unavailable | Implemented and automated-test covered |
| Missing values can be hidden by aggregation | Preserve gaps and display missing-value notices | Implemented |
| A portfolio does not always beat every component | Compare portfolio CV with each source and use conditional takeaway language | Implemented |
| Regional map points could imply boundaries | Label points as approximate references, not balancing-authority boundaries | Implemented |

## Human-testing queue

Two target-audience sessions are required using `evaluation/feedback_form.md`.

| Session | Status | Findings | Revision decision |
|---|---|---|---|
| Tester 1 | Pending | Not yet available | Not yet available |
| Tester 2 | Pending | Not yet available | Not yet available |

## Future revision-entry template

Append one row per evidence-based change; do not overwrite the pending record.

| Date | Evidence source | Problem observed | Decision | Change made | Verification |
|---|---|---|---|---|---|
|  | Tester 1 / Tester 2 / automated / browser |  | accept / defer / reject |  |  |
