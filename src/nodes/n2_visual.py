# 视觉并行流(含生成-校验循环)
import os
from src.core.state import GraphState
from src.services.media_service import MediaGenService
from src.services.llm_service import LLMService

media_service = MediaGenService()
vlm_service = LLMService()

FORCE_EXECUTE = os.getenv("FORCE_EXECUTE")

def visual_node(state: GraphState) -> GraphState:
    """节点：视觉生成流
    功能：生图 -> 校验 -> (重试) -> 生视频
    注意：这是一个耗时操作
    """
    print("--- Starting Visual Pipeline ---")       # 开始视觉流
    anchor_img = state['anchor_character_img']      # 主角/基准参考图路径
    
    updated_storyboard = []
    
    for shot in state['storyboard']:        # 分镜列表
        id = shot["id"]
        prompt = shot['visual_prompt']      # 画面提示词
        video_path = None                   # 视频路径
        
        # === 内部循环：生图 + 校验 (最多重试3次) ===
        for attempt in range(3):
            # 1. 生图
            img_path = media_service.generate_image_with_control(id, prompt, anchor_img)
            
            # 2. VLM 校验
            check_result = vlm_service.validate_image_quality(img_path, prompt)
            
            if check_result['passed']:
                # 3. 校验通过，生成视频
                video_path, visual_extend_prompt = media_service.image_to_video(id, img_path, motion_strength=0.5)
                shot['image_path'] = img_path
                shot['video_path'] = video_path
                shot['visual_extend_prompt'] = visual_extend_prompt
                break # 跳出重试循环
            else:
                # 4. 失败，优化 Prompt 进行下一次尝试
                print(f"第{attempt+1}次失败: Shot {shot['id']} failed: {check_result['reason']}")
                prompt = vlm_service.optimize_prompt(prompt, check_result['reason'])
        
        # 如果3次都没过，强制使用最后一次的图生成视频，或者标记错误
        if not video_path:
             # fallback logic...
            #  logger.error(f"Shot {shot['id']} failed after 3 attempts. Reason: {check_result['reason']}")
            if FORCE_EXECUTE:
                video_path = media_service.image_to_video(img_path, motion_strength=0.5)
                shot['image_path'] = img_path
                shot['video_path'] = video_path
                shot['visual_extend_prompt'] = None
            else:
                raise RuntimeError(f"视觉生成失败: Shot {shot['id']} 连续3次失败")
             
        updated_storyboard.append(shot)

    state['storyboard'] = updated_storyboard
    state['visual_ready'] = True
    return state