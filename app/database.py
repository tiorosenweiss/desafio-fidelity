import psycopg2
from app.config import Config
import time 

class Database:
    def __init__(self):
        self.connection = None        
        self.connect()

    def connect(self):
        max_retries = 10 
        retry_delay = 5  

        for i in range(max_retries):
            try:
                self.connection = psycopg2.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    dbname=Config.DB_NAME
                )
                print("Conectado ao PostgreSQL com sucesso!")
                return 
            except psycopg2.OperationalError as e:
                
                print(f"Tentativa {i+1}/{max_retries}: Erro ao conectar ao PostgreSQL: {e}")
                if i < max_retries - 1:
                    print(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                    time.sleep(retry_delay)
                else:
                    
                    print("Número máximo de retentativas de conexão atingido. A aplicação será encerrada.")
                    raise 

            except Exception as e:
                
                print(f"Erro inesperado durante a conexão ao PostgreSQL: {e}")
                raise

    def close(self):
        """Fecha a conexão com o banco de dados se estiver aberta."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None 
    def fetchall(self, sql, params=None):
        """
        Executa uma query SELECT e retorna todos os resultados.
        Tenta reconectar se a conexão estiver fechada.
        """
        cursor = None
        try:
            
            if not self.connection or self.connection.closed:
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            raise 
        finally:
            if cursor:
                cursor.close()

    def execute(self, sql, params=None):
        """
        Executa uma query de INSERT, UPDATE ou DELETE e faz commit.
        Tenta reconectar se a conexão estiver fechada.
        """
        cursor = None
        try:
            # Verifica se a conexão está ativa; se não, tenta reconectar
            if not self.connection or self.connection.closed:
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            self.connection.commit() 
            return cursor.rowcount 
        except psycopg2.Error as e:
            print(f"Error executing update/insert: {e}")
            self.connection.rollback() 
            raise 
        finally:
            if cursor:
                cursor.close()

db = Database()