#!/usr/bin/env python3
"""Rebuild the AI Contract Review proposal PDF and initial Skill ZIP.

The Skill ZIP intentionally contains only SKILL.md and its linked Markdown
reference. This helper script remains outside the Skill package.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


SUBMISSION_DIR = Path(__file__).resolve().parent
SKILL_DIR = SUBMISSION_DIR / "ai-contract-review"
PROPOSAL_PATH = SUBMISSION_DIR / "ai-contract-review-proposal.pdf"
PACKAGE_PATH = SUBMISSION_DIR / "ai-contract-review-initial-skill.zip"
PACKAGE_FILES = (
    ("SKILL.md", SKILL_DIR / "SKILL.md"),
    ("references/review-output.md", SKILL_DIR / "references/review-output.md"),
)
MAX_PROPOSAL_BYTES = 1_000_000
MAX_PACKAGE_BYTES = 10_000_000
MAX_ANSWER_WORDS = 500

ANSWERS = (
    (
        "One sentence: What does the Skill do?",
        "AI Contract Review extracts key terms from a NAS contract, verifies each "
        "against source evidence, and returns a cited, corrected review that "
        "flags unverified items.",
    ),
    (
        "Who is the target user and problem?",
        "Small-business owners, operations staff, and legal-support teams must "
        "find payment, term, and termination clauses quickly, but cannot safely "
        "rely on uncited, single-pass AI summaries.",
    ),
    (
        "What is your proposed solution?",
        "A read-only, three-pass workflow: extract terms, independently gather "
        "supporting or conflicting evidence, then reconcile both into a concise, "
        "source-grounded report.",
    ),
    (
        "What is the Core User Flow?",
        "The user picks a contract and review focus. (1) An expert extracts "
        "terms. (2) A second expert gathers evidence. (3) A document expert "
        "corrects and reconciles claims. (4) The user receives a findings table "
        "with citations, confidence, inferences, and unverified items.",
    ),
    (
        "What substantive difference does your idea offer compared with existing "
        "tools or conventional AI solutions?",
        "Typical AI tools present one summary as authoritative. This Skill "
        "separates extraction, evidence checking, and correction; keeps "
        "unresolved issues visible; and never invents citations. It supports a "
        "human decision-maker and does not replace counsel.",
    ),
    (
        "Which UGREEN AI NAS capabilities will be used, and at which step?",
        "Step 1: ug-filesystem find locates candidate contracts. Step 2: "
        "ug-document extract applies the contract schema. Step 3: ug-knowledge "
        "collect-evidence checks claims against the selected contract. Step 4: "
        "ug-document reconcile corrects claims and reports unresolved "
        "discrepancies.",
    ),
    (
        "What was your technical approach?",
        "The parent Skill delegates to catalog-registered experts: file-agent "
        "(bounded search), document-agent (extraction, reconciliation), and "
        "knowledge-agent (separate evidence pass). Inputs: an authorized NAS "
        "file or folder, review focus, and optional language or style. All "
        "selected actions are read-only and touch only user-selected files. The "
        "catalog does not expose model choice or runtime model identity. No "
        "credentials are requested or stored; nothing is shared externally or "
        "written to the NAS.",
    ),
    (
        "What is the current development status?",
        "Built: the Skill, a linked output reference, and a package draft, which "
        "pass the supplied static checker. Not built or tested: NAS execution, "
        "extraction quality, citation locator availability, expert handoffs, and "
        "runtime model and data handling. All require finalist-device "
        "validation.",
    ),
    (
        "What is your final validation plan?",
        "Core 1: extract payment, term, and termination clauses from a readable "
        "contract; verify every citation against the source. Core 2: request a "
        "field absent from the contract; confirm it is marked \"not found\". "
        "Edge: conflicting clauses, or a locked or scanned file, must yield an "
        "explicit unresolved limitation, never a fabricated citation.",
    ),
    (
        "Are there any known limitations of your Project?",
        "document-agent handles both extraction and reconciliation, so three "
        "independent models cannot be guaranteed. Page or section locators and "
        "scanned-document coverage may be unavailable. Results depend on UGREEN "
        "experts, NAS permissions, file readability, and runtime model "
        "behavior. This is not legal advice and cannot judge enforceability or "
        "whether to sign. Third-party components: none bundled; only UGREEN "
        "catalog capabilities are used (license terms not stated in the "
        "catalog; to be verified).",
    ),
)

DISCLOSURES = (
    "THIRD-PARTY COMPONENTS AND LICENSES (excluded from the ten-response word count)",
    "No third-party libraries, scripts, binaries, or external downloads are "
    "bundled. The Skill uses UGREEN-published ug-filesystem, ug-document, and "
    "ug-knowledge capabilities and registered experts. The supplied capability "
    "catalog does not state applicable UGREEN product/API license terms; verify "
    "them before distribution.",
    "",
    "AI TOOL DISCLOSURE (outside the ten substantive responses)",
    "Claude code",
)


def answer_word_count() -> int:
    substantive_text = " ".join(answer for _, answer in ANSWERS)
    return len(re.findall(r"\b[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*\b", substantive_text))


def build_proposal_text() -> str:
    count = answer_word_count()
    if count > MAX_ANSWER_WORDS:
        raise ValueError(
            f"The ten substantive answers contain {count} words; "
            f"the maximum is {MAX_ANSWER_WORDS}."
        )

    lines = ["AI CONTRACT REVIEW — PROJECT PROPOSAL", ""]
    for number, (question, answer) in enumerate(ANSWERS, start=1):
        lines.extend((f"{number}. {question}", answer, ""))
    lines.extend(DISCLOSURES)
    lines.extend(("", f"Ten-response word count: {count} (maximum 500)."))
    return "\n".join(lines)


def make_proposal_pdf() -> None:
    cupsfilter = shutil.which("cupsfilter")
    if not cupsfilter:
        raise RuntimeError(
            "PDF generation requires the macOS cupsfilter command, which was "
            "not found on PATH."
        )

    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".txt", delete=False
    ) as source_file:
        source_file.write(build_proposal_text())
        source_path = Path(source_file.name)

    try:
        with PROPOSAL_PATH.open("wb") as output_file:
            subprocess.run(
                [
                    cupsfilter,
                    "-i",
                    "text/plain",
                    "-m",
                    "application/pdf",
                    str(source_path),
                ],
                stdout=output_file,
                check=True,
                stderr=subprocess.PIPE,
            )
    finally:
        source_path.unlink(missing_ok=True)

    if PROPOSAL_PATH.stat().st_size > MAX_PROPOSAL_BYTES:
        raise ValueError(f"Proposal PDF exceeds {MAX_PROPOSAL_BYTES} bytes.")


def make_skill_zip() -> None:
    missing = [str(path) for _, path in PACKAGE_FILES if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required Skill package files are missing: " + ", ".join(missing))

    with zipfile.ZipFile(
        PACKAGE_PATH, "w", compression=zipfile.ZIP_DEFLATED
    ) as package:
        for archive_name, source_path in PACKAGE_FILES:
            package.write(source_path, arcname=archive_name)

    with zipfile.ZipFile(PACKAGE_PATH) as package:
        expected_names = {archive_name for archive_name, _ in PACKAGE_FILES}
        actual_names = set(package.namelist())
        if actual_names != expected_names:
            raise ValueError(f"Unexpected ZIP contents: {sorted(actual_names)}")
        if any(not name.endswith(".md") for name in actual_names):
            raise ValueError("The Skill ZIP may contain Markdown files only.")
        if any(info.file_size > 1_000_000 for info in package.infolist()):
            raise ValueError("A Skill ZIP file exceeds the 1 MB per-file limit.")

    if PACKAGE_PATH.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError(f"Skill ZIP exceeds {MAX_PACKAGE_BYTES} bytes.")


def main() -> None:
    make_proposal_pdf()
    make_skill_zip()
    print(f"Proposal word count: {answer_word_count()}")
    print(f"Proposal PDF: {PROPOSAL_PATH} ({PROPOSAL_PATH.stat().st_size:,} bytes)")
    print(f"Initial Skill ZIP: {PACKAGE_PATH} ({PACKAGE_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
