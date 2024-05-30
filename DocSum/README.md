# Document Summarization Application

In a world where data, information, and legal complexities are prevalent, the volume of legal documents is growing rapidly. Law firms, legal professionals, and businesses are dealing with an ever-increasing number of legal texts, including contracts, court rulings, statutes, and regulations. These documents contain important insights, but understanding them can be overwhelming. This is where the demand for legal document summarization comes in.

Large Language Models (LLMs) have revolutionized the way we interact with text. These models can be used to create summaries of news articles, research papers, technical documents, and other types of text. Suppose you have a set of documents (PDFs, Notion pages, customer questions, etc.) and you want to summarize the content. In this example use case, we utilize LangChain to implement summarization strategies and facilitate LLM inference using Text Generation Inference on Intel Xeon and Gaudi2 processors.

The architecture for document summarization will be illustrated/described below:

![Architecture](https://i.imgur.com/XT0YUhu.png)

![Workflow](https://i.imgur.com/m9Ac9wy.png)

# Deploy Document Summarization Service

The Document Summarization service can be effortlessly deployed on either Intel Gaudi2 or Intel XEON Scalable Processors.

## Deploy Document Summarization on Gaudi

Refer to the [Gaudi Guide](./docker/gaudi/README.md) for instructions on deploying Document Summarization on Gaudi.

## Deploy Document Summarization on Xeon

Refer to the [Xeon Guide](./docker/xeon/README.md) for instructions on deploying Document Summarization on Xeon.
