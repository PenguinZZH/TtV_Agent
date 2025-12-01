import os
from typing import List, Dict, Any
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    ColorClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips,
    fadein, fadeout, speedx, resize
)


class VideoEditorService:
    def __init__(self):
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        # 配置 ImageMagick 路径 (Windows用户通常需要手动指定，Linux/Mac通常不需要)
        # from moviepy.config import change_settings
        # change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe"})

    def _create_visual_clip(self, clip_data: Dict[str, Any]) -> VideoFileClip:
        """根据素材创建基础视频片段，并强制对齐时长"""
        video_path = clip_data.get("video_path")
        image_path = clip_data.get("image_path")
        target_duration = clip_data.get("target_duration")
        
        clip = None
        
        # 1. 加载素材
        if video_path and os.path.exists(video_path):
            clip = VideoFileClip(video_path)
            # 视频变速处理 (Time Stretch)
            if clip.duration and clip.duration > 0:
                speed_factor = clip.duration / target_duration
                # 限制变速倍率，防止过于鬼畜 (0.5x - 3.0x)
                if 0.5 <= speed_factor <= 3.0:
                    clip = clip.fx(speedx, speed_factor)
                else:
                    # 差异太大时，截取或循环，这里简化为截取
                    pass 
        elif image_path and os.path.exists(image_path):
            clip = ImageClip(image_path)
            # 图片加一点缓慢缩放效果 (Ken Burns)
            # clip = clip.fx(resize, lambda t: 1 + 0.04 * t) 
        else:
            # 缺失素材，使用黑屏
            clip = ColorClip(size=(1280, 720), color=(0,0,0))

        # 2. 强制设置时长
        clip = clip.set_duration(target_duration)
        
        # 3. 统一分辨率 (防止合成报错)
        clip = clip.resize(newsize=(1280, 720)) 
        
        # 4. 绑定音频
        audio_path = clip_data.get("audio_path")
        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            # 确保音频时长不超过视频 (裁掉尾部静音)
            audio = audio.set_duration(min(audio.duration, target_duration))
            clip = clip.set_audio(audio)
            
        return clip

    def _create_subtitle_clips(self, subtitles: List[Dict], video_w: int, video_h: int) -> List[TextClip]:
        """生成字幕层列表"""
        subs = []
        # 字体配置 (注意: 需要系统中有该字体，否则会报错，建议用 Arial 或 SimHei)
        font_name = "Arial-Bold" if os.name == 'nt' else "Helvetica-Bold"
        fontsize = 40
        
        for item in subtitles:
            txt = item['text']
            start = item['start']
            duration = item['end'] - item['start']
            
            # 创建 TextClip
            try:
                txt_clip = TextClip(
                    txt, 
                    fontsize=fontsize, 
                    color='white', 
                    font=font_name, 
                    stroke_color='black', 
                    stroke_width=2,
                    size=(video_w - 100, None), # 限制宽度自动换行
                    method='caption'
                )
                
                txt_clip = (txt_clip
                            .set_position(('center', 'bottom')) # 底部居中
                            .set_start(start)
                            .set_duration(duration))
                
                subs.append(txt_clip)
            except Exception as e:
                print(f"[Subtitle Error] Failed to create text clip for: {txt}. Error: {e}")
                # 即使字幕失败，也不要阻断流程
                continue
                
        return subs

    def render_final_video(self, clips: List[Dict], subtitles: List[Dict], bgm_style: str, output_filename: str) -> str:
        """
        主渲染流程
        """
        print("[Editor] Starting render pipeline...")
        
        video_clips_objects = []
        
        # 1. 处理每一个片段 (转场逻辑在这里)
        for i, clip_data in enumerate(clips):
            v_clip = self._create_visual_clip(clip_data)
            
            # 添加转场 (Transitions)
            # 逻辑: 除了第一个片段，每个片段都淡入 0.5秒
            # 注意: MoviePy 的 concatenate 默认是硬切，compose 模式支持重叠
            if i > 0:
                v_clip = v_clip.crossfadein(0.5)
            
            video_clips_objects.append(v_clip)

        # 2. 视频拼接 (Concatenate)
        # padding=-0.5 意味着每个片段和上一个片段重叠 0.5秒 (用于 Crossfade)
        final_video = concatenate_videoclips(video_clips_objects, method="compose", padding=-0.5)

        # 3. 叠加字幕 (Composite)
        if subtitles:
            print(f"[Editor] Overlaying {len(subtitles)} subtitles...")
            subtitle_clips = self._create_subtitle_clips(subtitles, final_video.w, final_video.h)
            # 将视频底与字幕层合并
            final_video = CompositeVideoClip([final_video] + subtitle_clips)

        # 4. 处理 BGM (可选)
        # if bgm_path:
        #    ... (参考之前的 BGM 逻辑)

        # 5. 导出文件
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"[Editor] Writing video file to {output_path}...")
        final_video.write_videofile(
            output_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            preset="medium", # ultrafast 测试用, medium 生产用
            threads=4,
            logger='bar'
        )
        
        # 6. 清理内存 (重要! MoviePy 容易内存泄漏)
        # final_video.close()
        # for c in video_clips_objects: c.close()
        
        return output_path