# Financial News Article Summarizer and Ticker Extractor

This project is a backend-focused MVP designed to automatically scrape financial news articles from multiple sources and extract valuable insights. It collects essential data such as article titles, publication dates, full content, source domains, stock tickers, market indexes, and company names mentioned within the articles.

The core functionality includes:

- Robust extraction of article metadata and content from various news websites.
- Identification and validation of stock tickers using regex patterns and Yahoo Finance data.
- Matching company names to their stock tickers via a curated CSV reference.
- Generating concise, coherent article summaries leveraging the Hugging Face BART summarization API.

The final product aims to serve as a foundational backend system that enables users or applications to query and receive up-to-date financial news insights enriched with relevant market data. It can be expanded with alerting, sentiment analysis, and AI-driven advisory features in future phases.

This tool is ideal for developers and analysts looking to automate the collection and summarization of financial news for decision-making, research, or integration into larger financial platforms.
