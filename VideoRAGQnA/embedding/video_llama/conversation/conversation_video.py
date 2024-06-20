"""
Conversation prompt template of Video-LLaMA.
Adapted from: https://github.com/Vision-CAIR/MiniGPT-4/blob/main/minigpt4/conversation/conversation.py 
"""
import argparse
import time
from PIL import Image
import sys
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, LlamaTokenizer
from transformers import StoppingCriteria, StoppingCriteriaList

import dataclasses
from enum import auto, Enum
from typing import List, Tuple, Any
import os
from embedding.video_llama.common.registry import registry
from embedding.video_llama.processors.video_processor import ToTHWC,ToUint8,load_video
from embedding.video_llama.processors import Blip2ImageEvalProcessor
            
from embedding.video_llama.models.ImageBind.data import load_and_transform_audio_data
class SeparatorStyle(Enum):
    """Different separator style."""
    SINGLE = auto()
    TWO = auto()
    LLAMA_2 = auto()


@dataclasses.dataclass
class Conversation:
    """A class that keeps all conversation history."""
    system: str
    roles: List[str]
    messages: List[List[str]]
    offset: int
    # system_img: List[Image.Image] = []
    sep_style: SeparatorStyle = SeparatorStyle.SINGLE
    sep: str = "###"
    sep2: str = None

    skip_next: bool = False
    conv_id: Any = None

    def get_prompt(self):
        if self.sep_style == SeparatorStyle.SINGLE:
            ret = self.system + self.sep
            for role, message in self.messages:
                if message:
                    ret += role + ": " + message + self.sep
                else:
                    ret += role + ":"
            return ret
        elif self.sep_style == SeparatorStyle.TWO:
            seps = [self.sep, self.sep2]
            ret = self.system + seps[0]
            for i, (role, message) in enumerate(self.messages):
                if message:
                    ret += role + ": " + message + seps[i % 2]
                else:
                    ret += role + ":"
            return ret
        elif self.sep_style == SeparatorStyle.LLAMA_2:
            wrap_sys = lambda msg: f"<<SYS>>\n{msg}\n<</SYS>>\n\n"
            wrap_inst = lambda msg: f"[INST] {msg} [/INST]"
            ret = ""

            for i, (role, message) in enumerate(self.messages):
                if i == 0:
                    assert message, "first message should not be none"
                    assert role == self.roles[0], "first message should come from user"
                if message:
                    if type(message) is tuple:
                        message, _, _ = message
                    if i == 0: message = wrap_sys(self.system) + message
                    if i % 2 == 0:
                        message = wrap_inst(message)
                        ret += self.sep + message
                    else:
                        ret += " " + message + " " + self.sep2
                else:
                    ret += ""
            ret = ret.lstrip(self.sep)
            return ret
        else:
            raise ValueError(f"Invalid style: {self.sep_style}")

    def append_message(self, role, message):
        self.messages.append([role, message])

    def to_gradio_chatbot(self):
        ret = []
        for i, (role, msg) in enumerate(self.messages[self.offset:]):
            if i % 2 == 0:
                ret.append([msg, None])
            else:
                ret[-1][-1] = msg
        return ret

    def copy(self):
        return Conversation(
            system=self.system,
            # system_img=self.system_img,
            roles=self.roles,
            messages=[[x, y] for x, y in self.messages],
            offset=self.offset,
            sep_style=self.sep_style,
            sep=self.sep,
            sep2=self.sep2,
            conv_id=self.conv_id)

    def dict(self):
        return {
            "system": self.system,
            # "system_img": self.system_img,
            "roles": self.roles,
            "messages": self.messages,
            "offset": self.offset,
            "sep": self.sep,
            "sep2": self.sep2,
            "conv_id": self.conv_id,
        }


class StoppingCriteriaSub(StoppingCriteria):

    def __init__(self, stops=[], encounters=1):
        super().__init__()
        self.stops = stops

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor):
        for stop in self.stops:
            if torch.all((stop == input_ids[0][-len(stop):])).item():
                return True

        return False


