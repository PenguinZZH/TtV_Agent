import mimetypes
import base64


def encode_image(img_path: str):
    mime_type = mimetypes.guess_type(img_path)  # 判断文件类型
    if not mime_type:  # 如果img_path没有后缀，则默认为jpeg类型
        mime_type = "image/jpeg"

    with open(img_path, 'rb') as image_file:
        base64_data = base64.b64encode(image_file.read()).decode('utf-8')

    # 返回 OpenAI 格式要求的 Data URL
    return f"data:{mime_type};base64,{base64_data}"