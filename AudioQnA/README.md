# AudioQnA Application

AudioQnA is an example that demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio files, with the added functionality of Text-to-Speech (TTS) for generating spoken responses. The example showcases how to convert audio input to text using Automatic Speech Recognition (ASR), generate answers to user queries using a language model, and then convert those answers back to speech using Text-to-Speech (TTS).

## Deploy AudioQnA Service

The AudioQnA service can be deployed on either Intel Gaudi2 or Intel XEON Scalable Processor.

### Deploy AudioQnA on Gaudi

Refer to the [Gaudi Guide](./docker/gaudi/README.md) for instructions on deploying AudioQnA on Gaudi.

### Deploy AudioQnA on Xeon

Refer to the [Xeon Guide](./docker/xeon/README.md) for instructions on deploying AudioQnA on Xeon.

## Supported Models

### ASR

The default model is [openai/whisper-small](https://huggingface.co/openai/whisper-small). It also supports all models in the Whisper family, such as `openai/whisper-large-v3`, `openai/whisper-medium`, `openai/whisper-base`, `openai/whisper-tiny`, etc.

To replace the model, please edit the `compose.yaml` and add the `command` line to pass the name of the model you want to use:

```yaml
services:
  whisper-service:
    ...
    command: --model_name_or_path openai/whisper-tiny
```

### TTS

The default model is [microsoft/SpeechT5](https://huggingface.co/microsoft/speecht5_tts). We currently do not support replacing the model. More models under the commercial license will be added in the future.
