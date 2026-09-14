"""Tests for the provider-neutral Wiki generation prompt contract."""

from __future__ import annotations

import pytest

from app.prompts import (
    MISSING_INFORMATION_MARKER,
    REQUIRED_WIKI_HEADINGS,
    WIKI_GENERATION_INSTRUCTIONS,
    WIKI_MARKDOWN_SKELETON,
    WikiStructureIssueCode,
    build_wiki_generation_prompt,
    validate_wiki_markdown,
)


def make_wiki_markdown(headings: tuple[str, ...] = REQUIRED_WIKI_HEADINGS) -> str:
    sections = "\n\n".join(f"{heading}\nเนื้อหาจากเอกสาร" for heading in headings)
    return f"# ระบบคลังปริญญานิพนธ์\n\n{sections}"


def issue_codes(markdown: str) -> list[WikiStructureIssueCode]:
    return [issue.code for issue in validate_wiki_markdown(markdown).issues]


def test_contract_contains_all_required_headings_in_stable_order() -> None:
    positions = [WIKI_MARKDOWN_SKELETON.index(heading) for heading in REQUIRED_WIKI_HEADINGS]

    assert len(REQUIRED_WIKI_HEADINGS) == 7
    assert positions == sorted(positions)
    assert validate_wiki_markdown(make_wiki_markdown()).is_valid


def test_validator_detects_missing_required_heading() -> None:
    markdown = make_wiki_markdown(REQUIRED_WIKI_HEADINGS[:-1])
    validation = validate_wiki_markdown(markdown)

    assert not validation.is_valid
    assert WikiStructureIssueCode.MISSING_REQUIRED_HEADING in issue_codes(markdown)
    assert validation.issues[0].heading == REQUIRED_WIKI_HEADINGS[-1]


def test_validator_detects_required_headings_out_of_order() -> None:
    reordered = list(REQUIRED_WIKI_HEADINGS)
    reordered[1], reordered[2] = reordered[2], reordered[1]

    assert WikiStructureIssueCode.REQUIRED_HEADINGS_OUT_OF_ORDER in issue_codes(
        make_wiki_markdown(tuple(reordered))
    )


def test_validator_detects_duplicate_required_heading() -> None:
    headings = (*REQUIRED_WIKI_HEADINGS[:2], REQUIRED_WIKI_HEADINGS[1], *REQUIRED_WIKI_HEADINGS[2:])

    assert WikiStructureIssueCode.DUPLICATE_REQUIRED_HEADING in issue_codes(
        make_wiki_markdown(headings)
    )


def test_prompt_separates_and_preserves_supplied_thai_source_text() -> None:
    source = "ชื่อโครงงาน: ระบบค้นคืนข้อมูล\nเทคโนโลยี: Python และ PyMuPDF"

    prompt = build_wiki_generation_prompt(source)

    assert source in prompt
    assert f"<SOURCE_DOCUMENT>\n{source}\n</SOURCE_DOCUMENT>" in prompt
    assert prompt.index("SOURCE-GROUNDING RULES") < prompt.index("<SOURCE_DOCUMENT>")


def test_prompt_contains_anti_hallucination_rules() -> None:
    instructions = WIKI_GENERATION_INSTRUCTIONS.lower()

    assert "use only information supported" in instructions
    assert "do not invent" in instructions
    assert "fake references" in instructions
    assert "summarize" in instructions
    assert "markdown only" in instructions
    assert MISSING_INFORMATION_MARKER in WIKI_GENERATION_INSTRUCTIONS


def test_prompt_rejects_empty_extracted_text() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        build_wiki_generation_prompt("  \n")
