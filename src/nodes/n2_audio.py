# 音频并行流
from src.core.state import GraphState
from src.services.media_service import MediaGenService

media_service = MediaGenService()

def audio_node(state: GraphState) -> GraphState:
    """
    Node 2A: 音频生成
    功能:
    1. 遍历分镜，生成 TTS 语音。
    2. 获取音频精确时长，回写到 Storyboard。
    """
    print("--- [N2_Audio] Generating Voiceovers ---")
    
    # 获取当前的分镜列表
    current_storyboard = state["storyboard"]    # 当前分镜列表
    updated_storyboard = []

    for item in current_storyboard:
        id = item[id]
        text = item["text_content"]     # 文本内容
        emotion = item["emotion"]       # 情感

        print(f"-> Processing Audio for Scene {item['id']}...")
        
        # 1. 生成 TTS: 生成音频(路径), 持续时间
        audio_path, duration = media_service.text_to_speech(id, text, emotion)
        
        # 2. 更新 Item
        # 注意：这里不要直接修改 item，最好创建副本或更新引用
        item_copy = item.copy()
        item_copy["audio_path"] = audio_path
        item_copy["audio_duration"] = duration  # 这里是Fake数据，Audio并没有依据此数据生成
        
        updated_storyboard.append(item_copy)

    print("-> Audio processing complete.")

    return {
        "storyboard": updated_storyboard, # LangGraph 会处理这里与 Visual 节点的合并(通常需要看具体reducer配置，或假设这是独立更新)
        # 注意：在真实的并发场景下，最好将 Audio 和 Visual 的结果存储在 State 的不同字段中，或者在 Merge 阶段再合并。
        # 但为了简化，假设 LangGraph 可以处理 dict merge，或者我们在 n3 中统一读取。
        # **更稳妥的做法**: 将音频结果存入一个临时 dict，例如 state['audio_results'] = {id: path}，在 n3 合并。
        # 但这里我们假设串行或者最后由 LangGraph 的 Reducer 处理。
        "audio_ready": True,
        "logs": state.get("logs", []) + ["Audio tracks generated."]
    }