
"""Local text extraction for the Office formats supported by ingestion."""

from pathlib import Path

import logfire
from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


SUPPORTED_EXTENSIONS = {".docx", ".pptx"}



def _table_text(table) -> list[str]:
    """Return non-empty cell text, without duplicating merged cells."""
    text: list[str] = []
    seen_cells: set[int] = set()
    for row in table.rows:
        for cell in row.cells:
            if id(cell._tc) in seen_cells:
                continue
            seen_cells.add(id(cell._tc))
            value = cell.text.strip()
            if value:
                text.append(value)
    return text


def _shape_text(shape) -> list[str]:
    """Extract text from a PowerPoint shape, including tables and groups."""
    if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
        return [text for child in shape.shapes for text in _shape_text(child)]
    if shape.has_table:
        return _table_text(shape.table)
    if shape.has_text_frame:
        value = shape.text.strip()
        return [value] if value else []
    return []


def _parse_pptx(file_path: Path) -> str:
    presentation = Presentation(str(file_path))
    text: list[str] = []
    for slide in presentation.slides:
        for shape in slide.shapes:
            text.extend(_shape_text(shape))
    return "\n".join(text)


def _parse_docx(file_path: Path) -> str:
    document = Document(str(file_path))
    text = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        text.extend(_table_text(table))
    return "\n".join(text)


def parse_office(file_path: str) -> str:
    """Extract text from a local ``.docx`` or ``.pptx`` document.

    ``unstructured.partition.auto`` can try to download a spaCy model during
    text classification. That blocks ingestion when the runtime has no network
    access, so this loader uses the project's local Office libraries instead.
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    with logfire.span("Office Document Parsing", filename=str(path), extension=extension):
        if extension not in SUPPORTED_EXTENSIONS:
            message = f"Unsupported Office document type: {extension or '<none>'}"
            logfire.error(message)
            raise ValueError(message)
        if not path.is_file():
            message = f"Office document does not exist: {path}"
            logfire.error(message)
            raise FileNotFoundError(message)

        try:
            full_text = _parse_pptx(path) if extension == ".pptx" else _parse_docx(path)
        except Exception as exc:
            logfire.error("Office parse failed for {file_path}: {error}", file_path=str(path), error=str(exc))
            raise RuntimeError(f"Could not parse Office document '{path}': {exc}") from exc

        if full_text:
            logfire.info("Extracted text from Office document", filename=str(path), characters=len(full_text))
        else:
            logfire.warning("Office document contained no extractable text", filename=str(path))
        return full_text
