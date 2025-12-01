# 后期合成
import os
from typing import List, Dict, Any
from src.core.state import GraphState, StoryboardItem
from src.services.editor_service import VideoEditorService

# 初始化剪辑服务
editor_service = VideoEditorService()

def merge_node(state: GraphState) -> GraphState:
    """
    Node 3: 后期合成与渲染
    功能:
    1. 数据清洗: 检查音频/视频素材是否完整。
    2. 时间轴计算: 根据音频时长，计算每一句话的字幕 Start/End 时间。
    3. 调用 Service: 执行物理渲染 (转场、字幕、BGM)。
    """
    print("--- [N3_Merge] Final Editing & Rendering ---")
    
    # 1. 获取所有素材数据
    # 注意: 在并行流结束后，假设 state['storyboard'] 已包含了 audio_path 和 video_path
    full_storyboard = state.get("storyboard", [])
    bgm_style = state.get("bgm_style", "cinematic")
    
    if not full_storyboard:
        return {"logs": state.get("logs", []) + ["Error: Storyboard is empty."]}

    # 2. 数据清洗与对齐 (Data Validation & Alignment)
    # 我们需要构建一个用于剪辑的干净列表
    clips_to_process = []
    
    # 用于计算字幕时间轴的累加器
    current_timestamp = 0.0
    subtitle_data = [] # 格式:List[{text, start, end}]

    print(f"-> Analyzing timeline for {len(full_storyboard)} clips...")

    for item in full_storyboard:
        clip_id = item.get("id")
        audio_path = item.get("audio_path")
        video_path = item.get("video_path")
        image_path = item.get("image_path")
        text = item.get("text_content", "")
        
        # 2.1 确定本片段的基准时长 (Duration Strategy)
        # 优先级: 真实音频时长 > 预估时长
        duration = item.get("audio_duration")
        if not duration:
            duration = item.get("estimated_duration", 3.0)
        
        # 2.2 检查素材完整性
        # 如果没有视频，回退到图片；如果图片也没有，标记为黑屏(由Editor处理)
        has_visual = (video_path and os.path.exists(video_path)) or \
                     (image_path and os.path.exists(image_path))
        
        if not has_visual:
            print(f"   [Warning] Scene {clip_id} missing visuals. Will use placeholder.")

        # 2.3 构建字幕数据 (Subtitle Logic)
        # 只有当有文字且时长有效时才生成字幕
        if text and duration > 0.5:
            subtitle_data.append({
                "text": text,
                "start": current_timestamp,
                "end": current_timestamp + duration
            })

        # 2.4 将清洗后的数据加入待处理列表
        clips_to_process.append({
            "id": clip_id,
            "video_path": video_path,
            "image_path": image_path,
            "audio_path": audio_path,
            "target_duration": duration, # 告诉编辑器：无论视频多长，必须强行缩放至这个时长
            "visual_prompt": item.get("visual_prompt", "") # 用于可能的元数据记录
        })
        
        # 更新时间轴指针
        current_timestamp += duration

    print(f"-> Total duration estimate: {current_timestamp:.2f} seconds")
    print(f"-> Generated {len(subtitle_data)} subtitle lines.")

    # 3. 调用 Editor Service 进行物理渲染
    # 我们将“片段列表”和“字幕列表”分开传，逻辑更清晰
    try:
        final_video_path = editor_service.render_final_video(
            clips=clips_to_process,
            subtitles=subtitle_data,
            bgm_style=bgm_style,
            output_filename=f"final_{state['topic'].replace(' ', '_')}.mp4"
        )
        
        status_log = f"Success. Video saved at {final_video_path}"
    except Exception as e:
        import traceback
        traceback.print_exc()
        final_video_path = ""
        status_log = f"Error during rendering: {str(e)}"

    # 4. 更新 State
    return {
        "final_video_path": final_video_path,
        "logs": state.get("logs", []) + [status_log]
    }