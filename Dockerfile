# Base inicial para CLI. Serviço REST e CI/CD serão adicionados nas fases 9 e 13.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY main.py .
CMD ["python", "main.py"]
