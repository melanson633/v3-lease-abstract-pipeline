"""Shared runtime constants aligned to config/shared_constants.md."""

from __future__ import annotations

import re

SCHEMA_VERSION = "4.0.0"

VALIDATION_STATUSES = {"confirmed", "pending", "uncertain", "flagged", "missing"}

# DOC pPAGE REF where REF is optional trailing segment.
CITATION_REGEX = re.compile(
    r"^(OL|CM|A[1-9]|EX-[A-Z]|SL[1-9]) p\d+( .+)?$"
)

DOCUMENT_ORDER_PRIORITY = ("OL", "CM", "A1..An", "other")

RISK_MATERIALITY_ANNUAL_RENT = 250_000
