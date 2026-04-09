# Fixture: golden_ol_a1

**ANONYMIZED: true**

## Intent
Minimal fixture that exercises `change_log` coherence checks. Builds on `golden_ol_only` by layering an Amendment 1 that extends the term and adds a TI allowance. Used to verify:
- Schema conformance on an amended `lease_state`.
- Change-log coherence: every entry's `new_value` matches the current `lease_state` value for the most recent change on that path.
- Citation format accepts `A1 pN §X` document codes.
- Traceability metadata carries amendment citations alongside OL citations.

## Synthetic source scenario
Starts from the `golden_ol_only` baseline, same parties and premises. Layers:
- **Document**: A1.pdf (2 pages), effective 2027-01-15. First Amendment to Lease.
- **Term extension**: +24 months. New expiration 2032-05-31. TermMonths 60 → 84.
- **Rent schedule**: Years 6 and 7 added at $37.00/RSF and $38.00/RSF (continuing the $1.00/RSF annual step). Years 1-5 unchanged.
- **TI allowance**: $50,000 ($20.00/RSF) added for store refresh, to be drawn against tenant improvement work completed before 2028-06-01.
- No other changes — §5 (additional rent), §6 (security deposit), §8 (renewal option), etc. carry forward unchanged.

All values, names, and addresses are fictional.

## How to use
```
lease-eval CANDIDATE_JSON=fixtures/golden_ol_a1/lease_state.json
```

Expected result: verdict = PASS, zero issues. The six change_log entries must all reconcile against the current `lease_state`.
