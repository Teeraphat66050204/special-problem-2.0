# Special Project Repository and Retrieval

This repository currently contains Fourth's Phase 1 backend foundation for a
PDF-to-Wiki application. It intentionally does **not** include upload routes,
OCR, LLM generation, chunking logic, embeddings, semantic search, or frontend
code yet.

## Current Phase 1 flow

```text
Future POST /api/upload
        |
        v
Save original digital PDF
        |
        v
PDF extractor (all pages, text layer only)
        |
        v
Persist Document metadata + raw_text
        |
        v
Future AI Wiki Generator -> review -> publish -> chunk -> embed
```

The extractor accepts a filesystem path or a binary file-like object such as
`UploadFile.file`. It returns cleaned full text, page count, one-based per-page
text, and typed warnings for blank pages. It never performs database writes and
does not attempt OCR.

## Data model

- `Document` stores source-file provenance, student/project metadata, extracted
  raw text, page count, and extraction lifecycle state.
- `WikiPage` stores versioned Markdown and its review/publication state. Versions
  are unique within a document, and a database constraint keeps `status` and
  `is_published` consistent.
- `Chunk` belongs to a document and may belong to a particular Wiki version. Its
  zero-based `chunk_index` and optional one-based `source_page` preserve enough
  provenance for a future search result to link to the Wiki, original PDF, and
  source page.

The first schema uses portable string-backed enums so model tests run with
SQLite. No migration framework existed in the repository, so one has not been
introduced in this phase.

### pgvector handoff

pgvector is not configured yet, so `Chunk` deliberately has no placeholder JSON
or binary embedding field. When PostgreSQL and pgvector are added, Jing should:

1. Add the `pgvector` Python dependency and enable the PostgreSQL `vector`
   extension in infrastructure or a migration.
2. Add an appropriately dimensioned `Vector(...)` column to `Chunk`; choose the
   dimension only after the embedding model is selected.
3. Add an HNSW or IVFFlat index after measuring the expected collection size and
   query behavior.
4. Introduce Alembic at that point to migrate the schema rather than relying on
   `SQLModel.metadata.create_all()` in production.

## Local setup and checks

Python 3.11 or newer is required.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## Upload endpoint handoff for Jing

The future `POST /api/upload` route should remain thin:

1. Validate the upload and save the original PDF under a unique `storage_key`.
2. Mark a new `Document` as `processing`.
3. Pass the saved path or `UploadFile.file` to
   `app.services.pdf_extractor.extract_pdf`.
4. Persist `full_text`, `page_count`, and a final `completed` status. For an
   expected user/input error such as an invalid or encrypted PDF, persist
   `failed` and return an appropriate 4xx response. Treat unexpected extraction
   or internal failures as server errors and normally return a 5xx response.
5. Pass the persisted document to the future Wiki generator in a separate
   service. Do not add generation logic to the upload route or extractor.

If page-level text must later be stored independently, add a dedicated page
entity or retain page metadata while chunking. Do not encode page boundaries by
rewriting the extracted Thai text.
