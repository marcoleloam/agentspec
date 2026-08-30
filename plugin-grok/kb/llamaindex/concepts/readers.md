# Readers

> **Purpose**: Load documents from files into LlamaIndex Document objects for indexing
> **Confidence**: 0.95
> **MCP Validated**: 2026-04-12

## Overview

Readers convert raw files into `Document` objects that LlamaIndex can embed and index. `SimpleDirectoryReader` handles generic files (txt, pdf, csv) from a directory. `JSONReader` handles JSON and JSONL files — set `is_jsonl=True` to split each line into a separate Document, which is critical for review data where each line is an independent record.

## The Pattern

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.json import JSONReader

# Option 1: Load all files from a directory
documents = SimpleDirectoryReader("./data/docs/").load_data()

# Option 2: Load JSONL file — one Document per line
reader = JSONReader(is_jsonl=True, clean_json=True)
documents = reader.load_data(input_file="./data/reviews/reviews.jsonl")

# Option 3: Load specific files
documents = SimpleDirectoryReader(
    input_files=["./data/report.pdf", "./data/notes.txt"]
).load_data()

# Each document has:
# - doc.text: the content string
# - doc.metadata: file path, creation date, etc.
# - doc.id_: unique identifier
```

## Quick Reference

| Reader | Input | Key Params | Output |
|--------|-------|------------|--------|
| `SimpleDirectoryReader` | Directory path | `input_dir`, `input_files`, `recursive` | List[Document] — one per file |
| `JSONReader` | File path | `is_jsonl=True`, `clean_json=True` | List[Document] — one per JSON line |

## JSONReader Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `is_jsonl` | `False` | **Set True for JSONL** — splits each line into a Document |
| `clean_json` | `True` | Sanitize JSON before parsing |
| `levels_back` | `None` | Number of levels to go back in nested JSON |
| `collapse_length` | `None` | Collapse long strings beyond this length |
| `ensure_ascii` | `False` | Force ASCII encoding (set False for Portuguese text) |

## Common Mistakes

### Wrong

```python
# SimpleDirectoryReader treats JSONL as ONE document (the entire file)
documents = SimpleDirectoryReader("./data/reviews/").load_data()
# Result: 1 document with ALL reviews concatenated — bad for RAG retrieval
```

### Correct

```python
# JSONReader with is_jsonl=True splits each line into a separate Document
reader = JSONReader(is_jsonl=True, clean_json=True)
documents = reader.load_data(input_file="./data/reviews/reviews.jsonl")
# Result: 1000 documents — one per review — each independently retrievable
```

## Related

- [Settings](../concepts/settings.md)
- [VectorStoreIndex](../concepts/vector-store-index.md)
- [JSONL to Qdrant Pattern](../patterns/jsonl-to-qdrant.md)
