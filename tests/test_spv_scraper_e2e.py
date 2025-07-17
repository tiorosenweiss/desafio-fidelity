import unittest
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

from config import Config
from database import Database

SELENOID_HUB_URL = os.getenv('SELENOID_HUB_URL', 'http://selenoid:4444/wd/hub')
DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_USER = os.getenv('DB_USER', 'usr_teste')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'teste')
DB_NAME = os.getenv('DB_NAME', 'db_teste')


class TestSPVAutomaticoE2E(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Garante que o DB de teste está limpo e populado
        cls.db = Database() 

        # Limpar e popular o DB para o teste E2E
        cls.db.execute("DELETE FROM pesquisa_spv;")
        cls.db.execute("DELETE FROM pesquisa;")
        cls.db.execute("DELETE FROM estado;")
        cls.db.execute("DELETE FROM servico;")
        cls.db.execute("INSERT INTO estado (UF, Nome_Estado) VALUES ('SP', 'São Paulo') ON CONFLICT (UF) DO NOTHING;")
        cls.db.execute("INSERT INTO servico (Descricao_Servico) VALUES ('Consulta SPV') ON CONFLICT DO NOTHING;")

        # Inserir dados de teste para o SPVAutomatico consumir
        cls.db.execute(
            """
            INSERT INTO pesquisa (Cod_Cliente, Cod_Servico, Cod_UF, Nome, CPF, Tipo) VALUES
            (100, (SELECT Cod_Servico FROM servico WHERE Descricao_Servico = 'Consulta SPV'), (SELECT Cod_UF FROM estado WHERE UF = 'SP'), 'Teste Sem Processo', '999.999.999-99', 0)
            ON CONFLICT (CPF) DO NOTHING;
            """
        )
        print("\nBanco de dados de teste E2E preparado.")

    @classmethod
    def tearDownClass(cls):
        # Limpar o DB após os testes (opcional, mas boa prática)
        cls.db.execute("DELETE FROM pesquisa_spv;")
        cls.db.execute("DELETE FROM pesquisa;")
        cls.db.close()
        print("Banco de dados de teste E2E limpo e conexão fechada.")

    def setUp(self):
        
        pass

    def test_spv_automatico_runs_and_updates_db(self):
        print("Iniciando teste E2E: verificando se SPVAutomatico processa dados e atualiza o DB.")
        
        print("Aguardando 30 segundos para a aplicação SPVAutomatico processar...")
        time.sleep(30) 

        # Verificar se a pesquisa foi marcada como concluída e o resultado foi inserido
        pesquisa_concluida = self.db.fetchall(
            "SELECT Data_Conclusao FROM pesquisa WHERE CPF = '999.999.999-99';"
        )
        self.assertIsNotNone(pesquisa_concluida)
        self.assertIsNotNone(pesquisa_concluida[0][0]) # Data_Conclusao deve estar preenchida

        pesquisa_spv_result = self.db.fetchall(
            "SELECT Resultado FROM pesquisa_spv WHERE Cod_Pesquisa = (SELECT Cod_Pesquisa FROM pesquisa WHERE CPF = '999.999.999-99');"
        )
        self.assertIsNotNone(pesquisa_spv_result)
        self.assertEqual(pesquisa_spv_result[0][0], 0) # Assumindo 0 para "Nada Consta" do site de teste

        print("Teste E2E de SPVAutomatico concluído com sucesso.")


if __name__ == '__main__':
    unittest.main()