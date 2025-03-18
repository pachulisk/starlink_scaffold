import luigi
from .zhipu import zhipuClient

class ProcessImageTask(luigi.Task):
    image_url = luigi.Parameter()
    
    def output(self):
        return luigi.LocalTarget(f"tmp/{self.image_url.split('/')[-1]}.txt")
    
    def run(self):
        # 调用智谱视觉API
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
                        "url" : f"{self.image_url}"
                    }
                }
                ]
            }
            ]
        )
        message = response.choices[0].message
        with self.output().open('w') as f:
            f.write(str(message.content))