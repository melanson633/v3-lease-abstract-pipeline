# Abstraction Procedure (Refined)

## Role
This procedure guides **shortcut.ai_cre** when generating a polished Lease Abstract from a validated `lease_state` and its associated `change_log`. It emphasizes clarity, readability, and decision-readiness for different audiences and property types, while faithfully representing the current lease state and history.

## Inputs
- `lease_state`: The final structured JSON produced by the extraction procedure, representing the current state of the lease. It must have validation status `confirmed` or `pending` (with acknowledged gaps).
- `change_log`: The list of historical modifications captured during extraction.
- `property_type`: One of `Office`, `Retail`, `Industrial`, or other supported types. Determines emphasis areas and metrics. **If not provided, ask the user -- do not silently default.**
- `audience`: One of `Executive`, `AssetManagement`, `PropertyManagement`, `Legal`, `Investor/Finance`, `Compliance/Regulatory`, `Marketing/Leasing`, or `Custom`. Determines detail level and narrative tone. **If not provided, ask the user -- do not silently default.**
- `need_PM_block` (optional, default `true`): Whether to include a detailed Property Management responsibility matrix.
- `exec_only` (optional, default `false`): If `true`, generate only the one-page Executive Fact Sheet.
- `output_type` (optional): Desired format -- `markdown` or `pdf`. If `pdf` is requested, a conversion script will be invoked after generating the markdown.

### Custom Audience Handling
If the user specifies `Custom` audience:
- Fall back to the generic template structure.
- Ask the user which emphasis areas matter most (e.g., "financial terms", "operational details", "legal provisions").
- Adjust section depth accordingly.

## Output
- `Lease Abstract`: A markdown document (converted to PDF if requested) that presents a concise summary of the lease, tailored to the specified property type and audience, incorporating change highlights and citations.

**Date format rules:** See `Configuration/shared_constants.md` (JSON uses `YYYY-MM-DD`; abstracts display `MM-DD-YYYY`).

## Workflow

### 1. Pre-Flight Validation
1. **Validate Inputs**: Confirm that `property_type` and `audience` are provided; if not, **ask the user** (do not silently default). Check that `lease_state` has been validated.
2. **Check Completeness**: Confirm that all key sections needed for the chosen audience can be derived from `lease_state`. If critical data is missing, stop and inform the user.
3. **Summarize Change Log**: Identify the most significant changes to highlight in the narrative. Significance algorithm:
   - **High significance** (always highlight): rent changes, term changes (extensions/reductions), option additions/removals, security deposit changes
   - **Medium significance** (highlight if material): maintenance responsibility shifts, insurance requirement changes, assignment/subletting modifications
   - **Low significance** (mention in change log table only): administrative updates, notice address changes, minor clarifications

### 2. Template Selection & Layout
1. **Select Base Template**: Choose an outline based on `property_type`:
   - *Office*: Emphasize parking ratios, after-hours HVAC, expansion rights, business hours.
   - *Retail*: Emphasize percentage rent, co-tenancy requirements, exclusive uses, foot traffic drivers.
   - *Industrial*: Emphasize loading capacities, power supply, environmental conditions, ceiling height.
   - *Other*: Fall back to a generic template and ask the user for custom emphasis areas.
2. **Audience Customization**:
   - *Executive*: One-page summary focusing on critical metrics, key dates, rent structure, options and major risks/opportunities.
   - *Asset Management*: Detailed financial analysis, rent schedule table, escalation assumptions and ROI context.
   - *Property Management*: Detailed responsibility matrix, maintenance schedules, vendor requirements and operational guidance.
   - *Legal*: Emphasize compliance flags, default and remedy provisions, liabilities and dispute resolution mechanisms.
   - *Investor/Finance*: Highlight cash flows, rent escalation trends, pro-rata shares and valuation impacts.
   - *Compliance/Regulatory*: Focus on accounting standards (ASC 842, IFRS 16), environmental compliance and municipal obligations.
   - *Marketing/Leasing*: Focus on tenant mix, co-tenancy clauses, exclusives and potential synergy with surrounding tenants.
   - *Custom*: Use generic template + ask user for emphasis areas.
