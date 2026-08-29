import base64

import pytest

from app.services.document_text import DocumentTextExtractionError, extract_document_text


def test_extract_document_text_reads_plain_text_cv() -> None:
    text = extract_document_text(
        filename="cv.txt",
        content_base64=base64.b64encode(
            b"Python FastAPI backend project with Docker, tests, and REST APIs."
        ).decode("ascii"),
    )

    assert "Python FastAPI backend project" in text


def test_extract_document_text_rejects_unsupported_files() -> None:
    with pytest.raises(DocumentTextExtractionError, match="Supported CV file types"):
        extract_document_text(
            filename="cv.pages",
            content_base64=base64.b64encode(b"Some CV content").decode("ascii"),
        )
