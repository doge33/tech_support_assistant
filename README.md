# Sitecore Content Hub Support Assistant

An unofficial RAG assistant that answers questions about asset management in Sitecore Content Hub, using its public documentation as a knowledge base.

## Knowledge Base

The downloaded documentation is excluded from this repository because redistribution permissions have not been confirmed.

The source URLs are listed in `urls.txt`. To download the selected pages and populate the `knowledge-base` folder, run:

```bash
uv sync
uv run soup.py