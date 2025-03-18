import gradio as gr
import requests


API_ENDPOINT = "http://localhost/upload-image"
def gradio_upload(image_file):
    try:
        with open(image_file, "rb") as f:
            response = requests.post(
                API_ENDPOINT,
                files={"file": f},
                # 如果需要携带认证信息
                # headers={"Authorization": f"Bearer {TOKEN}"}
            )
        return response.json().get("message", "上传成功")
    except Exception as e:
        return f"上传错误：{str(e)}"
def create_gradio_app():
# 使用 Blocks 获得更多配置能力
    with gr.Blocks(
        title="文件上传系统",
        # max_file_size="100MB",  # 核心配置项
        theme=gr.themes.Soft()
    ) as demo:
        # 创建交互界面
        gr.Markdown("## 企业文件上传平台")
        with gr.Row():
            with gr.Column():
                img_input = gr.Image(
                    type="filepath",
                    label="请选择图片文件",
                    image_mode="RGB",
                    sources=["upload", "clipboard"]
                )
                upload_btn = gr.Button("提交到服务器", variant="primary")
            with gr.Column():
                proc_output = gr.Image(label="处理结果")
                text_output = gr.JSON(label="服务器响应")

        # 绑定处理逻辑
        upload_btn.click(
            fn=gradio_upload,  # 你的处理函数
            inputs=img_input,
            outputs=[proc_output, text_output]
        )

    # 附加配置（可选）
    # demo.app.proxy_headers = True  # 适用于反向代理场景
    return demo.app
