# Graph组装
from langgraph.graph import StateGraph, END
from src.core.state import GraphState
from src.nodes import n0_init, n1_script, n2_audio, n2_visual, n3_merge

def build_app():
    # 1. 初始化 Graph
    workflow = StateGraph(GraphState)

    # 2. 添加节点
    workflow.add_node("init", n0_init.init_node)            # 初始化与锚点生成
    workflow.add_node("script", n1_script.script_node)      # 脚本与分镜规划
    workflow.add_node("audio_gen", n2_audio.audio_node)     # 音频并行流
    workflow.add_node("visual_gen", n2_visual.visual_node)  # 视觉并行流 (含生成-校验循环)
    workflow.add_node("merge", n3_merge.merge_node)         # 后期合成

    # 3. 定义边 (流程走向)
    # Start -> Init -> Script
    workflow.set_entry_point("init")
    workflow.add_edge("init", "script")

    # Script -> (并行) Audio & Visual
    # 在 LangGraph 中，从一个节点指向多个节点即代表分支
    workflow.add_edge("script", "audio_gen")
    workflow.add_edge("script", "visual_gen")

    # (并行) -> Merge
    # Merge 节点需要等待 Audio 和 Visual 都完成。
    # 注意：LangGraph 默认等待所有前置分支完成才会进入汇聚节点。
    workflow.add_edge(["audio_gen", "visual_gen"], "merge")

    # Merge -> End
    workflow.add_edge("merge", END)

    return workflow.compile()

if __name__ == "__main__":
    app = build_app()
    
    # 启动输入
    initial_input = {
        "topic": "赛博朋克风格的侦探故事",
        "user_params": {"ratio": "16:9", "duration": "short"}
    }
    
    print("--- Workflow Started ---")
    result = app.invoke(initial_input)
    print(f"--- Finished! Video saved at: {result['final_video_path']} ---")