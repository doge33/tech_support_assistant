# Sitecore Content Hub Support Assistant

An unofficial retrieval-augmented generation (RAG) assistant that answers questions about asset management in Sitecore Content Hub using public documentation.

## How It Works

1. Downloads selected documentation pages and converts their article content into Markdown.
2. Chunks the documents, generates embeddings, and stores them in Chroma.
3. Retrieves candidates using the original and rewritten queries.
4. Reranks the candidates and passes the top chunks to the answering model.
5. Provides answers grounded in the retrieved documentation.

The project includes a Gradio chatbot and a separate evaluation dashboard for inspecting answers, retrieved context, and evaluation feedback.

## Knowledge Base

The downloaded documentation is excluded from this repository because redistribution permissions have not been confirmed.

Source URLs are listed in `urls.txt`. To install dependencies and populate the `knowledge-base` folder, run:

```bash
uv sync
uv run soup.py
```

## Configuration

| Setting | Value |
| --- | --- |
| Chunking model | `gpt-5-mini` |
| Answering model | `gpt-5-mini` |
| Evaluation model | `gpt-6.1-terra` |
| Target average chunk size | 200 words |
| Requested chunk overlap | Approximately 25%, or 50 words |
| Retrieval K | 10 candidates per retrieval query |
| Final K | 5 chunks passed to the answering model |

Chunk size and overlap are requested targets for model-based chunking; actual lengths may vary.

## Evaluation

The initial evaluation set contains 10 questions covering factual answers, procedures, troubleshooting, comparisons, multi-document reasoning, and conflicting documentation.

Retrieval is evaluated using keyword-based MRR, nDCG, and keyword coverage. An LLM judge evaluates answer accuracy, completeness, and relevance on a 1–5 scale. Individual answers and retrieved chunks are also inspected manually.

### Findings and Improvements

Procedure questions initially performed poorly. Inspection showed that relevant chunks sometimes ended before the detailed instructions, leaving the answering model without essential steps.

The following changes improved results:

- Increased the final context limit from 3 to 5 chunks.
- Increased retrieval K from 5 to 10.
- Increased the target average chunk size from 100 to 200.

After these changes, scores for the affected procedure questions increased from approximately 3/5 to 4–5/5. Manual inspection confirmed that previously missing key information appeared in the retrieved context.

These results reflect iterative development on a small evaluation set. They do not establish performance on unseen questions, and LLM judge scores may vary.

## Limitations

- Coverage is limited to the selected documentation pages.
- The assistant cannot inspect a user's Content Hub instance, configuration, or logs.
- Public documentation can contain incomplete or conflicting information.
- Retrieval and generated answers can still contain errors.

## Disclaimer

This is an independent portfolio project and is not affiliated with or endorsed by Sitecore.

## Acknowledgments

This project builds on the RAG implementation and evaluation code
from Ed Donner's LLM Engineering course on Udemy.

### My Contributions

- Adapted the application to Sitecore Content Hub asset-management documentation.
- Built the documentation scraping and HTML-to-Markdown conversion pipeline.
- Created a domain-specific evaluation set with AI assistance.
- Extended the Gradio evaluation dashboard to show generated answers,
  reference answers, judge feedback, individual scores, and retrieved
  chunks for each question.
- Used the detailed evaluation results to diagnose missing procedure
  steps and improve retrieval settings and chunk sizes.

The underlying RAG and evaluation implementation is adapted from
the course.