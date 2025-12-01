# 初始化与锚点生成
from src.core.state import GraphState
from src.services.llm_service import LLMService
from src.services.media_service import MediaGenService

# 初始化服务实例
llm_service = LLMService()
media_service = MediaGenService()

def init_node(state: GraphState) -> GraphState:
    """
    Node 0: 初始化
    功能:
    1. 基于用户 Topic 扩展出详细的风格 Prompt。
    2. 生成并固定全片的主角/场景锚点图 (Anchor Image)。
    """
    print(f"--- [N0_Init] 待处理主题: {state['topic']} ---")
    
    topic = state["topic"]      # 主题
    user_style = state["user_params"].get("style", "cinematic")     # 风格(Default: 电影级的)

    # 1. 使用 LLM 优化风格描述
    anchor_style_prompt = llm_service.refine_style(topic, user_style)

    # 2. 生成锚点参考图 (Character/Scene Anchor)
    # 这张图将作为后续所有 IP-Adapter 的输入
    anchor_img_path = media_service.generate_reference_image(anchor_style_prompt)

    # 3. 更新状态
    # 注意：LangGraph 中返回的 dict 会被合并 update 到全局 state 中
    return {
        "anchor_style_prompt": anchor_style_prompt,
        "anchor_character_img": anchor_img_path,
        "logs": [f"Init completed. Anchor saved at {anchor_img_path}"]
    }
