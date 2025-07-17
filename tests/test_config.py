import unittest
import os
import importlib
from unittest.mock import patch


import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from config import Config

class TestConfig(unittest.TestCase):

    # Usamos patch.dict para simular as variáveis de ambiente
    @patch.dict(os.environ, {
        'DB_HOST': 'test_db_host',
        'DB_USER': 'test_db_user',
        'DB_PASSWORD': 'test_db_password',
        'DB_NAME': 'test_db_name',
        'SELENOID_HUB_URL': 'http://test_selenoid:4444/wd/hub'
    })
    def test_config_loading_from_env(self):
        
        
        importlib.reload(Config) # Recarregar o módulo Config para pegar as variáveis mockadas

        self.assertEqual(Config.DB_HOST, 'test_db_host')
        self.assertEqual(Config.DB_USER, 'test_db_user')
        self.assertEqual(Config.DB_PASSWORD, 'test_db_password')
        self.assertEqual(Config.DB_NAME, 'test_db_name')
        self.assertEqual(Config.SELENOID_HUB_URL, 'http://test_selenoid:4444/wd/hub')

    # Simula que nenhuma variável de ambiente está definida
    @patch.dict(os.environ, {}) 
    def test_config_missing_env_vars(self):
        
        import importlib
        with self.assertRaises(TypeError): 
            importlib.reload(Config) 

    def test_config_constants(self):
        self.assertEqual(Config.NADA_CONSTA, 'Não existem informações disponíveis para os parâmetros informados.')
        self.assertEqual(Config.CONSTA01, 'Processos encontrados')
        self.assertEqual(Config.CONSTA02, 'Audiências')


if __name__ == '__main__':
    unittest.main()