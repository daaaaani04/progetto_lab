FROM python:3.11-slim

# Dipendenze di sistema per Playwright (usato da crawl4ai)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installa browser Playwright necessari per crawl4ai
RUN playwright install chromium
RUN playwright install-deps chromium

# Copia tutto il progetto (backend, parser, gs_data, domain.json)
COPY backend/ ./backend/
COPY parser/ ./parser/
COPY gs_data/ ./gs_data/
COPY domain.json ./domain.json

EXPOSE 8003

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8003"]
