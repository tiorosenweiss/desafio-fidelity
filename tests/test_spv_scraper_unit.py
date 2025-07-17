import unittest
import os
from unittest.mock import patch, MagicMock
from spv_scraper import SPVAutomatico
from database import Database


import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))




class TestSPVAutomaticoUnit(unittest.TestCase):

    @patch('spv_scraper.webdriver.Remote') 
    @patch('spv_scraper.Database')       
    @patch('spv_scraper.Config')         
    def setUp(self, MockConfig, MockDatabase, MockRemote):
    
        self.mock_driver = MagicMock()
        MockRemote.return_value = self.mock_driver
       
    
        self.mock_db_instance = MagicMock()
        MockDatabase.return_value = self.mock_db_instance
       
    
        MockConfig.SELENOID_HUB_URL = 'http://mock_selenoid:4444/wd/hub'
        MockConfig.NADA_CONSTA = 'Não existem informações disponíveis para os parâmetros informados.'
        MockConfig.CONSTA01 = 'Processos encontrados'

        # Instanciar a classe com mocks
        self.spv_app = SPVAutomatico(initial_filter=0)

    def test_initialization(self):
        # Verifica se o WebDriver e o Database foram instanciados corretamente
        self.spv_app.driver.get.assert_not_called() 

    def test_run_method_no_data(self):
        # Simula que não há dados para processar no banco
        self.mock_db_instance.fetchall.return_value = []
       
        with patch('builtins.print') as mock_print:
            self.spv_app.run()
            mock_print.assert_any_call("Nenhuma pesquisa pendente encontrada com o filtro 0.")
       
        self.spv_app.driver.quit.assert_called_once()
        self.mock_db_instance.close.assert_called_once()

    @patch('spv_scraper.time.sleep', return_value=None)
    def test_process_pesquisa_data_found_nada_consta(self, mock_sleep):
        # Simula que há uma pesquisa pendente e o resultado é "Nada Consta"
        mock_pesquisas = [
            (1, 101, 1, 1, 'João da Silva', '111.111.111-11', None, '1980-01-15', 'Maria Silva', None)
        ]
        self.mock_db_instance.fetchall.side_effect = [
            mock_pesquisas, 
            [],             
        ]

        # Simula a interação com o WebDriver
        # Mocka a busca de elementos e o texto retornado pelo site
        mock_element_nada_consta = MagicMock()
        mock_element_nada_consta.text = self.spv_app.config.NADA_CONSTA
       
        # Simula o clique no botão e a existência do elemento de resultado
        self.mock_driver.find_element.return_value = MagicMock() 
        self.mock_driver.find_element.side_effect = [
            MagicMock(), 
            mock_element_nada_consta 
        ]
       
        with patch('builtins.print') as mock_print:
            self.spv_app.run()
            mock_print.assert_any_call(f"Resultado da Pesquisa SPV para {mock_pesquisas[0][4]}: Não Existem Informações")

        # Verifica se o método de atualização no DB foi chamado corretamente
        self.mock_db_instance.execute.assert_called_with(
            "UPDATE pesquisa SET Data_Conclusao = CURRENT_TIMESTAMP WHERE Cod_Pesquisa = %s",
            (mock_pesquisas[0][0],)
        )
        self.mock_db_instance.execute.assert_called_with(
            "INSERT INTO pesquisa_spv (Cod_Pesquisa, Cod_SPV, Cod_spv_computador, Cod_Spv_Tipo, Resultado, Cod_Funcionario, Filtro, Website_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (mock_pesquisas[0][0], mock_pesquisas[0][1], 36, 1, 0, -1, 0, 1) # Resultado 0 para "Não Consta"
        )
        self.spv_app.driver.quit.assert_called_once()
        self.mock_db_instance.close.assert_called_once()

   


if __name__ == '__main__':
    unittest.main()
