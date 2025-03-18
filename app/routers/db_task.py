import luigi
from .supabase import supabase
from .vector_task import GenerateVectorTask
# from .vision_task import ProcessImageTask
TABLE_NAME = "images"

class SaveToSupabaseTask(luigi.Task):
    image_url = luigi.Parameter()
    
    def requires(self):
        return GenerateVectorTask(self.image_url)
        # return ProcessImageTask(self.image_url)
    
    def run(self):
        with self.input().open() as f:
            description = f.read()
        supabase.table(TABLE_NAME).update({"descriptions": description}).eq("fullurl", self.image_url).execute()