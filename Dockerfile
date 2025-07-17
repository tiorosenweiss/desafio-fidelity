# Use uma imagem base Python oficial com a versão que você usa na VM
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY app/ app/

# Define variáveis de ambiente (serão sobrescritas pelo docker-compose.yml)
ENV PYTHONUNBUFFERED=1

# Comando para executar a aplicação quando o contêiner iniciar
CMD python -m app.main