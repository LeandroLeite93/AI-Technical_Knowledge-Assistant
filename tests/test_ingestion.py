import json

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject

from ingestion.chunking.text_chunker import chunk_page
from ingestion.loaders.document_loader import load_document
from ingestion.models import IngestionError, Page
from ingestion.parsers.text_cleaner import clean_text
from ingestion.pipeline import ingest, write_jsonl


def make_pdf(path, texts):
    writer = PdfWriter()
    for text in texts:
        page = writer.add_blank_page(width=300, height=300)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})
        })
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 20 200 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as output:
        writer.write(output)


def test_text_and_markdown_metadata(tmp_path):
    folder = tmp_path / "linux"
    folder.mkdir()
    (folder / "guide.MD").write_text("# Ação\n\n    code();", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("Texto", encoding="utf-8")
    chunks = ingest(tmp_path)
    assert [c.metadata["source"] for c in chunks] == ["linux/guide.MD", "readme.txt"]
    assert chunks[0].metadata["category"] == "LINUX"
    assert chunks[0].metadata["page"] is None
    assert "    code();" in chunks[0].text
    assert chunks[1].metadata["category"] == "GENERAL"


def test_pdf_page_numbers(tmp_path):
    path = tmp_path / "guide.pdf"
    make_pdf(path, ["First page", "Second page"])
    pages = load_document(path, tmp_path)
    assert [p.page for p in pages] == [1, 2]
    assert "First page" in pages[0].text
    chunks = ingest(tmp_path, chunk_size=8, overlap=2)
    assert {c.metadata["page"] for c in chunks} == {1, 2}


def test_blank_pdf_page_preserves_numbering(tmp_path):
    path = tmp_path / "guide.pdf"
    make_pdf(path, ["", "Page two"])
    with pytest.warns(UserWarning, match="sem texto"):
        pages = load_document(path, tmp_path)
    assert [p.page for p in pages] == [2]


def test_chunk_coverage_overlap_and_stable_ids():
    text = "abcdefghijklmnopqrstuvwxyz"
    page = Page(text, "example.txt", None, "GENERAL")
    chunks = chunk_page(page, 10, 3)
    assert [c.text for c in chunks] == [text[0:10], text[7:17], text[14:24], text[21:26]]
    reconstructed = chunks[0].text + "".join(c.text[3:] for c in chunks[1:])
    assert reconstructed == text
    assert chunks == chunk_page(page, 10, 3)
    assert len({c.id for c in chunks}) == len(chunks)
    assert chunks[-1].metadata["end_char"] == len(text)
    changed = chunk_page(Page(text, "other.txt", None, "GENERAL"), 10, 3)
    assert chunks[0].id != changed[0].id


@pytest.mark.parametrize(("size", "overlap"), [(0, 0), (10, -1), (10, 10)])
def test_invalid_chunk_parameters(size, overlap):
    with pytest.raises(ValueError):
        chunk_page(Page("abc", "a.txt", None, "GENERAL"), size, overlap)


def test_cleaning_preserves_code_and_accents():
    assert clean_text("\ufeffação\r\n    x = 1;  \r\n\r\n\r\nFim\x00") == (
        "\ufeffação\n    x = 1;\n\nFim"
    )


@pytest.mark.parametrize(("name", "content"), [
    ("bad.txt", b"\xff\xfe"), ("broken.pdf", b"broken"), ("empty.md", b"   "),
])
def test_invalid_documents(tmp_path, name, content):
    (tmp_path / name).write_bytes(content)
    with pytest.raises(IngestionError):
        ingest(tmp_path)


def test_encrypted_pdf(tmp_path):
    path = tmp_path / "locked.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    with path.open("wb") as stream:
        writer.write(stream)
    with pytest.raises(IngestionError, match="protegido"):
        ingest(tmp_path)


def test_missing_or_unsupported_input(tmp_path):
    with pytest.raises(IngestionError, match="não encontrada"):
        ingest(tmp_path / "missing")
    (tmp_path / "skip.csv").write_text("a,b")
    with pytest.raises(IngestionError, match="Nenhum"):
        ingest(tmp_path)


def test_symlink_outside_root(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("outside")
    (root / "link.txt").symlink_to(target)
    with pytest.raises(IngestionError, match="fora"):
        ingest(root)


def test_output_replaces_instead_of_appending(tmp_path):
    page = Page("Texto válido", "guide.txt", None, "GENERAL")
    chunks = chunk_page(page)
    output = tmp_path / "data" / "chunks.jsonl"
    write_jsonl(chunks, output)
    first = output.read_bytes()
    write_jsonl(chunks, output)
    assert output.read_bytes() == first
    record = json.loads(first.decode())
    assert record["text"] == page.text
    assert record["metadata"]["source"] == "guide.txt"


def test_cli_failure_keeps_previous_output(tmp_path, monkeypatch, capsys):
    from ingestion.pipeline import main

    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "broken.pdf").write_bytes(b"broken")
    output = tmp_path / "chunks.jsonl"
    output.write_text("previous result")
    monkeypatch.setattr("sys.argv", [
        "ingest", "--documents", str(docs), "--output", str(output),
    ])
    assert main() == 1
    assert output.read_text() == "previous result"
    assert "Erro:" in capsys.readouterr().err


def test_cli_rejects_output_inside_documents(tmp_path, monkeypatch, capsys):
    from ingestion.pipeline import main

    source = tmp_path / "guide.txt"
    source.write_text("Original")
    monkeypatch.setattr("sys.argv", [
        "ingest", "--documents", str(tmp_path), "--output", str(source),
    ])
    assert main() == 1
    assert source.read_text() == "Original"
    assert "fora" in capsys.readouterr().err