3. **Apply `exec_only` and `need_PM_block` Flags**: If `exec_only` is `true`, limit output to the Executive Fact Sheet. If `need_PM_block` is `false`, omit the detailed property management responsibilities table.

### 3. Content Generation
1. **Executive Fact Sheet** (Page 1):
   - Compose a concise narrative (≤400 words) summarizing the lease basics: parties, property address, term, lease structure, rent overview and key options. Highlight any significant amendments or changes derived from the `change_log`.
   - Create a **Metrics Table** with columns `Metric`, `Value` and `Citation`. Include lease execution date, commencement date, expiration date, RSF, pro-rata share, current base rent, rent structure, security deposit, options, guarantor and compliance flags. Pull values from `lease_state` and citations from `change_log`.
   - Conclude the page with a compliance snapshot or highlights section, mentioning flags or special provisions.
   - Insert a form feed (`\f`) after Page 1.

2. **Thematic Sections** (Pages 2+): Generate up to seven sections, ordered per `style_guide_markdown.md` section 2:
   1. **Lease Fundamentals**: Parties, premises description, key dates and amendment summary.
   2. **Rent & Security**: Term length, detailed rent schedule with escalations, additional rent structure, security deposit, late fees and holdover provisions.
   3. **Additional Rent / Expenses**: Recovery type, pro-rata share, CAM charges, expense recoveries, caps, billing cycle.
   4. **Options**: Renewal terms, expansion/contraction rights, termination options, ROFO/ROFR.
   5. **Use / Operating Covenants**: Permitted uses, restrictions, operating hours, parking, tenant improvements, alteration rights, assignment/subletting.
   6. **Maintenance & Repairs**: Landlord vs. tenant responsibility matrix (if `need_PM_block` is `true`), HVAC terms, insurance requirements, utilities obligations.
   7. **Other Key Provisions / Open Items**: Environmental obligations, SNDA/estoppel, force majeure, governing law, defaults/remedies, amendments & change log table.

3. **Highlight Changes**: Where the `change_log` reveals major updates (e.g., rent increases, extended term), include call-out bullets to draw attention. Clearly state the previous value and the updated value, with effective dates.

4. **Confidence Score Display**: For fields with confidence < 0.7, append a confidence indicator in the abstract (e.g., `[confidence: 0.6]`) so the reader knows which values need verification.

5. **Formatting Standards**: Use Markdown headings (`##`, `###`) for sections. Use tables for schedules and responsibility matrices. Display calculations inline where helpful (e.g., "Current base rent of $24.50/RSF annually ($2.04/RSF monthly)"). Maintain consistent currency formatting and date format (`MM-DD-YYYY`). Provide a blank line after each table.

### 4. Validation & Quality Assurance
1. **Cross-Check Data**: Ensure that every figure in the abstract matches the corresponding value in `lease_state` and is backed by a citation.
2. **Narrative Consistency**: Review the narrative for clarity and cohesion. Avoid legal jargon unless the audience is `Legal`. Explain unusual clauses or deviations from market norms.
3. **Citation Completeness**: Confirm that each table entry and narrative fact includes a citation. If a citation is missing, search `lease_state` and `change_log` or flag the omission.
4. **Self-Check**: At the end of the document, perform a self-check statement indicating that the abstract accurately reflects the lease_state, that all calculations were validated, and that the content is appropriate for the specified audience.

### 5. Output & Conversion
1. **Markdown Deliverable**: Provide the lease abstract in a fenced `markdown` block. Conclude with a self-check statement.
2. **PDF Conversion** (optional): If `output_type` is `pdf`, follow `render_procedure_pdf.md` to convert. Provide the resulting PDF file to the user.
3. **Error Handling**: If the abstract cannot be generated due to missing critical data or validation failures, produce a markdown error report detailing the issues and recommended actions.
