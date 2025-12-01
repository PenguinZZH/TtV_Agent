# 脚本与分镜规划
from src.core.state import GraphState
from src.services.llm_service import LLMService

llm = LLMService()

def script_node(state: GraphState) -> GraphState:
    """
    节点：脚本生成
    功能：基于主题生成分镜脚本
    """
    print(f"--- Generating Script for: {state['topic']} ---")
    
    # 1. 调用 LLM
    storyboard_json = llm.generate_storyboard(
        topic=state['topic'],
        style=state['user_params'].get('style', 'cinematic')    # 取style字段, 没有则默认返回'cinematic'(电影级的)
    )
    
    # 2. 简单的后处理（例如为每个镜头分配唯一ID）
    for i, item in enumerate(storyboard_json):
        item['id'] = i
        
    # 3. 更新状态
    state['storyboard'] = storyboard_json
    return state