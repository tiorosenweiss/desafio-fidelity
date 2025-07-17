import psycopg2
from app.config import Config
import time # Importação adicionada para usar time.sleep

class Database:
    def __init__(self):
        self.connection = None
        # A chamada para connect() no __init__ tentará a conexão inicial.
        # A lógica de retentativa está dentro do connect()
        self.connect()

    def connect(self):
        max_retries = 10 # Número de tentativas de conexão
        retry_delay = 5  # Atraso em segundos entre as tentativas

        for i in range(max_retries):
            try:
                self.connection = psycopg2.connect(
                    host=Config.DB_HOST,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    dbname=Config.DB_NAME
                )
                print("Conectado ao PostgreSQL com sucesso!")
                return # Sai da função se a conexão for bem-sucedida
            except psycopg2.OperationalError as e:
                # Captura erros de operação (como "Connection refused")
                print(f"Tentativa {i+1}/{max_retries}: Erro ao conectar ao PostgreSQL: {e}")
                if i < max_retries - 1:
                    print(f"Aguardando {retry_delay} segundos antes de tentar novamente...")
                    time.sleep(retry_delay)
                else:
                    # Se atingir o número máximo de retentativas, levanta a exceção final
                    print("Número máximo de retentativas de conexão atingido. A aplicação será encerrada.")
                    raise # Propaga a exceção para que a aplicação saia

            except Exception as e:
                # Captura quaisquer outras exceções inesperadas durante a conexão
                print(f"Erro inesperado durante a conexão ao PostgreSQL: {e}")
                raise

    def close(self):
        """Fecha a conexão com o banco de dados se estiver aberta."""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None # Define como None após fechar

    def fetchall(self, sql, params=None):
        """
        Executa uma query SELECT e retorna todos os resultados.
        Tenta reconectar se a conexão estiver fechada.
        """
        cursor = None
        try:
            # Verifica se a conexão está ativa; se não, tenta reconectar
            if not self.connection or self.connection.closed:
                self.connect()
            cursor = self.connection.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        except psycopg2.Error as e:
            print(f"Error executing query: {e}")
            raise # Re-levanta a exceção para ser tratada em níveis superiores
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
            self.connection.commit() # Commit explícito para garantir a persistência
            return cursor.rowcount # Retorna o número de linhas afetadas
        except psycopg2.Error as e:
            print(f"Error executing update/insert: {e}")
            self.connection.rollback() # Rollback em caso de erro na transação
            raise # Re-levanta a exceção
        finally:
            if cursor:
                cursor.close()

# Instância única da classe Database para ser usada em toda a aplicação
# Esta linha é executada quando o módulo database.py é importado.
# A chamada db = Database() irá iniciar o processo de conexão, incluindo as retentativas.
db = Database()