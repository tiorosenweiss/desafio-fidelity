import unittest
import os
import time
from unittest.mock import patch, MagicMock
from database import Database
from config import Config 



import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))


# Configurações para o banco de dados de teste (devem vir do docker-compose.yml)
# Idealmente, você usaria um .env.test e carregaria com dotenv para esses testes
# Ou faria o mock de psycopg2.connect completamente
TEST_DB_HOST = os.getenv('TEST_DB_HOST', 'localhost') # ou 'postgres' se rodar no docker-compose
TEST_DB_USER = os.getenv('TEST_DB_USER', 'usr_teste')
TEST_DB_PASSWORD = os.getenv('TEST_DB_PASSWORD', 'teste')
TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'db_teste')

class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        
        print("\nVerificando conexão com o PostgreSQL de teste...")
        
        cls.patcher = patch.dict(os.environ, {
            'DB_HOST': TEST_DB_HOST,
            'DB_USER': TEST_DB_USER,
            'DB_PASSWORD': TEST_DB_PASSWORD,
            'DB_NAME': TEST_DB_NAME
        })
        cls.patcher.start()
        import importlib
        importlib.reload(Config) 

        cls.db = Database() 
        cls.db.connect() 

        # Limpar ou popular o banco de dados de teste com dados controlados        
        try:
            cls.db.execute("DROP TABLE IF EXISTS test_table;")
            cls.db.execute("CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(50));")
            cls.db.execute("INSERT INTO test_table (name) VALUES ('Test Item 1'), ('Test Item 2');")
            print("Banco de dados de teste preparado com sucesso.")
        except Exception as e:
            print(f"Erro ao preparar o banco de dados de teste: {e}")
            raise

    @classmethod
    def tearDownClass(cls):
        # Este método será executado uma vez após todos os testes da classe
        if cls.db.connection:
            cls.db.close()
            print("Conexão com PostgreSQL de teste fechada.")
        cls.patcher.stop() # Parar o patch

    def setUp(self):
        # Garante que a conexão está aberta para cada teste individual
        if self.db.connection and self.db.connection.closed:
            self.db.connect()

    def tearDown(self):
        # Não precisa fechar a conexão após cada teste, já que setUpClass a gerencia
        pass

    @patch('time.sleep', return_value=None) 
    def test_connect_success(self, mock_sleep):
        db_instance = Database()
        self.assertIsNotNone(db_instance.connection)
        self.assertFalse(db_instance.connection.closed)
        db_instance.close()

    @patch('psycopg2.connect', side_effect=psycopg2.OperationalError("Mocked Connection Error"))
    @patch('time.sleep', return_value=None)
    def test_connect_failure_and_retry(self, mock_sleep, mock_connect):
        # Testa o comportamento de retry da conexão
        with self.assertRaises(psycopg2.OperationalError):
            Database()
        self.assertEqual(mock_connect.call_count, 10) 
        self.assertEqual(mock_sleep.call_count, 9)    

    def test_close_connection(self):
        db_instance = Database()
        self.assertIsNotNone(db_instance.connection)
        db_instance.close()
        self.assertTrue(db_instance.connection.closed)

    def test_fetchall(self):
        rows = self.db.fetchall("SELECT * FROM test_table ORDER BY id;")
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][1], 'Test Item 1')
        self.assertEqual(rows[1][1], 'Test Item 2')

    def test_execute_insert(self):
        initial_count = self.db.fetchall("SELECT COUNT(*) FROM test_table;")[0][0]
        self.db.execute("INSERT INTO test_table (name) VALUES ('New Item');")
        new_count = self.db.fetchall("SELECT COUNT(*) FROM test_table;")[0][0]
        self.assertEqual(new_count, initial_count + 1)
        # Verifica se o item foi realmente inserido
        item = self.db.fetchall("SELECT name FROM test_table WHERE name = 'New Item';")
        self.assertIsNotNone(item)
        self.assertEqual(item[0][0], 'New Item')

    def test_execute_update(self):
        self.db.execute("UPDATE test_table SET name = 'Updated Item' WHERE id = 1;")
        updated_item = self.db.fetchall("SELECT name FROM test_table WHERE id = 1;")[0][0]
        self.assertEqual(updated_item, 'Updated Item')

    def test_execute_delete(self):
        self.db.execute("DELETE FROM test_table WHERE id = 1;")
        remaining_items = self.db.fetchall("SELECT * FROM test_table;")
        self.assertEqual(len(remaining_items), 1)
        self.assertEqual(remaining_items[0][1], 'Test Item 2') 

    def test_fetchall_reconnect(self):
        # Força o fechamento da conexão para testar a reconexão automática
        self.db.close()
        rows = self.db.fetchall("SELECT * FROM test_table;")
        self.assertIsNotNone(rows)
        self.assertFalse(self.db.connection.closed) # Verifica que a conexão foi reaberta

    def test_execute_reconnect(self):
        # Força o fechamento da conexão para testar a reconexão automática
        self.db.close()
        self.db.execute("INSERT INTO test_table (name) VALUES ('Another Item');")
        self.assertFalse(self.db.connection.closed)
        item = self.db.fetchall("SELECT name FROM test_table WHERE name = 'Another Item';")
        self.assertIsNotNone(item)


if __name__ == '__main__':
   
    unittest.main()