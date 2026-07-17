# Assignment 1: Build a Knowledge Base — Choose Your Retrieval Approach

In this assignment you will build a knowledge base over the same source document — `employee_handbook.pdf` — and test how well it answers policy questions. There are **two approaches**, representing two different philosophies of retrieval. Pick one (or try both and compare).

---

## The Two Approaches

### 1. Vector Store (AWS Bedrock)

The classic RAG pipeline. The document is **chunked**, each chunk is turned into a vector by an **embedding model**, and the vectors are stored in a **vector database**. At query time, the question is embedded and the most **similar** chunks (top-K) are retrieved and passed to an LLM.

→ **[Vector store approach](README-vector-store.md)**

### 2. Vectorless (PageIndex)

A reasoning-based alternative. The document is transformed into a hierarchical **tree structure** (like a table of contents). At query time, an LLM performs **multi-step reasoning / tree search** to navigate the outline and pull the exact relevant pages — **no embeddings, no chunking, no vector database**.

→ **[Vectorless (PageIndex) approach](README-vectorless-pageindex.md)**

---

## How They Differ

| | Vector Store (Bedrock) | Vectorless (PageIndex) |
|---|---|---|
| **Chunking** | Yes — semantic chunking | No |
| **Embeddings** | Yes — an embedding model | No |
| **Vector database** | Yes — S3 vector store | No |
| **Retrieval mechanism** | Top-K vector similarity | LLM reasoning / tree search over a document outline |
| **Explainability** | Ranked chunks by similarity score | Traceable path: browse → outline → targeted pages |
| **Setup surface** | Entirely within AWS (S3 + Bedrock) | External service via API key + MCP |
| **Best for** | Broad semantic recall across many passages | Long, structured documents where the answer lives in a specific section |

---

## Shared Assets

Both approaches use the files already in this folder:

- `employee_handbook.pdf` — the source document.
- `eval_data_set.jsonl` — 10 question / reference-answer pairs for testing. (The vector-store approach runs these through Bedrock's evaluation job; the vectorless approach uses them for manual spot-checks.)

---

## Continuing to Later Assignments

Subsequent assignments will provide **separate variants for each approach**, so whichever path you choose here, you can carry it forward.
