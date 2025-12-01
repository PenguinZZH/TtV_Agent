import json
import os
import base64
import mimetypes

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, human
from langchain_core.output_parsers import JsonOutputParser

from utils.tools import encode_image
from utils.universal_prompt import vlm_system_message

# 定义分镜的输出结构，强制 LLM 遵守
class StoryboardItemSchema(BaseModel):
    text_content: str = Field(description="The spoken narration text")
    emotion: str = Field(description="The emotion of the narration (e.g., excited, sad)")
    visual_prompt: str = Field(description="Detailed prompt for image generation")
    visual_tags: List[str] = Field(description="List of visual tags (e.g., ['close-up', 'blue'])")
    estimated_duration: float = Field(description="Estimated duration in seconds")

class StoryboardList(BaseModel):
    items: List[StoryboardItemSchema]

class LLMService:
    def __init__(self):
        # 这里的 API Key通常从环境变量读取
        # 这里应该是个多模态模型: img-text to text
        api_key = os.getenv("GEMINI_API_KEY")
        api_base = os.getenv("GEMINI_API_BASE")
        model = os.getenv("MODEL_NAME")

        self.llm = init_chat_model(
            model = model,
            openai_api_base=api_base,
            openai_api_key=api_key,
        )

    def refine_style(self, topic: str, user_style: str) -> str:
        """将用户简短的风格描述扩展为详细的 Prompt"""
        if not self.llm:
            return f"Cinematic shot, {user_style}, high detailed, consistent lighting, related to {topic}, 8k resolution."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是艺术总监。基于Topic，将用户输入的Style展开为详细的图像生成提示"),
            ("user", "Topic: {topic}\nStyle: {style}")
        ])
        chain = prompt | self.llm
        return chain.invoke({"topic": topic, "style": user_style}).content


    def generate_storyboard(self, topic: str, style_prompt: str) -> List[Dict]:
        """生成结构化分镜脚本"""
        if not self.llm:
            # MOCK DATA: 如果没有配置 LLM，返回假数据
            print("[LLMService] Using Mock Storyboard Data")
            return [
                {
                    "text_content": f"Welcome to the world of {topic}.",
                    "emotion": "mysterious",
                    "visual_prompt": f"Wide shot of {topic}, {style_prompt}, cinematic lighting",
                    "visual_tags": ["wide-shot", "intro"],
                    "estimated_duration": 3.0
                },
                {
                    "text_content": "Everything changes here.",
                    "emotion": "intense",
                    "visual_prompt": f"Close up details of {topic}, dramatic shadows",
                    "visual_tags": ["close-up", "drama"],
                    "estimated_duration": 2.5
                }
            ]

        # 使用 Pydantic parser 保证 JSON 格式正确
        parser = JsonOutputParser(pydantic_object=StoryboardList)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个视频导演。根据Topic生成一个故事板。严格返回JSON."),
            ("user", "Topic: {topic}\nVisual Style: {style}\n\n{format_instructions}")
        ])

        chain = prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "topic": topic, 
                "style": style_prompt,
                "format_instructions": parser.get_format_instructions()
            })
            return result['items'] # 返回列表
        except Exception as e:
            print(f"[LLM Error] {e}")
            return []


    def validate_image_quality(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """VLM 视觉校验"""
        # 获取Base64编码
        try:
            image_data_url = encode_image(image_path)

            # 构建多模态Messages
            sys_msg = SystemMessage(content=vlm_system_message)
            human_msg = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url}
                    }
                ]
            )
            resposne = self.llm.invoke([sys_msg, human_msg])
            alignment_score = resposne.prompt_image_alignment_score
            quality_score = resposne.visual_quality_score
            satisfy_judge = resposne.is_prompt_satisfied
            problems = resposne.problems
            positive_aspects = resposne.positive_aspects
            overall_comment = resposne.overall_comment

            if satisfy_judge and (alignment_score + quality_score > 12):
                return {
                    "passed": True,
                    "reason": positive_aspects,
                }
            else:
                return {
                    "passed": False,
                    "reason": problems,
                    "suggestion": overall_comment,
                }

        except Exception as e:
            print(f"发现错误: {e}")


    def optimize_prompt(self, original_prompt: str, reason: str) -> str:
        """根据失败原因优化 Prompt"""
        return f"{original_prompt}, corrected {reason}, high quality, fixed anatomy"




