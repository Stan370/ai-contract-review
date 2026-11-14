---
name: ai-contract-review
description: Find this year's contracts and invoices in a user-selected UGREEN NAS folder, extract key fields (counterparty, amount, dates), show an index table and exact copy plan for review, and after approval copy the files into a chosen archive folder with an index file. Use when users want a year-end or tax-season document archive without deleting or overwriting anything.
---

# Goal

Turn a messy NAS folder into a reviewed, searchable archive of the user's contracts and invoices for one year. The Skill extracts key fields into an index table, shows the exact plan, and only after the user approves, copies the files into the user's chosen archive folder and writes the index file. It never deletes or overwrites files.
# Required input

- One accessible contract file on the NAS, or a folder to search for contract files.
- The user's review focus, such as payment, term and renewal, termination, obligations, liability, indemnity, confidentiality, intellectual property, or data handling. If no focus is specified, review key commercial terms and potential ambiguities without judging legal validity.
- Optional output style, language, audience, and desired length. Default to concise, plain-language prose and tables rather than technical/legalese.

Do not request or include account credentials, keys, or unrelated personal data. Treat contract content as confidential and use only the user-authorized file(s). Ask the user to confirm the exact contract before analysis if a folder search finds multiple candidates.

Read [Review output and evidence rules](references/review-output.md) before producing the final report.

# Supported CLI capabilities

