# 定义 LangGraph 的全局状态结构
from typing import TypedDict, List, Optional, Dict, Any

class StoryboardItem(TypedDict):
    """单个分镜的数据结构"""
    id: int
    text_content: str           # 口播文案
    emotion: str                # 情感标签(FAKE)
    visual_prompt: str          # 画面提示词
    visual_tags: List[str]      # 画面标签（用于转场判断）
    estimated_duration: float   # 预估时长(FAKE)
    

    # 以下字段在后续流程中填充
    audio_path: Optional[str]   # 生成的音频文件路径
    audio_duration: Optional[float]       # 实际音频时长
    image_path: Optional[str]   # 校验通过的图片路径
    video_path: Optional[str]   # 最终生成的视频片段路径
    visual_extend_prompt: Optional[str] = None  # 阿里云的视频生成接口会自动优化传入的prompt

class GraphState(TypedDict):
    """LangGraph 的全局状态"""
    # 输入
    topic: str
    user_params: Dict[str, Any] # 风格、宽高比等

    # 阶段 0: 锚点
    anchor_style_prompt: str    # 全局风格提示词(没有用到啊，怎么能这样，应该作为输入信息之一加入VLM中图像的生成节点中)
    anchor_character_img: str   # 主角/基准参考图路径

    # 阶段 1: 脚本
    storyboard: List[StoryboardItem] # 分镜列表
    bgm_style: str              # BGM 搜索关键词

    # 阶段 2: 生产状态 (用于并行控制)
    audio_ready: bool
    visual_ready: bool

    # 阶段 3: 产出
    final_video_path: str
    logs: List[str]