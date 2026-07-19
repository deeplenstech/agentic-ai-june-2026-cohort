# Session 5 - RAG — Assignments

## Assignment 1: Build a Knowledge Base — Two Approaches

**Project:** [1.knowledgebase/](1.knowledgebase/README.md)

Build, test, and evaluate a knowledge base over the provided employee handbook. You choose between two retrieval philosophies for the same document:

- **Vector store (AWS Bedrock)** — chunk the document, embed the chunks, and retrieve by vector similarity.
- **Vectorless (PageIndex)** — build a hierarchical tree of the document and retrieve by LLM reasoning / tree search, with no embeddings or vector database.

See the [approach chooser](1.knowledgebase/README.md) to compare the two and get started.

---

## Assignment 2: Employee Policy Crew

**Project:** [2.employeepolicy/](2.employeepolicy/)

Connect a crewAI HR Manager agent to the knowledge base you built in Assignment 1. The agent answers employee policy questions by retrieving relevant passages from the handbook using RAG. The project ships **two retrieval variants** — mirroring the two approaches from Assignment 1:

- **Vector RAG** — retrieves from the Amazon Bedrock Knowledge Base via `BedrockKBRetrieverTool` (top-K vector similarity).
- **Vectorless RAG** — retrieves via the PageIndex MCP server (LLM reasoning / tree search, no embeddings).

Both run the same single HR Manager agent through a ReAct loop, and both support optional per-employee conversational memory via AWS Bedrock AgentCore.

See the [full instructions](2.employeepolicy/README.md) to get started.