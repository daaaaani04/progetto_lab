FROM python:3.11-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia frontend e gs_data (usato per leggere gli URL gold standard)
COPY frontend/ ./frontend/
COPY gs_data/ ./gs_data/

EXPOSE 8004

CMD ["uvicorn", "frontend.src.frontend:app", "--host", "0.0.0.0", "--port", "8004"]
