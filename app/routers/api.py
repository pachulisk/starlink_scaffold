from fastapi import APIRouter, File, UploadFile, HTTPException, Response
from starlette.background import BackgroundTask
from typing import Optional
from .supabase import supabase
from .zhipu import zhipuClient
import httpx
import luigi
import base64
# from .chroma import chroma
from .db_task import SaveToSupabaseTask
from pydantic import BaseModel
from .utils import stringq2b
import requests
import time
import re

api = APIRouter()

# 内部上传服务的配置
INTERNAL_UPLOAD_URL = "https://r2-worker.pachulisk.workers.dev/upload"
ACCESS_URL_TEMPLATE = "https://r2-worker.pachulisk.workers.dev/{key}"  # 根据实际访问URL格式调整


# 允许的文件类型白名单
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

async def upload_to_internal_service(image_data: bytes, filename: str, content_type: str) -> str:
    """
    调用内部上传服务
    返回: 上传成功后得到的文件key
    """
    files = {
        "image": (filename, image_data, content_type)
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                INTERNAL_UPLOAD_URL,
                files=files,
                timeout=30.0  # 根据实际情况调整超时时间
            )
            response.raise_for_status()
            print(response)
            print(response.text)
            return response.text.strip()  # 假设直接返回key字符串
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"内部上传服务错误: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"无法连接内部服务: {str(e)}"
            )

@api.post("/upload-image/", tags=["api"])
async def upload_image(
    file: UploadFile = File(..., description="上传的图片文件"),
    max_size: Optional[int] = 5 * 1024 * 1024  # 默认限制5MB
):
  """
  上传图片文件接口
  
  参数:
  - file: 上传的文件对象
  - max_size: 可选参数，自定义最大文件大小（字节）
  
  返回:
  - 包含文件名和访问URL的JSON响应
  """
  # 验证文件类型
  if file.content_type not in ALLOWED_MIME_TYPES:
    print(f"file.content_type = {file.content_type}")
    raise HTTPException(
        status_code=400,
        detail=f"不支持的文件类型 {file.content_type}。仅支持：{', '.join(ALLOWED_MIME_TYPES)}"
    )
  # 验证文件大小
  file.file.seek(0, 2)  # 移动到文件末尾
  file_size = file.file.tell()
  file.file.seek(0)  # 重置文件指针
  if file_size > max_size:
      raise HTTPException(
          status_code=413,
          detail=f"文件过大（{file_size} 字节）。最大允许 {max_size} 字节"
      )
  try:
    # 读取文件内容
    contents = await file.read()
    print(f"filename = {file.filename}")
    # 调用内部上传服务
    file_key = await upload_to_internal_service(
        image_data=contents,
        filename=file.filename,
        content_type=file.content_type
    )

    # 构造访问URL
    access_url = ACCESS_URL_TEMPLATE.format(key=file_key)

    # 将url和文件相关内容存储到supabase
    table_name = 'images'
    img_data = {
        "filename": file_key,
        "fullurl": access_url,
        "descriptions": "",
    }
    _ = supabase.table(table_name).insert(img_data).execute()

    # 返回响应
    return {
        "key": file_key,
        "access_url": access_url,
        "content_type": file.content_type,
        "size": file_size
    }
  except Exception as e:
      if isinstance(e, HTTPException):
          raise
      raise HTTPException(
          status_code=500,
          detail=f"上传失败: {str(e)}"
      )
  
# 添加新的GET接口
@api.get("/images/{key}", responses={
    200: {
        "content": {"image/*": {}},
        "description": "成功返回图片内容",
    }
}, tags=["api"])
async def get_image(
    key: str,
    download: bool = False,  # 可选参数控制下载行为
    max_retries: int = 3     # 重试次数
):
    """
    通过key代理访问图片
    
    参数:
    - key: 图片的唯一标识符
    - download: 是否强制作为附件下载（默认false直接展示）
    - max_retries: 请求内部服务的重试次数
    
    返回:
    - 图片二进制流或错误响应
    """
    target_url = ACCESS_URL_TEMPLATE.format(key=key)
    
    # 配置请求头（可根据需要扩展）
    headers = {
        "User-Agent": "ImageProxy/1.0",
    }

    async def close_response(response: httpx.Response):
        """确保响应正确关闭"""
        await response.aclose()

    async with httpx.AsyncClient() as client:
        for attempt in range(max_retries):
            try:
                response = await client.get(
                    target_url,
                    headers=headers,
                    timeout=10.0,  # 分项超时设置
                    follow_redirects=True
                )
                
                # 处理成功响应
                if response.status_code == 200:
                    # 构建返回头
                    headers = {
                        "Content-Type": response.headers.get("Content-Type", "application/octet-stream"),
                        "Cache-Control": "public, max-age=86400"  # 24小时缓存
                    }
                    
                    # 处理下载参数
                    if download:
                        headers["Content-Disposition"] = f"attachment; filename={key}"
                    
                    return Response(
                        content=response.content,
                        headers=headers,
                        background=BackgroundTask(close_response, response)
                    )
                
                # 处理错误状态码
                if 400 <= response.status_code < 500:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"上游服务错误：{response.text[:200]}"
                    )
                else:
                    continue  # 5xx错误重试

            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503,
                        detail=f"无法连接上游服务：{str(e)}"
                    )
                continue

        # 最终重试失败
        raise HTTPException(
            status_code=504,
            detail="上游服务响应超时"
        )
