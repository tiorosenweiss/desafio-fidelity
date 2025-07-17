
FROM python:3.9-slim-buster


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app/ app/
COPY tests/ tests/


ENV PYTHONUNBUFFERED=1

# Para execução - mantenha descomentado abaixo e comente a última linha
CMD python -m app.main

#Para executar os testes - descomente abaixo e comente a linha de cima
# CMD ["PYTHON", "-m", "unitest", "tests/test_spv_scraper_e2e.py"]