- [`ug-filesystem` `find`](#orchestration) — `file-agent` locates contract candidates in a user-selected folder. Use a shallow, bounded search; do not broaden it without permission.
- [`ug-document` `extract`](#orchestration) — `document-agent` extracts contract terms from the selected source using the catalog's `contract` schema.
- [`ug-knowledge` `collect-evidence`](#orchestration) — `knowledge-agent` conducts a separate evidence-collection pass against the same source and the initial claims, looking for support, contradiction, and missing evidence.
- [`ug-document` `reconcile`](#orchestration) — `document-agent` reconciles the original contract, initial extraction, and independent evidence report into a corrected result with unresolved discrepancies identified.

These are read-only capabilities. The parent Skill delegates NAS work to registered experts and does not perform NAS operations itself. Do not use document writing or save-text actions unless a separate user-approved save-to-NAS feature is added in a future version.

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`
- `ug-document` → `document-agent`
- `ug-knowledge` → `knowledge-agent`

# Orchestration

1. Confirm the user's scope, review focus, and presentation preference. If a folder was supplied, delegate a bounded `ug-filesystem` `find` to `file-agent` for documents under only that folder (`max-depth` 2, `limit` 20). Pass the actual returned candidate paths to the user and ask them to select the contract if more than one matches. Example: `delegate --target file-agent --instruction 'Search only the user-authorized folder for contract document candidates. Bound the search to depth 2 and 20 results. Return actual file paths/IDs, empty status, and errors; do not read, alter, or broaden scope.'`
2. Stop and report if no contract candidate is found. If exactly one candidate is found, confirm it with the user before analysis. For a supplied exact file, confirm that file and proceed.
3. Delegate initial extraction to `document-agent` using `ug-document` `extract`, the exact selected file, `schema=contract`, and a query requesting the user's focus plus key contract terms. Request each claim with exact source wording and page/section/paragraph locator when available; distinguish missing, ambiguous, and inferred data. Example: `delegate --target document-agent --instruction 'Extract the requested contract terms from the exact user-confirmed file using the contract schema. Return each claim with exact supporting wording and page/section/paragraph locator only when present in the source result. Mark missing or ambiguous terms and inferences explicitly; do not assess enforceability or invent citations.'`
4. Once extraction completes, delegate an independent evidence pass to `knowledge-agent` using `ug-knowledge` `collect-evidence`, the same exact file path, `full=true`, and a query containing the actual extracted claims and review focus. Ask it to locate support, contradiction, qualifications, exceptions, and evidence gaps for each material claim; return source locations only when available. This is a separate registered expert pass, not a claim that the system used a distinct AI model. Example: `delegate --target knowledge-agent --instruction 'Independently collect evidence from only the user-confirmed contract path for these extracted claims and review focus. For each claim, find supporting or contradicting source text, qualifications, exceptions, and gaps. Return actual evidence, source locations when available, coverage, and failures; do not provide legal advice or assume an unsupported claim is true.'`
5. After the evidence pass completes, delegate correction/reconciliation to `document-agent` using `ug-document` `reconcile` on the same contract. Pass only the actual extraction and evidence report returned by the earlier stages as downstream inputs. Ask for a corrected claim set, resolved contradictions, unresolved items, evidence locators, and confidence. Preserve disagreements that the source cannot resolve; do not turn absence of evidence into proof of absence. Example: `delegate --target document-agent --instruction 'Reconcile the exact user-confirmed contract against this completed initial extraction and this completed independent evidence report. Correct claims only when supported by the contract, include exact source wording and available page/section/paragraph locators, and list unresolved conflicts, missing evidence, inferences, and coverage limits. Do not invent text or citations and do not give legal advice.'`
6. Produce the final report from the reconciliation result only, following the [review output and evidence rules](references/review-output.md). Adapt wording, language, and length to the user's stated preference without omitting material uncertainty. Identify the source contract by its returned path/name, not by an invented title.

# Completion and failure

- **completed:** Report only findings present in the completed reconciliation result. Provide the source-evidence table, confidence, inferences, and unverified items. Make clear this is informational document review, not legal advice.
- **failed:** State which stage failed and its returned reason. Do not treat partial extraction as fully validated; if useful, offer to return it clearly labeled as unverified.
- **cancelled:** Stop the workflow and report cancellation. Do not continue to later review passes.
- **waiting_user:** Ask only for the missing scope, candidate selection, review focus, or style choice. Continue only after the user responds.
- **waiting_approval:** Stop until approval completes. The selected actions are read-only, but honor any runtime approval state and never bypass it.
- **Empty folder or no contract candidate:** If no results or no contract candidate are returned, report that and stop. Do not substitute a different document.
- **Multiple candidates:** Ask the user to select the exact contract; do not review every file by default.
- **Missing permission, locked, scanned, or unreadable file:** Report the inaccessible source or extraction limitation. Do not bypass access controls or fabricate OCR text. Ask for an accessible or text-readable copy.
- **Long or oversized contract / incomplete coverage:** Preserve the expert's coverage warnings, do not claim a complete review, and ask the user to narrow the requested focus or provide a manageable section.
- **Contradictory claims or unlocated citation:** Keep the discrepancy unresolved and flag it for human review. Never invent page numbers, clause numbers, quotations, or confidence.
- **Legal interpretation requested:** Explain that the Skill summarizes and organizes what the document says but cannot determine enforceability, jurisdiction-specific legal effect, or whether the user should sign. Suggest qualified legal counsel for those decisions.
- **User declines or changes scope:** Stop. A changed document or review scope requires new confirmation and fresh passes.

## Disclosure

- **Functionality developed for the Hackathon:** A new three-pass contract review orchestration: contract extraction, separate evidence collection, and correction/reconciliation, followed by a citation-first, confidence-labeled report. The first and third passes use the registered `document-agent`; the evidence pass uses the separate registered `knowledge-agent`. The catalog identifies one expert per CLI, so this is role-separated orchestration, not three guaranteed independent models.
- **Third-party components and licenses:** No third-party libraries, scripts, binaries, or external downloads are bundled. The workflow depends on UGREEN's published `ug-filesystem`, `ug-document`, and `ug-knowledge` capabilities and registered experts. The supplied capability catalog does not specify UGREEN product/API license terms; verify applicable terms before distribution.
- **Design references:** [invoice-organizer Skill on GitHub](https://github.com/davila7/claude-code-templates/blob/main/cli-tool/components/skills/productivity/invoice-organizer/SKILL.md) It informed the problem framing and evidence-first presentation only; this Skill is original and includes no third-party code or copied Skill text.
