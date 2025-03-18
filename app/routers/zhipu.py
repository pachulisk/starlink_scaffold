import os
from zhipuai import ZhipuAI

ZHIPUAI_KEY = os.getenv('ZHIPUAI_KEY')  
zhipuClient = ZhipuAI(api_key=ZHIPUAI_KEY)  # 请填写您自己的API Key
print(zhipuClient)