@api.post("/zhipu", tags=["api"])
async def zhipu():
    response = zhipuClient.chat.completions.create(
    model="glm-4v",  # 填写需要调用的模型名称
        messages=[
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": "图里有什么"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url" : "https://images.bingbing.tv/a9b3427106efce0976f97dda4be2274bfd2368c66d68b6ea8452f3e7b6f4b9d9.jpeg"
                }
            }
            ]
        }
        ]
    )
    return response.choices[0].message

class TestLuigi(BaseModel):
    url: str

@api.post("/test_luigi_hello", tags=["api"])
async def test_luigi_hello(params: TestLuigi):
    url = params.url
    try:
        # 运行Luigi任务
        luigi.build([SaveToSupabaseTask(url)], local_scheduler=True)
        return {"message": "Luigi task completed successfully"}
    except Exception as e:
        return {"error": str(e)}
    
# 定义请求体模型
class QueryRequest(BaseModel):
    text: str
    n_results: int = 1  # 默认返回1个结果

# @api.post("/search-images/", tags=["api"])
# async def search_images(query: QueryRequest):
#     try:
#         # 使用Chroma进行查询
#         results = chroma.query(
#             query_texts=[query.text],
#             n_results=query.n_results
#         )
        
#         # 提取返回的URL（即id）
#         urls = results["ids"][0]
#         return {"results": urls}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"搜索失败: {str(e)}"
#         )
    
def get_stock_data(stocks):
    timestamp = int(time.time() * 1000)
    headers = {
        "host": "hq.sinajs.cn",
        "referer": "https://vip.stock.finance.sina.com.cn/",
        "user - agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    url = f"https://hq.sinajs.cn/rn={timestamp}&list={','.join(stocks)}"
    res = requests.get(url, headers=headers)
    parsed_data = []
    pattern = re.compile(r'var hq_str_s_(\w+)="(.*?)";')
    matches = pattern.findall(res.text)
    for code, values in matches:
        values_list = values.split(',')
        parsed_data.append({
            'code': code,
            'name': values_list[0],
            'current_value': float(values_list[1]),
            'change': float(values_list[2]),
            'change_percent': float(values_list[3]),
            'volume': values_list[4],
            'turnover': values_list[5]
        })
    return parsed_data
    
@api.post("/get_indexes", tags=["api"])
async def get_indexes():
    # 指数代码列表
    stocks = ["s_sh000001", "s_sz399001", "s_sz399006", "s_sh000300", "s_sh000688"]
    data = get_stock_data(stocks)
    lst = []
    for item in data:
        # x * (1+change_percent) = currnet_value
        current_value = item.get("current_value") 
        change_percent = item.get("change_percent")
        original_value = current_value / (1 + change_percent / 100) if change_percent != 0 else current_value
        change_value = current_value - original_value
        lst.append(f"指数代码：{item['code']}，名称：{item['name']}，最近收盘价：{item['current_value']}，涨跌幅：{change_percent}%，涨跌值：{change_value}")
    return {"data": lst}

class Q2BRequest(BaseModel):
    text: str

@api.post("/q2b", tags=["api"])
async def q2b_endpoint(request: Q2BRequest):
    text = request.text
    # 这个text是经过base64加密的，需要解码
    text = base64.b64decode(text).decode('utf-8')
    converted = stringq2b(text)
    converted_text = base64.b64encode(converted.encode("utf-8"))
    return {"converted_text": str(converted_text, 'utf-8')}
