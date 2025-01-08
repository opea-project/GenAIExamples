# Trust and Safety with LLM

The Guardrails service enhances the security of LLM-based applications by offering a suite of microservices designed to ensure trustworthiness, safety, and security.

| MicroService                                                   | Description                                                                                                              |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| [Llama Guard](./src/guardrails/README.md#LlamaGuard)           | Provides guardrails for inputs and outputs to ensure safe interactions using Llama Guard                                 |
| [WildGuard](./src/guardrails/README.md#WildGuard)              | Provides guardrails for inputs and outputs to ensure safe interactions using WildGuard                                   |
| [PII Detection](./src/pii_detection/README.md)                 | Detects Personally Identifiable Information (PII) and Business Sensitive Information (BSI)                               |
| [Toxicity Detection](./src/toxicity_detection/README.md)       | Detects Toxic language (rude, disrespectful, or unreasonable language that is likely to make someone leave a discussion) |
| [Bias Detection](./src/bias_detection/README.md)               | Detects Biased language (framing bias, epistemological bias, and demographic bias)                                       |
| [Prompt Injection Detection](./src/prompt_injection/README.md) | Detects malicious prompts causing the system running an LLM to execute the attacker’s intentions)                        |

Additional safety-related microservices will be available soon.
