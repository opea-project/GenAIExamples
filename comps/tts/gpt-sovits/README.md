# GPT-SoVITS Microservice

[GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS) allows you to to do zero-shot voice cloning and text to speech of multi languages such as English, Japanese, Korean, Cantonese and Chinese.

This microservice is validated on Xeon/CUDA. HPU support is under development.

## Build the Image

```bash
docker build -t opea/gpt-sovits:latest --build-arg http_proxy=$http_proxy --build-arg https_proxy=$https_proxy -f comps/tts/gpt-sovits/Dockerfile .
```

## Start the Service

```bash
docker run  -itd -p 9880:9880 -e http_proxy=$http_proxy -e https_proxy=$https_proxy opea/gpt-sovits:latest
```

## Test

- Chinese only

```bash
curl localhost:9880/ -XPOST -d '{
    "text": "先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
    "text_language": "zh"
}' --output out.wav
```

- English only

```bash
curl localhost:9880/ -XPOST -d '{
    "text": "Discuss the evolution of text-to-speech (TTS) technology from its early beginnings to the present day. Highlight the advancements in natural language processing that have contributed to more realistic and human-like speech synthesis. Also, explore the various applications of TTS in education, accessibility, and customer service, and predict future trends in this field. Write a comprehensive overview of text-to-speech (TTS) technology.",
    "text_language": "en"
}' --output out.wav
```

- Auto detection of languages

```bash
curl localhost:9880/ -XPOST -d '{
    "text": "Hi 你好，这里是一个 cross-lingual 的例子。",
    "text_language": "auto"
}' --output out.wav
```

- Change reference audio

This microservice allows you to use the zero-shot voice cloning feature. For example, you can change the reference audio from the default female to a male voice:

```bash
wget https://github.com/OpenTalker/SadTalker/blob/main/examples/driven_audio/chinese_poem1.wav

docker cp chinese_poem1.wav gpt-sovits-service:/home/user/chinese_poem1.wav

curl localhost:9880/change_refer -d '{
    "refer_wav_path": "/home/user/chinese_poem1.wav",
    "prompt_text": "窗前明月光，疑是地上霜，举头望明月，低头思故乡。",
    "prompt_language": "zh"
}'
```

- openai protocol compatible request

```bash
curl localhost:9880/v1/audio/speech -XPOST -d '{"input":"你好呀，你是谁. Hello, who are you?"}' -H 'Content-Type: application/json' --output speech.mp3
```
