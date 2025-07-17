import os
from dotenv import load_dotenv

load_dotenv() 

class Config:
    DB_HOST = os.getenv('DB_HOST')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAME = os.getenv('DB_NAME')
    SELENOID_HUB_URL = os.getenv('SELENOID_HUB_URL')

    NADA_CONSTA = 'Não existem informações disponíveis para os parâmetros informados.'
    CONSTA01 = 'Processos encontrados'
    CONSTA02 = 'Audiências'
    