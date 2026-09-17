FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV HOST=0.0.0.0 PORT=5000 DB_PATH=/app/data/leads.db
EXPOSE 5000
VOLUME ["/app/data"]
CMD ["python", "serve.py"]
