# AudioQnA accuracy Evaluation

AudioQnA is an example that demonstrates the integration of Generative AI (GenAI) models for performing question-answering (QnA) on audio scene, which contains Automatic Speech Recognition (ASR) and Text-to-Speech (TTS). The following is the piepline for evaluating the ASR accuracy.

## Dataset

We evaluate the ASR accuracy on the test set of librispeech [dataset](https://huggingface.co/datasets/andreagasparini/librispeech_test_only), which contains 2620 records of audio and texts.

## Metrics

We evaluate the WER (Word Error Rate) metric of the ASR microservice.

## Evaluation

### Launch ASR microservice

Launch the ASR microserice with the following commands. For more details please refer to [doc](https://github.com/opea-project/GenAIComps/tree/main/comps/asr).

```bash
git clone https://github.com/opea-project/GenAIComps
cd GenAIComps
docker build -t opea/whisper:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/asr/whisper/Dockerfile .
# change the name of model by editing model_name_or_path you want to evaluate
docker run -p 7066:7066 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/whisper:latest --model_name_or_path "openai/whisper-tiny"
```

### Evaluate

Install dependencies:

```
pip install -r requirements.txt
```

Evaluate the performance with the LLM:

```py
# validate the offline model
# python offline_evaluate.py
# validate the online asr microservice accuracy
python online_evaluate.py
```

### Performance Result

Here is the tested result for your reference
|| WER |
| --- | ---- |
|whisper-large-v2| 2.87|
|whisper-large| 2.7 |
|whisper-medium| 3.45 |
