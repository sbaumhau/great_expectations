import os

from .base import DataContext
from ..dataset.sparkdf_dataset import SparkDFDataset

from pyspark.sql import SparkSession


class SparkCSVDataContext(DataContext):
    """For now, functions like PandasCSVDataContext
    """

    def __init__(self, options, *args, **kwargs):
        super(SparkCSVDataContext, self).__init__(options, *args, **kwargs)
        self.spark = SparkSession.builder.getOrCreate()

    def connect(self, options):
        self.directory = options

    def list_datasets(self):
        return os.listdir(self.directory)

    def get_dataset(self, dataset_name, *args, caching=False, **kwargs):
        reader = self.spark.read
        for option in kwargs.items():
            reader = reader.option(*option)
        df = reader.csv(os.path.join(self.directory, dataset_name))
        return SparkDFDataset(df, caching=caching)
