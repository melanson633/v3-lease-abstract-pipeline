"""Implementation of the lease-portfolio skill."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from leasegpt.utils.dates import parse_date, today_utc


@dataclass(slots=True)
class PortfolioResult:
    summary_markdown: str
    manifest: dict[str, Any]


def _identity_key(lease_state: dict[str, Any]) -> str:
    tenant = (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")) or "unknown_tenant"
    address = ((lease_state.get("Premises") or {}).get("Address")) or "unknown_address"
    original = ((lease_state.get("Dates") or {}).get("OriginalLeaseDate")) or "unknown_date"
    return f"{tenant}|{address}|{original}"


def _current_annual_rent(lease_state: dict[str, Any], reference_date: date) -> float | None:
    schedule = (((lease_state.get("Financials") or {}).get("BaseRent") or {}).get("Schedule")) or []
    if not isinstance(schedule, list):
        return None
    nearest_future = None
    for row in schedule:
        if not isinstance(row, dict):
            continue
        annual = row.get("annualAmount")
        if annual is None:
            continue
        start = parse_date(row.get("startDate"))
        end = parse_date(row.get("endDate"))
        if start and end and start <= reference_date <= end:
            return float(annual)
        if start and start > reference_date and nearest_future is None:
            nearest_future = float(annual)
    if nearest_future is not None:
        return nearest_future
    for row in reversed(schedule):
        if isinstance(row, dict) and row.get("annualAmount") is not None:
            return float(row["annualAmount"])
    return None


def build_portfolio(
    bundles: list[dict[str, Any]],
    reference_date: date | None = None,
) -> PortfolioResult:
    reference = reference_date or today_utc()
    warnings: list[dict[str, Any]] = []
    per_lease_inputs: list[dict[str, Any]] = []
    if len(bundles) < 2:
        raise ValueError("insufficient_portfolio_size: at least two leases are required for portfolio analytics.")

    identity_seen: dict[str, int] = {}
    concentration_denominator = 0.0
    concentration_numerators: dict[str, float] = {}
    expiration_ladder = {"<1 year": 0, "1-2 years": 0, "3-5 years": 0, "6-10 years": 0, ">10 years": 0}
    rent_roll_by_year: dict[int, float] = {}
    total_ti = 0.0
    total_security = 0.0
    weighted_sum = 0.0
    weight_total = 0.0

    for bundle in bundles:
        lease_state = bundle.get("lease_state") or {}
        tenant = (((lease_state.get("Parties") or {}).get("Tenant") or {}).get("Name")) or "Unknown Tenant"
        key = _identity_key(lease_state)
        if key in identity_seen:
            identity_seen[key] += 1
            key = f"{key}#{identity_seen[key]}"
            warnings.append({"issue": "duplicate_identity_key", "lease_key": key})
        else:
            identity_seen[key] = 1

        rsf = ((lease_state.get("Premises") or {}).get("RSF"))
        expiration = parse_date(((lease_state.get("Dates") or {}).get("ExpirationDate")))
        annual_rent = _current_annual_rent(lease_state, reference)
        ti_amount = (((lease_state.get("Financials") or {}).get("TIAllowance")) or {}).get("Amount")
        sec_amount = (((lease_state.get("Financials") or {}).get("SecurityDeposit")) or {}).get("Amount")
        recovery_type = (((lease_state.get("Financials") or {}).get("AdditionalRent")) or {}).get("RecoveryType")

        if isinstance(ti_amount, (int, float)):
            total_ti += float(ti_amount)
        if isinstance(sec_amount, (int, float)):
            total_security += float(sec_amount)

        remaining_years = None
        if expiration:
            remaining_years = max((expiration - reference).days / 365.25, 0.0)
            if remaining_years < 1:
                expiration_ladder["<1 year"] += 1
            elif remaining_years < 3:
                expiration_ladder["1-2 years"] += 1
            elif remaining_years < 6:
                expiration_ladder["3-5 years"] += 1
            elif remaining_years <= 10:
                expiration_ladder["6-10 years"] += 1
            else:
                expiration_ladder[">10 years"] += 1
        else:
            warnings.append({"issue": "missing_expiration_date", "lease_key": key})

        weight = None
        weight_basis = None
        if isinstance(rsf, (int, float)) and rsf > 0:
            weight = float(rsf)
            weight_basis = "rsf"
        elif isinstance(annual_rent, (int, float)) and annual_rent > 0:
            weight = float(annual_rent)
            weight_basis = "annual_rent"
        else:
            warnings.append({"issue": "missing_rsf_and_rent_weight", "lease_key": key})

        if remaining_years is not None and weight is not None:
            weighted_sum += remaining_years * weight
            weight_total += weight

        if isinstance(annual_rent, (int, float)):
            concentration_denominator += float(annual_rent)
            concentration_numerators[tenant] = concentration_numerators.get(tenant, 0.0) + float(annual_rent)
        else:
            warnings.append({"issue": "missing_rent_schedule", "lease_key": key})

        schedule = (((lease_state.get("Financials") or {}).get("BaseRent")) or {}).get("Schedule") or []
        if isinstance(schedule, list):
            for row in schedule:
                if not isinstance(row, dict):
                    continue
                start = parse_date(row.get("startDate"))
                annual = row.get("annualAmount")
                if start and isinstance(annual, (int, float)):
                    rent_roll_by_year[start.year] = rent_roll_by_year.get(start.year, 0.0) + float(annual)

        per_lease_inputs.append(
            {
                "lease_key": key,
                "tenant_name": tenant,
                "rsf": rsf,
                "expiration_date": expiration.isoformat() if expiration else None,
                "remaining_term_years": round(remaining_years, 6) if remaining_years is not None else None,
                "current_annual_base_rent": annual_rent,
                "ti_allowance_amount": ti_amount,
                "security_deposit_amount": sec_amount,
                "recovery_type": recovery_type,
                "weight_basis": weight_basis,
                "weight_value": weight,
            }
        )

    walt = weighted_sum / weight_total if weight_total else None
    concentration = []
    if concentration_denominator > 0:
        for tenant, amount in sorted(concentration_numerators.items(), key=lambda item: item[1], reverse=True):
            concentration.append(
                {
                    "tenant": tenant,
                    "annual_rent": round(amount, 2),
                    "share_pct": round((amount / concentration_denominator) * 100, 4),
                }
            )
    top_3_share = round(sum(item["share_pct"] for item in concentration[:3]), 4) if concentration else 0.0

    summary_lines = [
        f"Portfolio size: {len(bundles)} leases",
        f"Reference date: {reference.isoformat()}",
        (
            f"WALT: {walt:.3f} years (weighted_sum={weighted_sum:.6f}, weight_base={weight_total:.6f})"
            if walt is not None
            else "WALT: unavailable (insufficient weighting inputs)"
        ),
        "Expiration ladder: " + ", ".join(f"{bucket}={count}" for bucket, count in expiration_ladder.items()),
        (
            f"Top tenant concentration: {concentration[0]['tenant']} at {concentration[0]['share_pct']:.2f}%"
            if concentration
            else "Top tenant concentration: unavailable"
        ),
        f"Top-3 concentration share: {top_3_share:.2f}%",
        f"Aggregate TI allowance: ${total_ti:,.2f}",
        f"Aggregate security deposits: ${total_security:,.2f}",
    ]
    if warnings:
        summary_lines.append("Caveats: " + "; ".join(w["issue"] for w in warnings[:5]))

    manifest = {
        "reference_date": reference.isoformat(),
        "lease_count": len(bundles),
        "walt": {
            "value_years": round(walt, 6) if walt is not None else None,
            "weighted_sum": round(weighted_sum, 6),
            "weight_base": round(weight_total, 6),
            "weighting_method": "rsf_with_annual_rent_fallback",
        },
        "expiration_ladder": expiration_ladder,
        "rent_roll_by_year": {str(year): round(total, 2) for year, total in sorted(rent_roll_by_year.items())},
        "tenant_concentration": {
            "denominator_annual_rent": round(concentration_denominator, 2),
            "rows": concentration,
            "top_3_share_pct": top_3_share,
        },
        "aggregate_exposure": {
            "total_ti_allowance": round(total_ti, 2),
            "total_security_deposit": round(total_security, 2),
        },
        "per_lease_inputs": per_lease_inputs,
        "warnings": warnings,
    }

    return PortfolioResult(summary_markdown="\n".join(summary_lines) + "\n", manifest=manifest)
