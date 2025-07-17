import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm
import sys
import os

from app.config import Config
from app.database import db 

class SPVAutomatico:
    def __init__(self, initial_filter=0):
        self.current_filter = initial_filter
        self.driver = None 

    def _init_selenium_driver(self):
        """Inicializa o driver do Selenium para Selenoid."""
        options = webdriver.ChromeOptions() 
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless") 

        try:
            self.driver = webdriver.Remote(
                command_executor=Config.SELENOID_HUB_URL,
                options=options
            )
            print("Driver Selenium conectado ao Selenoid.")
            
        except Exception as e:
            print(f"Erro ao conectar ao Selenoid: {e}")            
            raise ConnectionError(f"Não foi possível conectar ao Selenoid: {e}")

    def _close_selenium_driver(self):
        """Fecha o driver do Selenium."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _get_pesquisas(self, offset, limit):
        """
        Consulta as pesquisas em aberto no banco de dados com paginação.
        Retorna uma lista de tuplas com os dados das pesquisas.
        """
        cond_rg = ''
        if (self.current_filter == 1 or self.current_filter == 3):
            
            cond_rg = ' AND p.rg IS NOT NULL AND p.rg <> \'\' '

        
        sql = f"""
            SELECT
                p.Cod_Cliente, p.Cod_Pesquisa, e.UF, p.Data_Entrada,
                COALESCE(p.nome_corrigido, p.nome) AS Nome, p.CPF,
                COALESCE(p.rg_corrigido, p.rg) AS RG, p.Nascimento,
                COALESCE(p.mae_corrigido, p.mae) AS Mae, p.anexo AS Anexo,
                ps.Resultado, ps.cod_spv_tipo
            FROM pesquisa p
            INNER JOIN servico s ON p.Cod_Servico = s.Cod_Servico
            LEFT JOIN lote_pesquisa lp ON p.Cod_Pesquisa = lp.Cod_Pesquisa
            LEFT JOIN lote l ON l.cod_lote = lp.cod_lote
            LEFT JOIN estado e ON e.Cod_UF = p.Cod_UF
            LEFT JOIN pesquisa_spv ps ON ps.Cod_Pesquisa = p.Cod_Pesquisa AND ps.Cod_SPV = 1 AND ps.filtro = %s
            WHERE p.Data_Conclusao IS NULL
              AND ps.resultado IS NULL
              AND p.tipo = 0
              AND p.cpf IS NOT NULL AND p.cpf <> ''
              {cond_rg} -- A condição dinâmica é injetada aqui
              AND (e.UF = 'SP' OR p.Cod_UF_Nascimento = 26 OR p.Cod_UF_RG = 26)
            GROUP BY 
                p.Cod_Cliente, p.Cod_Pesquisa, e.UF, p.Data_Entrada,
                p.nome_corrigido, p.nome, p.CPF, p.rg_corrigido, p.rg,
                p.Nascimento, p.mae_corrigido, p.mae, p.anexo,
                ps.Resultado, ps.cod_spv_tipo
            ORDER BY Nome ASC, Resultado DESC
            LIMIT %s OFFSET %s
        """
        
        params = (self.current_filter, limit, offset)
        return db.fetchall(sql, params)


    def _check_result(self, site_content):
        """
        Enquadra a pesquisa de acordo com o resultado obtido na pesquisa
        (Nada Consta, Consta Criminal e Consta Cível).
        """
        final_result = 7 
        if Config.NADA_CONSTA in site_content:
            final_result = 1
        elif (Config.CONSTA01 in site_content or Config.CONSTA02 in site_content) and \
             ('Criminal' in site_content or 'criminal' in site_content):
            final_result = 2
        elif (Config.CONSTA01 in site_content or Config.CONSTA02 in site_content):
            final_result = 5
        return final_result

    def _load_site(self, search_type, document):
        """
        Busca a pesquisa na plataforma online utilizando o Selenoid.
        Retorna o page_source se sucesso, None em caso de falha.
        """
        try:
            self._init_selenium_driver() 
            self.driver.get("https://esaj.tjsp.jus.br/cpopg/open.do")

            wait = WebDriverWait(self.driver, 30) 

            if search_type in [0, 1, 3]: 
                select_el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="cbPesquisa"]')))
                select_ob = Select(select_el)
                select_ob.select_by_value('DOCPARTE')

                input_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="campo_DOCPARTE"]')))
                input_field.send_keys(document)

            elif search_type == 2: 
                select_el = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="cbPesquisa"]')))
                select_ob = Select(select_el)
                select_ob.select_by_value('NMPARTE')
                
                try:
                    full_name_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pesquisarPorNomeCompleto"]')))
                    full_name_checkbox.click()
                except:
                    print("Checkbox 'pesquisarPorNomeCompleto' não encontrado ou não clicável (pode ser opcional).")


                input_field = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="campo_NMPARTE"]')))
                input_field.send_keys(document)

            
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="botaoConsultarProcessos"]'))).click()

            wait.until(EC.url_contains("cpopg/search.do")) 
            time.sleep(2) 

            return self.driver.page_source

        except ConnectionError as ce:
            print(f"Erro de conexão com Selenoid: {ce}")
            return None
        except Exception as e:
            print(f"Erro ao carregar o site ou interagir com elementos: {e}")
            
            return None
        finally:
            self._close_selenium_driver() 

    def _insert_spv_result(self, cod_pesquisa, result, search_filter):
        """Insere o resultado da pesquisa no banco de dados."""
        sql = """
            INSERT INTO pesquisa_spv
                (Cod_Pesquisa, Cod_SPV, Cod_spv_computador, Cod_Spv_Tipo, Resultado, Cod_Funcionario, filtro, website_id)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (cod_pesquisa, 1, 36, None, result, -1, search_filter, 1)
        try:
            db.execute(sql, params)
            print(f"Resultado para Cod_Pesquisa {cod_pesquisa} inserido com sucesso.")
        except Exception as e:
            print(f"Erro ao inserir resultado para Cod_Pesquisa {cod_pesquisa}: {e}")
            

    def process_pesquisas(self):
        """
        Consulta as pesquisas no banco de dados e executa utilizando Selenium/Selenoid.
        Implementa paginação para processar grandes volumes de dados.
        """
        page_size = 20 # Quantidade de registros por página
        offset = 0
        total_processed = 0

        while True:
            print(f"Consultando pesquisas com filtro {self.current_filter}, offset {offset}...")
            
            qry = self._get_pesquisas(offset, page_size)

            if not qry:
                print(f"Nenhuma pesquisa encontrada para o filtro {self.current_filter} na página atual.")
                break 

            print(f"Processando {len(qry)} pesquisas...")
            for dados in tqdm(qry): 
                codPesquisa = dados[1]
                nome = dados[4]
                cpf = dados[5]
                rg = dados[6]

                site_content = None
                result_code = 7 

                try:
                    if self.current_filter == 0 and cpf:
                        site_content = self._load_site(self.current_filter, cpf)
                    elif (self.current_filter == 3 or self.current_filter == 1) and rg:
                        site_content = self._load_site(self.current_filter, rg)
                    elif self.current_filter == 2 and nome:
                        site_content = self._load_site(self.current_filter, nome)
                    else:
                        print(f"Dados insuficientes ou filtro incompatível para Cod_Pesquisa {codPesquisa} com filtro {self.current_filter}.")
                        
                        self._insert_spv_result(codPesquisa, result_code, self.current_filter)
                        continue 

                    if site_content:
                        result_code = self._check_result(site_content)
                        self._insert_spv_result(codPesquisa, result_code, self.current_filter)
                    else:
                        print(f"Falha ao obter conteúdo do site para Cod_Pesquisa {codPesquisa}. Inserindo resultado de erro.")
                        self._insert_spv_result(codPesquisa, result_code, self.current_filter) # Insere erro mesmo sem conteúdo

                except Exception as e:
                    print(f"Erro inesperado ao processar Cod_Pesquisa {codPesquisa}: {e}. Inserindo resultado de erro.")
                    self._insert_spv_result(codPesquisa, result_code, self.current_filter)

                total_processed += 1

            offset += page_size 

        print(f"Total de pesquisas processadas para o filtro {self.current_filter}: {total_processed}")


    def run(self):
        """Orquestra o ciclo de vida da aplicação, iterando pelos filtros."""
        max_filters = 3 
        while True: # Loop infinito para manter o serviço em execução
            for f in range(max_filters + 1):
                self.current_filter = f
                print(f"\nIniciando processamento para o filtro: {self.current_filter}")
                self.process_pesquisas()

            print("\nTodos os filtros foram processados. Aguardando para reiniciar o ciclo.")
            time.sleep(300) 