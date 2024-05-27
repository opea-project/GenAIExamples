# Document Summarization Application

In a world where data, information, and legal complexities is prevalent, the volume of legal documents is growing rapidly. Law firms, legal professionals, and businesses are dealing with an ever-increasing number of legal texts, including contracts, court rulings, statutes, and regulations.
These documents contain important insights, but understanding them can be overwhelming. This is where the demand for legal document summarization comes in.

Large Language Models (LLMs) have revolutionized the way we interact with text, LLMs can be used to create summaries of news articles, research papers, technical documents, and other types of text. Suppose you have a set of documents (PDFs, Notion pages, customer questions, etc.) and you want to summarize the content. In this example use case, we use LangChain to apply some summarization strategies and run LLM inference using Text Generation Inference on Intel Xeon and Gaudi2.

The document summarization architecture shows below:

![Architecture](https://i.imgur.com/XT0YUhu.png)

![Workflow](https://i.imgur.com/m9Ac9wy.png)

# Deploy Document Summarization Service

The Document Summarization service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

## Deploy Document Summarization on Gaudi

Refer to the [Gaudi Guide](./docker-composer/gaudi/README.md) for instructions on deploying Document Summarization on Gaudi.

## Deploy Document Summarization on Xeon

Refer to the [Xeon Guide](./docker-composer/xeon/README.md) for instructions on deploying Document Summarization on Xeon.
