# pipeline.py
import luigi
from .tasks.vision_task import ProcessImageTask
from .tasks.vector_task import GenerateVectorTask
from .tasks.db_task import SaveToSupabaseTask

class MemeProcessingPipeline(luigi.WrapperTask):
    image_urls = luigi.ListParameter()
    
    def requires(self):
        for url in self.image_urls:
            yield SaveToSupabaseTask(url)

if __name__ == "__main__":
    luigi.build([
        MemeProcessingPipeline(image_urls=[
            "https://images.bingbing.tv/a9b3427106efce0976f97dda4be2274bfd2368c66d68b6ea8452f3e7b6f4b9d9.jpeg"
        ])
    ])