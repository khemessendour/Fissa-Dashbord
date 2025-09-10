import pandas as pd
from src.config import DATA_FILE_PATH, DATA_DICT_FILE_PATH # type: ignore


def load_data_and_dict() -> tuple:
   """
   Load the dataset and the data dictionary
   Dataset files should not be renamed !
   :param data_folder: folder where the dataset is stored
   :return: tuple of the dataset and the data dictionary
   """
   df = pd.read_csv(DATA_FILE_PATH)   
   dictionnary = pd.read_csv(DATA_DICT_FILE_PATH)
   return df, dictionnary
