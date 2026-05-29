.PHONY: help install init-db collect-ft test lint

help:
	@echo "Commandes disponibles :"
	@echo "  make install      → installe les dépendances"
	@echo "  make init-db      → initialise la base de données"
	@echo "  make collect-ft   → lance le collecteur France Travail"
	@echo "  make test         → lance les tests unitaires"
	@echo "  make lint         → vérifie la qualité du code"

install:
	pip install -r requirements.txt

init-db:
	python -m scripts.init_db

collect-ft:
	python -m src.ingestion.france_travail_collector

collect-remotive:
	python -m src.ingestion.remotive_collector

collect-wwr:
	python -m src.ingestion.wwr_collector

collect-greenhouse:
	python -m src.ingestion.greenhouse_collector

collect-hellowork:
	python -m src.ingestion.hellowork_collector

dbt-run:
	cd dbt/market_intelligence && dbt run

dbt-test:
	cd dbt/market_intelligence && dbt test

test:
	python -m pytest tests/ -v

lint:
	python -m flake8 src/ scripts/ tests/
