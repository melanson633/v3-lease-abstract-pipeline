"""Lease extraction pipeline stage."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from leasegpt.constants import SCHEMA_VERSION
from leasegpt.errors import InputValidationError
from leasegpt.models import ExtractionBundle, LeaseDocument
from leasegpt.pipeline.llm_json import parse_json_from_text
from leasegpt.providers.base import LLMAdapter
from leasegpt.utils.io import utc_timestamp

_EXTRACTION_SYSTEM_RULES = """You are LeaseGPT extraction runtime.
Hard constraints:
- Single-tenant only: if documents contain multiple primary tenants, return all tenant candidates.
- Process documents in this order exactly as provided and apply supersession: OL -> CM -> A1..An -> other.
- Never invent facts. Use null and include pending_fields reasons when unavailable.
- For every populated business field, include traceability metadata with citation, confidence (0-1), validation_status.
- Citation format: DOC pPAGE REF (for example: OL p5 §4.1, A1 p2 §3).
- Date format in JSON: YYYY-MM-DD.
Return JSON only (no markdown fences).
"""


def _serialize_docs_for_prompt(documents: list[LeaseDocument]) -> str:
    blocks: list[str] = []
    for index, doc in enumerate(documents, start=1):
        header = [
            f"DOCUMENT {index}",
            f"path: {doc.path.name}",
            f"doc_code: {doc.doc_code}",
            f"order_index: {doc.order_index}",
        ]
        if doc.page_count is not None:
            header.append(f"page_count: {doc.page_count}")
        if doc.truncated and doc.truncation_note:
            header.append(f"note: {doc.truncation_note}")
        block = "\n".join(header) + "\n---\n" + doc.text
        blocks.append(block)
    return "\n\n==========\n\n".join(blocks)


def _build_prompt(schema_text: str, documents: list[LeaseDocument]) -> str:
    docs_blob = _serialize_docs_for_prompt(documents)
    return f"""{_EXTRACTION_SYSTEM_RULES}

Output JSON shape:
{{
  "tenant_candidates": ["..."],
  "lease_state": {{ ... }},
  "change_log": [ ... ],
  "pending_fields": [ ... ],
  "traceability": {{
    "extractedFieldsMetadata": {{
      "Field.Path": {{
        "citation": "OL p1 §1",
        "confidence": 1.0,
        "validation_status": "confirmed",
        "notes": null
      }}
    }}
  }},
  "diagnostics": {{
    "documents_processed": [{{"path": "...", "doc_code": "..."}}],
    "assumptions": ["..."],
    "warnings": ["..."]
  }}
}}

Use this canonical v4 schema for lease_state:
{schema_text}

Documents (already ordered for supersession):
{docs_blob}
"""


def _normalize_candidates(payload: dict[str, Any]) -> list[str]:
    candidates = payload.get("tenant_candidates")
    if not isinstance(candidates, list):
        candidates = []
    normalized = []
    for item in candidates:
        if isinstance(item, str) and item.strip():
            normalized.append(item.strip())
    # de-duplicate while preserving order
    seen = set()
    deduped: list[str] = []
    for value in normalized:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(value)
    return deduped


def _enforce_single_tenant(payload: dict[str, Any]) -> list[str]:
    tenant_candidates = _normalize_candidates(payload)
    lease_state = payload.get("lease_state") or {}
    party_tenant_name = (
        (lease_state.get("Parties") or {}).get("Tenant") or {}
    ).get("Name")
    if isinstance(party_tenant_name, str) and party_tenant_name.strip():
        if party_tenant_name.casefold() not in {c.casefold() for c in tenant_candidates}:
            tenant_candidates.append(party_tenant_name.strip())

    if len(tenant_candidates) > 1:
        raise InputValidationError(
            "Multiple tenant candidates detected. Please rerun with documents for one tenant only. "
            f"Detected: {', '.join(tenant_candidates)}"
        )
    return tenant_candidates


def _ensure_bundle_shape(payload: dict[str, Any], source_documents: list[str]) -> ExtractionBundle:
    lease_state = payload.get("lease_state")
    if not isinstance(lease_state, dict):
        raise InputValidationError("Extraction output missing required object: lease_state")

    metadata = lease_state.setdefault("Metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
        lease_state["Metadata"] = metadata
    metadata["SchemaVersion"] = metadata.get("SchemaVersion") or SCHEMA_VERSION
    extraction_meta = metadata.setdefault("Extraction", {})
    if not isinstance(extraction_meta, dict):
        extraction_meta = {}
        metadata["Extraction"] = extraction_meta
    extraction_meta["GenerationTimestamp"] = extraction_meta.get("GenerationTimestamp") or utc_timestamp()
    extraction_meta["SourceDocuments"] = extraction_meta.get("SourceDocuments") or source_documents
    extraction_meta["ExtractorVersion"] = extraction_meta.get("ExtractorVersion") or "leasegpt-runtime/0.1.0"
    metadata["LeaseStatus"] = metadata.get("LeaseStatus") or "Active"
    metadata["LeaseCurrency"] = metadata.get("LeaseCurrency") or "USD"

    change_log = payload.get("change_log")
    if not isinstance(change_log, list):
        change_log = []
    pending_fields = payload.get("pending_fields")
    if not isinstance(pending_fields, list):
        pending_fields = []
    traceability = payload.get("traceability")
    if not isinstance(traceability, dict):
        traceability = {"extractedFieldsMetadata": {}}
    if not isinstance(traceability.get("extractedFieldsMetadata"), dict):
        traceability["extractedFieldsMetadata"] = {}

    diagnostics = payload.get("diagnostics")
    if not isinstance(diagnostics, dict):
        diagnostics = {}

    tenants = _enforce_single_tenant(payload)
    return ExtractionBundle(
        lease_state=lease_state,
        change_log=change_log,
        pending_fields=pending_fields,
        traceability=traceability,
        tenant_candidates=tenants,
        diagnostics=diagnostics,
    )


def run_extraction(
    adapter: LLMAdapter,
    schema_text: str,
    documents: list[LeaseDocument],
) -> ExtractionBundle:
    prompt = _build_prompt(schema_text=schema_text, documents=documents)
    raw_response = adapter.generate_text(prompt)
    payload = parse_json_from_text(raw_response)
    return _ensure_bundle_shape(
        payload=payload,
        source_documents=[doc.path.name for doc in documents],
    )


def build_extraction_output(bundle: ExtractionBundle) -> dict[str, Any]:
    return {
        "lease_state": bundle.lease_state,
        "change_log": bundle.change_log,
        "pending_fields": bundle.pending_fields,
        "traceability": bundle.traceability,
    }


def load_schema_text(schema_file: Path) -> str:
    return schema_file.read_text(encoding="utf-8")
