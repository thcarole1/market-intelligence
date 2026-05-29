FROM python:3.12-slim

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Installe les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Télécharge les modèles spaCy
RUN python -m spacy download fr_core_news_sm && \
    python -m spacy download en_core_web_sm

# Installe dbt
RUN pip install --no-cache-dir dbt-postgres

# Copie le code source
COPY . .

# Variables d'environnement par défaut
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
