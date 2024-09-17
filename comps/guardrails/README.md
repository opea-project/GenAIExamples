# Trust and Safety with LLM

The Guardrails service enhances the security of LLM-based applications by offering a suite of microservices designed to ensure trustworthiness, safety, and security.

| MicroService                                         | Description                                                                                                              |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [Llama Guard](./llama_guard/langchain/README.md)     | Provides guardrails for inputs and outputs to ensure safe interactions                                                   |
| [PII Detection](./pii_detection/README.md)           | Detects Personally Identifiable Information (PII) and Business Sensitive Information (BSI)                               |
| [Toxicity Detection](./toxicity_detection/README.md) | Detects Toxic language (rude, disrespectful, or unreasonable language that is likely to make someone leave a discussion) |
| [Bias Detection](./bias_detection/README.md)         | Detects Biased language (framing bias, epistemological bias, and demographic bias)                                       |

Additional safety-related microservices will be available soon.
