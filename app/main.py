from app.spv_scraper import SPVAutomatico
import time

if __name__ == "__main__":
    print("Iniciando a aplicação SPVAutomatico...")
    # A instância inicial pode ser com um filtro padrão, a lógica de iteração    
    spv_app = SPVAutomatico(initial_filter=0)
    try:
        spv_app.run()
    except Exception as e:
        print(f"Erro fatal na aplicação: {e}")
        print("A aplicação será encerrada. Verifique os logs.")
        time.sleep(10) 
        