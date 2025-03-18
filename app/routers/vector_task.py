import luigi
from sentence_transformers import SentenceTransformer
from .vision_task import ProcessImageTask
# from .chroma import chroma

class GenerateVectorTask(luigi.Task):
    image_url = luigi.Parameter()
    
    def requires(self):
        return ProcessImageTask(self.image_url)
    
    def output(self):
        return luigi.LocalTarget(f"tmp/{self.image_url.split('/')[-1]}.vec")
    
    def run(self):
        # 读取描述文本
        with self.input().open() as f:
            description = f.read()
        
        # 生成向量
        # model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        # vector = model.encode(description).tolist()
        
        # 存储到ChromaDB
        # chroma.upsert(
        #     ids=[self.image_url],
        #     documents=[description],
        # )
        
        with self.output().open('w') as f:
            f.write(str(description))