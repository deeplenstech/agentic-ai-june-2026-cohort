# Session 5 - RAG — Assignments

## Assignment 1: Build a Knowledge Base — Two Approaches

**Project:** [1.knowledgebase/](1.knowledgebase/)

Build, test, and evaluate a knowledge base over the provided employee handbook. You choose between two retrieval philosophies for the same document:

- **Vector store (AWS Bedrock)** — chunk the document, embed the chunks, and retrieve by vector similarity.
- **Vectorless (PageIndex)** — build a hierarchical tree of the document and retrieve by LLM reasoning / tree search, with no embeddings or vector database.

See the [approach chooser](1.knowledgebase/README.md) to compare the two and get started.

### Questions to Reflect On

- How does semantic chunking differ from fixed-size chunking? Did you see a difference in the relevance of retrieved passages?
- Which evaluation metrics mattered most for an HR policy use case, and why?
- Vector similarity vs reasoning-based tree search: which approach located the right passage more directly, and which was easier to trace?
---

## Assignment 2: Employee Policy Crew

**Project:** [2.employeepolicy/](2.employeepolicy/)

Connect a crewAI HR Manager agent to the knowledge base you built in Assignment 1. The agent answers employee policy questions by retrieving relevant passages from the handbook using RAG. The project ships **two retrieval variants** — mirroring the two approaches from Assignment 1:

- **Vector RAG** — retrieves from the Amazon Bedrock Knowledge Base via `BedrockKBRetrieverTool` (top-K vector similarity).
- **Vectorless RAG** — retrieves via the PageIndex MCP server (LLM reasoning / tree search, no embeddings).

Both run the same single HR Manager agent through a ReAct loop, and both support optional per-employee conversational memory via AWS Bedrock AgentCore.

See the [full instructions](2.employeepolicy/README.md) to get started.

### Questions to Reflect On

- How many iterations did the ReAct loop take? Did the agent call the retrieval tool more than once? Why might it need to?
- How does the answer quality differ between querying the LLM directly versus grounding it in the retrieved handbook passages?
- Did the vector and vectorless variants surface the same passage for a given question? Which was easier to trace?
- With memory enabled, how did the agent handle a follow-up question that depended on an earlier turn?