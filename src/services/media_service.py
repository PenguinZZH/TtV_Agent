# 负责生图、生视频、TTS (ComfyUI, Runway, EdgeTTS)
import os
import time
import requests
import random
import dashscope

from datetime import datetime
from pathlib import Path, PurePosixPath
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from dashscope import ImageSynthesis
from dashscope.audio.tts_v2 import *

# 获取当前时间并格式化
time_str = datetime.now().strftime("%m-%d-%H-%M")

# 创建文件保存路径
IMG_DIR = Path("data") / "image" / time_str
IMG_DIR.mkdir(parents=True, exist_ok=True)

AUI_DIR = Path("data") / "audio" / time_str
AUI_DIR.mkdir(parents=True, exist_ok=True)

BOARD_IMG_DIR = Path("data") / "StoryBoard" / time_str
BOARD_IMG_DIR.mkdir(parents=True, exist_ok=True)

VID_DIR = Path("data") / "video" / time_str
VID_DIR.mkdir(parents=True, exist_ok=True)


class MediaGenService:
    def __init__(self):
        # 通义千问-文生图
        self.img_api_key = os.getenv("IMAGE_API_KEY")
        self.img_model_name = os.getenv("IMAGE_MODEL_NAME")

        self.audio_api_key = os.getenv("AUDIO_API_KEY")
        self.audio_model_name = os.getenv("AUDIO_MODEL_NAME")
        self.audio_voice = os.getenv("AUDIO_VOICE")

    def generate_reference_image(self, prompt: str) -> str:
        """生成锚点图 (Anchor Image)"""
        
        dashscope.base_http_api_url = os.getenv("IMAGE_API_BASE")
        response = ImageSynthesis.call(api_key=self.img_api_key,
                          model=self.img_model_name,
                          prompt=prompt,
                          n=1,
                          size='1328*1328',
                          prompt_extend=True,
                          watermark=True)
        
        if response.status_code == HTTPStatus.OK:
            for result in response.output.results:
                file_name = PurePosixPath(unquote(urlparse(result.url).path)).parts[-1]
                save_path = rf"{IMG_DIR}/{file_name}"
                with open(save_path, 'wb+') as f:
                    f.write(requests.get(result.url).content)


        return save_path
        # 生成一个纯色图片作为 Mock
        # return self._create_mock_image("anchor.png", color="blue")


    def generate_image_with_control(self, id: str, prompt: str, anchor_img_path: str) -> str:
        """生成分镜图片 (带一致性控制)
        这里应该是: 用ComfyUI工作流; 目前尚未有合适的接口;  这里可以加入duration参数, 1s一张分镜(这里是个创新点-一键生成分镜) 需要调研下
        刚刚看到一个新开源项目: open-sora; "图生视频"和"文生视频"两类
        """
        print(f"[MediaService] Generating Image: {prompt[:30]}... (Ref: {anchor_img_path})")
        time.sleep(1)
        
        filename = f"board_img_{id}.png"
        board_img_path = rf"{BOARD_IMG_DIR}/{filename}"
        return board_img_path
        # return self._create_mock_image(filename, color="green")


    def image_to_video(self, image_path: str, motion_strength: float = 0.5) -> str:
        """图生视频 (I2V)"""
        print(f"[MediaService] Generating Video from {image_path}...")
        time.sleep(2) # 模拟视频生成耗时
        
        filename = f"vid_{int(time.time())}_{random.randint(0,100)}.mp4"
        return self._create_mock_video(filename, duration=3)


    def text_to_speech(self, id: int, text: str, emotion: str) -> tuple[str, float]:
        """TTS 生成，返回路径和时长"""
        print(f"[MediaService] TTS Generating: {text[:20]}... ({emotion})")
        time.sleep(0.5)
        
        filename = f"audio_{int(time.time())}_{random.randint(0,100)}.mp3"
        # 估算时长：假设英文单词平均 0.3秒
        duration = max(1.5, len(text.split()) * 0.4)    # Qwen系列模型用不上(emotion和duration参数)
        
        dashscope.api_key = self.audio_api_key
        synthesizer = SpeechSynthesizer(model=self.audio_model_name, voice=self.audio_voice)
        audio = synthesizer(text)
        audio_path = rf"{IMG_DIR}/{id}.mp3"
        
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        return audio_path, duration



    # --- Helper Methods for Mocking ---
    

    # def _create_mock_image(self, name: str, color: str) -> str:
    #     """创建一个纯色的图片用于测试"""
    #     from PIL import Image
    #     path = TEMP_DIR / name
    #     img = Image.new('RGB', (1024, 576), color=color) # 16:9
    #     img.save(path)
    #     return str(path)


    # def _create_mock_video(self, name: str, duration: int) -> str:
    #     """创建一个空白视频用于测试"""
    #     from moviepy.editor import ColorClip
    #     path = TEMP_DIR / name
    #     # 创建一个 3秒的 红色视频
    #     clip = ColorClip(size=(1024, 576), color=(200, 0, 0), duration=duration)
    #     clip.write_videofile(str(path), fps=24, logger=None)
    #     return str(path)


    # def _create_mock_audio(self, name: str, duration: float) -> str:
    #     """创建一个静音音频用于测试"""
    #     # 注意：MoviePy 需要真实的音频文件，这里用 subprocess 生成或者用 MoviePy 生成
    #     # 为简便，这里我们生成一个简单的正弦波
    #     from moviepy.audio.tools.cuts import find_audio_period
    #     from moviepy.editor import AudioFileClip
    #     import numpy as np
    #     from scipy.io.wavfile import write
        
    #     path = TEMP_DIR / name
    #     samplerate = 44100
    #     t = np.linspace(0., duration, int(samplerate * duration))
    #     data = np.int16(np.random.uniform(-32768, 32767, int(samplerate * duration)) * 0.1) # 噪音
    #     write(str(path), samplerate, data)
        
    #     return str(path)