CONV_VISION = Conversation(
    system="Give the following image: <Img>ImageContent</Img>. "
           "You will be able to see the image once I provide it to you. Please answer my questions.",
    roles=("Human", "Assistant"),
    messages=[],
    offset=0,
    sep_style=SeparatorStyle.SINGLE,
    sep="###",
)

default_conversation = Conversation(
    system="",
    roles=("Human", "Assistant"),
    messages=[],
    offset=0,
    sep_style=SeparatorStyle.SINGLE,
    sep="###",
)
conv_llava_llama_2 = Conversation(
    #system="You are a helpful language and vision assistant. "
    #       "You are able to understand the visual content that the user provides, "
    #       "and assist the user with a variety of tasks using natural language.",
    system="You are Intel's RAG assistant who understands visual and textual content. \
    You will be provided with two things, video embeddings and user's RAG prompt. \
    You are suppose to understand video content from the video embeddings \
and provide answer to user's question. \
\
As an assistant, you need to follow these Rules while answering questions,\
\
Rules:\
- Don't answer any question which are not related to provied video content.\
- Don't be toxic and don't include harmful information.\
- Give answer only if you find it in the video conent, otherwise just say You don't have enough information to answer the question.\
\
Here are the video embeddings:",
    roles=("USER", "ASSISTANT"),
    messages=(),
    offset=0,
    sep_style=SeparatorStyle.LLAMA_2,
    sep="<s>",
    sep2="</s>",
)
class Chat:
    def __init__(self, model, vis_processor, device='cuda:0'):
        self.device = device
        self.model = model
        self.vis_processor = vis_processor
        self.image_vis_processor = Blip2ImageEvalProcessor()
        self.video_msg = ""
        # stop_words_ids = [torch.tensor([835]).to(self.device),
        #                   torch.tensor([2277, 29937]).to(self.device)]  # '###' can be encoded in two different ways.
        # self.stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])
        self.conv = conv_llava_llama_2.copy()
        self.img_list = []

    def ask(self, text):
        self.question = text
        if len(self.conv.messages) > 0 and self.conv.messages[-1][0] == self.conv.roles[0] \
                and ('</Video>' in self.conv.messages[-1][1] or '</Image>' in self.conv.messages[-1][1]):  # last message is image.
            self.conv.messages[-1][1] = ' '.join([self.conv.messages[-1][1], text])
        else:
            self.conv.append_message(self.conv.roles[0], text)

    def answer(self, max_new_tokens=300, num_beams=1, min_length=1, top_p=0.9,
               repetition_penalty=1.0, length_penalty=1, temperature=1.0, max_length=2000, keep_conv_hist=True, streamer=None):
        self.conv.append_message(self.conv.roles[1], None)
        embs = self.get_context_emb(keep_conv_hist)
        print("chat.answer - input to llama: embs.shape:", embs.shape)

        current_max_len = embs.shape[1] + max_new_tokens
        if current_max_len - max_length > 0:
            print('Warning: The number of tokens in current conversation exceeds the max length. '
                  'The model will not see the contexts outside the range.')
        begin_idx = max(0, current_max_len - max_length)

        embs = embs[:, begin_idx:]
        if self.conv.sep =="###":
            stop_words_ids = [torch.tensor([835]).to(self.device),
                          torch.tensor([2277, 29937]).to(self.device)]  # '###' can be encoded in two different ways.
            stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])
        else:
            stop_words_ids = [torch.tensor([2]).to(self.device)]
            stopping_criteria = StoppingCriteriaList([StoppingCriteriaSub(stops=stop_words_ids)])

        # stopping_criteria
        outputs = self.model.llama_model.generate(
            inputs_embeds=embs,
            max_new_tokens=max_new_tokens,
            stopping_criteria=stopping_criteria,
            num_beams=num_beams,
            do_sample=True,
            min_length=min_length,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            length_penalty=length_penalty,
            temperature=temperature,
            streamer=streamer
        )
        output_token = outputs[0]
        if output_token[0] == 0:  # the model might output a unknow token <unk> at the beginning. remove it
            output_token = output_token[1:]
        if output_token[0] == 1:  # some users find that there is a start token <s> at the beginning. remove it
            output_token = output_token[1:]
        output_text = self.model.llama_tokenizer.decode(output_token, add_special_tokens=False)
        if self.conv.sep =="###":
            output_text = output_text.split('###')[0]  # remove the stop sign '###'
            output_text = output_text.split('Assistant:')[-1].strip()
        else:
            output_text = output_text.split(self.conv.sep2)[0]  # remove the stop sign '###'
            output_text = output_text.split(self.conv.roles[1]+':')[-1].strip()
        self.conv.messages[-1][1] = output_text
        print("chat.answer - llama output_text:", output_text)
        print("chat.answer - llama output_token.cpu().numpy().shape:", output_token.cpu().numpy().shape)
        return output_text, output_token.cpu().numpy()
    
    def upload_video(self, video_path):

        msg = ""
        if isinstance(video_path, str):  # is a video path
            ext = os.path.splitext(video_path)[-1].lower()
            print(f"\nuploading {video_path}")
            # image = self.vis_processor(image).unsqueeze(0).to(self.device)
            video, msg = load_video(
                video_path=video_path,
                n_frms=32,
                height=224,
                width=224,
                sampling ="uniform", return_msg = True
            )
            video = self.vis_processor.transform(video)
            video = video.unsqueeze(0).to(self.device)
            # print(image)
        else:
            raise NotImplementedError
        
        try:
            audio_flag = 1
            audio = load_and_transform_audio_data([video_path],"cpu",  clips_per_video=8)
            audio = audio.to(self.device)
        except :
            print('no audio is found')
            audio_flag = 0
        finally:
            if audio_flag == 1:
                # image_emb, _ = self.model.encode_videoQformer_audiovideo(video,audio)
                image_emb, _ = self.model.encode_videoQformer_visual(video)
                audio_emb,_  = self.model.encode_audioQformer(audio)
                self.img_list.append(audio_emb)
                self.img_list.append(image_emb)
                self.conv.system = ""
                # conv.append_message(conv.roles[0], "The audio of this video is <Video><ImageHere></Video> ")
                self.conv.append_message(self.conv.roles[0], "Close your eyes, open your ears and you imagine only based on the sound that: <ImageHere>. \
                Close your ears, open your eyes and you see that <Video><ImageHere></Video>.  \
                Now answer my question based on what you have just seen and heard.")

            else:  # only vison no audio
                # conv.system = "You can understand the video that the user provides. Follow the instructions carefully and explain your answers in detail."
                image_emb, _ = self.model.encode_videoQformer_visual(video)
                self.img_list.append(image_emb)
                self.conv.append_message(self.conv.roles[0], "<Video><ImageHere></Video> "+ msg)
            self.video_msg = msg
            print(f"chat.upload_video - len(img_list): {len(self.img_list)}, AL-branch_out: audio_emb.size():{audio_emb.size()}, VL-branch_out: image_emb.size():{image_emb.size()}")
            return "Received."

    def upload_video_without_audio(self, video_path, start_time, duration):
        msg = ""
        if isinstance(video_path, str):  # is a video path
            ext = os.path.splitext(video_path)[-1].lower()
            print(f"\nuploading {video_path}")
            # image = self.vis_processor(image).unsqueeze(0).to(self.device)
            video, msg = load_video(
                video_path=video_path, start_time=start_time, duration=duration,
                n_frms=32,
                height=224,
                width=224,
                sampling ="uniform", return_msg = True
            )
            video = self.vis_processor.transform(video)
            video = video.unsqueeze(0).to(self.device)
            # print(image)
        else:
            raise NotImplementedError
        
        
        # conv.system = "You can understand the video that the user provides.  Follow the instructions carefully and explain your answers in detail."
        image_emb, _ = self.model.encode_videoQformer_visual(video) 
        self.img_list.append(image_emb)
        self.conv.append_message(self.conv.roles[0], "<Video><ImageHere></Video> "+ msg)
        self.video_msg = msg
        print(f"chat.upload_video_without_audio - len(img_list): {len(self.img_list)}, VL-branch_out: image_emb.size():{image_emb.size()}")
        return "Received."

    def upload_img(self, image):

        print(f"\nuploading {image}")
        msg = ""
        if isinstance(image, str):  # is a image path
            raw_image = Image.open(image).convert('RGB') # 增加一个时间维度
            image = self.image_vis_processor(raw_image).unsqueeze(0).unsqueeze(2).to(self.device)
        elif isinstance(image, Image.Image):
            raw_image = image
            image = self.image_vis_processor(raw_image).unsqueeze(0).unsqueeze(2).to(self.device)
        elif isinstance(image, torch.Tensor):
            if len(image.shape) == 3:
                image = image.unsqueeze(0)
            image = image.to(self.device)
        else:
            raise NotImplementedError

        image_emb, _ = self.model.encode_videoQformer_visual(image)
        self.img_list.append(image_emb)
        # Todo msg=""
        self.conv.append_message(self.conv.roles[0], "<Image><ImageHere></Image> "+ msg)
        print(f"chat.upload_img - len(img_list): {len(self.img_list)}, VL-branch_out: image_emb.size():{image_emb.size()}")
        self.video_msg = msg
        return "Received."

    def get_context_emb(self, keep_conv_hist=True):
        prompt = self.conv.get_prompt()
        prompt_segs = prompt.split("<rag_prompt>")
        prompt_segs.insert(1, "The user wants to know:")
        prompt_segs = "".join(prompt_segs).split('<ImageHere>')
        print(f"chat.get_context_emb - prompt_segs before keep_conv_hist block:\n  {prompt_segs}")
        print("len(conv.messages):", len(self.conv.messages))
        if len(self.conv.messages) > 2 and not keep_conv_hist: # forget previous answers and reply to the question with provided image/audio embs
            media_placeholdername = prompt_segs[0][-7:] # <Image> or <Video>
            if self.conv.sep_style == SeparatorStyle.LLAMA_2:
                # wrap the question as it's the first question
                prompt_segs[-1] = f"</{media_placeholdername[1:]} {self.video_msg} {self.question}[/INST]"
            elif self.conv.sep_style == SeparatorStyle.SINGLE:
                # wrap the question as it's the first question
                prompt_segs[-1] = f"</{media_placeholdername[1:]} {self.video_msg} {self.question}###"
            else:
                print("prompt_segs error in chat.get_context_emb")

        print(f"chat.get_context_emb - prompt_segs after keep_conv_hist block:\n  {prompt_segs}")
        print(f"chat.get_context_emb - len(img_list): {len(self.img_list)}")
        for i in range(len(self.img_list)):
            print(f"img_list[{i}].size(): {self.img_list[i].size()}")
        assert len(prompt_segs) == len(self.img_list) + 1, "Unmatched numbers of image placeholders and images."
        seg_tokens = [
            self.model.llama_tokenizer(
                seg, return_tensors="pt", add_special_tokens=i == 0).to(self.device).input_ids
            # only add bos to the first seg
            for i, seg in enumerate(prompt_segs)
        ]
        print(f"chat.get_context_emb - len(seg_tokens): {len(seg_tokens)}")
        for i in range(len(seg_tokens)):
            print(f"seg_tokens[{i}].size(): {seg_tokens[i].size()}")
        seg_embs = [self.model.llama_model.model.embed_tokens(seg_t) for seg_t in seg_tokens]
        #print(f"chat.get_context_emb - seg_embs[:3]: {seg_embs[:3]}")
        mixed_embs = [emb for pair in zip(seg_embs[:-1], self.img_list) for emb in pair] + [seg_embs[-1]]
        mixed_embs = torch.cat(mixed_embs, dim=1)
        print(f"chat.get_context_emb - mixed_embs.size(): {mixed_embs.size()}")
        return mixed_embs

    def clear(self):
        self.img_list = []
        self.conv.messages = []

if __name__ =='__main__':
    video_path = '/mnt/workspace/videoGPT/Video-LLaMA/examples/applausing.mp4'
    # import torch.classes.torchaudio.ffmpeg_StreamReader
    # ffmpeg_StreamReader(video_path)
    load_and_transform_audio_data([video_path],"cpu",  clips_per_video=8)
