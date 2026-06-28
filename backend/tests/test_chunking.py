from app.services.chunking import Chunk, chunk_markdown

SAMPLE = """# Arindam

Short intro line.

## Experience

Worked at Acme as a backend engineer.

## Skills

Python, FastAPI, RAG.
"""


def test_splits_into_one_chunk_per_heading():
    chunks = chunk_markdown(SAMPLE, source_file="about.md")
    titles = [c.title for c in chunks]
    assert titles == ["Arindam", "Experience", "Skills"]


def test_heading_text_and_body_are_in_content():
    chunks = chunk_markdown(SAMPLE, source_file="about.md")
    experience = next(c for c in chunks if c.title == "Experience")
    assert "Experience" in experience.content
    assert "Worked at Acme" in experience.content


def test_metadata_records_source_and_heading():
    chunks = chunk_markdown(SAMPLE, source_file="about.md")
    assert chunks[0].metadata == {"source_file": "about.md", "heading": "Arindam"}


def test_empty_sections_are_dropped():
    chunks = chunk_markdown("## Empty\n\n## Has Body\n\nText here.\n")
    titles = [c.title for c in chunks]
    assert titles == ["Has Body"]
    assert isinstance(chunks[0], Chunk)


def test_content_before_first_heading_becomes_untitled_chunk():
    chunks = chunk_markdown("Loose intro paragraph.\n\n## Section\n\nBody.")
    assert chunks[0].title is None
    assert "Loose intro paragraph." in chunks[0].content
