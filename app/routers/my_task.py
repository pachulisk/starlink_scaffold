import luigi

class MyTask(luigi.Task):
    def output(self):
        return luigi.LocalTarget('output.txt')

    def run(self):
        with self.output().open('w') as f:
            f.write('Hello, Luigi!')