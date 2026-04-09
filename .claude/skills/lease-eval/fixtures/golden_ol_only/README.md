# Fixture: golden_ol_only

**ANONYMIZED: true**

## Intent
Smallest realistic `lease_state` that exercises the critical sections of the v4 schema without any amendments. Used to verify:
- Schema conformance on a clean OL-only extraction.
- Full citation + traceability coverage for every populated field.
- Empty `change_log` and `pending_fields` handled correctly.
- Verdict = PASS when run through `lease-eval` with no golden comparison.

## Synthetic source scenario
- **Document**: OL.pdf (9 pages), a straight-line 5-year retail lease.
- **Tenant**: Coastline Stationery LLC (Delaware LLC)
- **Landlord**: Harborview Plaza Owner LP (Delaware LP)
- **Premises**: 2,500 RSF ground-floor retail at 100 Harborview Plaza, Suite 104, Marina Bay, CA 90001. Building RSF = 85,000.
- **Term**: 60 months, 2025-06-01 through 2030-05-31. No free rent, no TI allowance, no guarantor.
- **Base rent**: $32.00/RSF Year 1, stepping $1.00/RSF each anniversary.
- **Additional rent**: Triple Net (NNN), pro-rata share 2.94%.
- **Security deposit**: $15,000 cash.
- **Renewal**: 1 option for 60 months at FMV, 270-day notice.
- **Use**: Retail sale of stationery, greeting cards, and gift items.

All values, names, and addresses are fictional.

## How to use
```
lease-eval CANDIDATE_JSON=fixtures/golden_ol_only/lease_state.json
```

Expected result: verdict = PASS, zero issues.
