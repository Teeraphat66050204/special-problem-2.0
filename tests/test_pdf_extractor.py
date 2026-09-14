"""Tests for digital PDF text-layer extraction."""

from __future__ import annotations

from io import BytesIO

import fitz
import pytest

from app.services import pdf_extractor
from app.services.pdf_extractor import (
    EmptyPdfError,
    EncryptedPdfError,
    InvalidPdfError,
    WarningCode,
    extract_pdf,
    normalize_text,
)


def make_pdf(*page_texts: str | None) -> bytes:
    document = fitz.open()
    try:
        for text in page_texts:
            page = document.new_page()
            if text is not None:
                page.insert_text((72, 72), text)
        return document.tobytes()
    finally:
        document.close()


def make_encrypted_pdf() -> bytes:
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "Protected text")
        return document.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner-password",
            user_pw="user-password",
        )
    finally:
        document.close()


def test_extracts_valid_digital_pdf_from_path(tmp_path) -> None:
    pdf_path = tmp_path / "project.pdf"
    pdf_path.write_bytes(make_pdf("Digital project text"))

    result = extract_pdf(pdf_path)

    assert result.page_count == 1
    assert result.full_text == "Digital project text"
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "Digital project text"
    assert result.warnings == ()


def test_extracts_all_pages_from_file_like_input() -> None:
    source = BytesIO(make_pdf("First page", "Second page", "Third page"))
    source.seek(5)

    result = extract_pdf(source)

    assert result.page_count == 3
    assert [page.text for page in result.pages] == [
        "First page",
        "Second page",
        "Third page",
    ]
    assert result.full_text == "First page\n\nSecond page\n\nThird page"
    assert source.tell() == 5


def test_blank_page_is_preserved_and_warned_about() -> None:
    result = extract_pdf(BytesIO(make_pdf("Text page", None)))

    assert result.page_count == 2
    assert result.pages[1].page_number == 2
    assert result.pages[1].text == ""
    assert len(result.warnings) == 1
    assert result.warnings[0].code is WarningCode.PAGE_HAS_NO_TEXT
    assert result.warnings[0].page_number == 2


def test_all_blank_pages_add_document_warning() -> None:
    result = extract_pdf(BytesIO(make_pdf(None, None)))

    assert result.full_text == ""
    assert [warning.code for warning in result.warnings] == [
        WarningCode.PAGE_HAS_NO_TEXT,
        WarningCode.PAGE_HAS_NO_TEXT,
        WarningCode.DOCUMENT_HAS_NO_TEXT,
    ]


def test_invalid_pdf_raises_clear_exception() -> None:
    with pytest.raises(InvalidPdfError, match="not a valid readable PDF"):
        extract_pdf(BytesIO(b"this is not a pdf"))


def test_encrypted_pdf_raises_clear_exception() -> None:
    with pytest.raises(EncryptedPdfError, match="requires a password"):
        extract_pdf(BytesIO(make_encrypted_pdf()))


def test_zero_page_pdf_raises_clear_exception(monkeypatch) -> None:
    class EmptyDocument:
        needs_pass = False
        page_count = 0

        def close(self) -> None:
            pass

    monkeypatch.setattr(pdf_extractor, "_open_pdf", lambda source: EmptyDocument())

    with pytest.raises(EmptyPdfError, match="contains no pages"):
        pdf_extractor.extract_pdf(BytesIO(b"unused by patched opener"))


def test_normalization_is_conservative() -> None:
    decomposed = "Cafe\u0301"
    thai_text = "ภาษาไทย"
    raw = f"\ufeff{decomposed}\t\t  {thai_text}\r\n\r\n\r\nnext\u200b line  "

    assert normalize_text(raw) == f"Caf\u00e9 {thai_text}\n\nnext\u200b line"


def test_normalization_joins_wrapped_prose_and_preserves_paragraphs() -> None:
    raw = (
        "This deliberately long sentence resembles a wrapped line and\n"
        "continues on the following line.\n\n"
        "A separate paragraph remains separate."
    )

    assert normalize_text(raw) == (
        "This deliberately long sentence resembles a wrapped line and "
        "continues on the following line.\n\n"
        "A separate paragraph remains separate."
    )


def test_normalization_joins_obvious_hyphenated_wrap() -> None:
    raw = "This deliberately long sentence ends with a docu-\nment boundary."

    assert normalize_text(raw) == ("This deliberately long sentence ends with a document boundary.")


def test_normalization_preserves_short_structural_line_breaks() -> None:
    assert normalize_text("Section title\nsubtitle\n\nParagraph") == (
        "Section title\nsubtitle\n\nParagraph"
    )


def test_normalization_preserves_thai_zero_width_space() -> None:
    thai_with_word_boundary = "การพัฒนา\u200bระบบ"

    normalized = normalize_text(thai_with_word_boundary)

    assert normalized == thai_with_word_boundary
    assert "\u200b" in normalized


def test_normalization_only_removes_bom_from_zero_width_formatting() -> None:
    meaningful_formatting = "A\u200bB\u200cC\u200dD\u2060E"

    assert normalize_text(f"\ufeff{meaningful_formatting}") == meaningful_formatting


def test_normalization_preserves_nonleading_bom_code_point() -> None:
    text = "First\ufeffsecond"

    assert normalize_text(text) == text
