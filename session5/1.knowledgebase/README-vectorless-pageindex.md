# Assignment 1 (Vectorless): PageIndex Reasoning-Based Retrieval

> This is the **vectorless** approach. For an overview of how it differs from the vector-store
> (AWS Bedrock) approach — and to switch — see the [approach chooser](README.md).

## What is PageIndex?

[PageIndex](https://pageindex.ai) is a **vectorless, reasoning-based RAG** system. Instead of chunking a document and storing embeddings in a vector database, PageIndex transforms the document into a hierarchical **tree structure** — much like a table of contents — and lets an LLM perform **multi-step reasoning / tree search** over that tree to locate the right passages.

- **No embeddings, no chunking, no vector DB, no top-K**
- Retrieval follows a **traceable reasoning path** through the document's outline
- Mirrors how a human expert navigates a long document: skim the table of contents, jump to the relevant section, read the specific pages

In this assignment you will upload the same `employee_handbook.pdf` to PageIndex and explore its **MCP server** directly using **MCP Inspector** — without writing any agent code. (This mirrors the approach from [session4/1.atlassian_mcp_server](../../session4/1.atlassian_mcp_server/README.md).)

---

## Source Document

`employee_handbook.pdf` is included in this folder. It is the same source document used by the vector-store approach, so you can compare answers side by side.

> **Note:** This employee handbook was generated with ChatGPT and is intentionally imperfect. It may contain inconsistencies, ambiguities, or errors — a realistic test of how well retrieval handles noisy real-world documents.

---

## Prerequisites

- A **PageIndex account** — sign up at [pageindex.ai](https://pageindex.ai) or [chat.pageindex.ai](https://chat.pageindex.ai). The free tier covers ~1000 pages.
- A **PageIndex API key** — create one in the [Developer Dashboard](https://dash.pageindex.ai/api-keys). Copy it immediately.
- **Node.js** installed (`node -v` to confirm) — required for MCP Inspector.

---

## Step 1 — Upload the Handbook in the PageIndex UI

Uploading is done through the PageIndex web app, **not** over MCP (the MCP server is read-only search/retrieval).

1. Sign in to the PageIndex web app ([pageindex.ai](https://pageindex.ai) / [chat.pageindex.ai](https://chat.pageindex.ai)).
2. Upload `employee_handbook.pdf` from this folder.
3. Wait for processing to reach **completed** — PageIndex parses the PDF and builds its hierarchical tree index. (Processing takes roughly a couple of seconds per page.)

---

## Step 2 — Install MCP Inspector

MCP Inspector is a browser-based UI for connecting to any MCP server and invoking its tools interactively.

```bash
npx @modelcontextprotocol/inspector
```

This starts the Inspector and opens the web UI on port `6274`. Open `http://localhost:6274` in your browser.

---

## Step 3 — Connect to the PageIndex MCP Server

PageIndex exposes a remote MCP server at:

```
https://api.pageindex.ai/mcp
```

In the Inspector UI, configure the target server:

1. Set **Transport** to `Streamable HTTP`
2. Set **URL** to `https://api.pageindex.ai/mcp`
3. Open the **Headers** section and add:

| Key | Value |
|---|---|
| `Authorization` | `Bearer <YOUR_PAGEINDEX_API_KEY>` |

4. Click **Connect**

---

## Step 4 — Explore Available Tools

Click the **Tools** tab. Every PageIndex MCP tool is **read-only search/retrieval** (except `remove_document`) — there is no upload tool, because uploading happens in the UI (Step 1).

| Tool | Purpose |
|---|---|
| `browse_documents` | **Primary** retrieval. A bare call lists root-level folders and documents; pass `sort="relevance"` + `query` for semantic ranking. |
| `search_documents` | Escalation only — keyword-only search when `browse_documents` missed a document you know exists. |
| `get_document` | Check a document's processing status (`pending` → `completed`) and metadata. |
| `get_document_structure` | Extract the hierarchical **outline / tree** (headers, sections, page references). |
| `get_page_content` | Pull content from targeted page ranges (e.g. `"5-10"`). |
| `get_document_image` | Retrieve an embedded image by its `image_path`. |
| `remove_document` | Permanently delete a document (destructive). |

Each tool shows its typed input schema — the same kind of schema an agent framework like CrewAI uses to call a tool.

---

## Step 5 — Run the Reasoning-Based Retrieval Flow

Rather than a single similarity lookup, PageIndex retrieval is a **navigation** through the document tree. Run these tools in order, using the same sample question as the vector-store approach:

> How many casual leave days does DeepLens provide?

1. **Find the document** — call `browse_documents`:
   ```json
   { "sort": "relevance", "query": "casual leave days" }
   ```
   Copy the `name` of the handbook from the result (e.g. `employee_handbook.pdf`).

2. **Confirm it's ready** — call `get_document`:
   ```json
   { "doc_name": "employee_handbook.pdf" }
   ```
   Check that `status` is `completed`.

3. **Read the tree** — call `get_document_structure`:
   ```json
   { "doc_name": "employee_handbook.pdf" }
   ```
   Inspect the outline and locate the leave-policy section, noting its page references.

4. **Pull the exact pages** — call `get_page_content`:
   ```json
   { "doc_name": "employee_handbook.pdf", "pages": "<pages from the outline>" }
   ```
   These pages contain the answer.

Notice the contrast with the vector-store approach: instead of returning top-K similarity chunks, PageIndex walks a table-of-contents tree straight to the relevant pages — a **transparent, traceable reasoning path**.

---

## Comparing Results & Evaluation

PageIndex has **no built-in RAG evaluation harness** equivalent to Bedrock's, and `eval_data_set.jsonl` in this folder is in the Bedrock evaluation format. So rather than running an automated evaluation job, **manually spot-check**:

- Run a few questions from `eval_data_set.jsonl` through the retrieval flow above.
- Compare PageIndex's answers against the **reference answers** in that file.
- If you also completed the [vector-store approach](README-vector-store.md), compare the two side by side — which found the right passage more directly? Which was easier to trace?

---

## What This Teaches You

| Concept | What you observed |
|---|---|
| Tree navigation vs chunking | PageIndex retrieves by walking a document outline, not by splitting text into fixed chunks |
| Reasoning vs similarity | Retrieval is a multi-step tree search, not a top-K vector similarity lookup |
| Explainability | The browse → structure → page-content path is a traceable reasoning trajectory |
| Separation of concerns | Upload happens in the UI; the MCP server is read-only retrieval |
| MCP tool schemas | Each tool exposes a typed input schema — the same contract an agent framework calls |
