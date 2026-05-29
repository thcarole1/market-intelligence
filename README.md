# 📊 Market Intelligence Pipeline

> Pipeline de data engineering end-to-end pour analyser les compétences les plus demandées sur le marché de l'emploi Data Engineer en France.

---

## 🎯 Objectif

Ce projet collecte automatiquement des offres d'emploi depuis plusieurs sources, les normalise, extrait les compétences techniques et soft skills via NLP, et les expose dans un dashboard interactif.

**Question centrale :** Quelles sont les compétences les plus demandées pour un poste de Data Engineer en France, à un instant donné ?

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     COUCHE INGESTION                        │
│   France Travail │ HelloWork │ Remotive │ WWR │ Greenhouse  │
└──────────────────────────┬──────────────────────────────────┘
                           │ offres brutes (JSON/HTML)
┌──────────────────────────▼──────────────────────────────────┐
│              BRONZE — Stockage brut                         │
│              PostgreSQL · table raw_jobs (JSONB)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              SILVER — Normalisation (dbt)                   │
│              table jobs · schéma uniforme                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              GOLD — Agrégations (dbt)                       │
│         skills_freq · co_occurrences                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              EXPOSITION                                      │
│              Dashboard Streamlit + Plotly                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              ORCHESTRATION & MONITORING                     │
│              APScheduler · PostgreSQL metrics               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Stack technique

| Couche | Technologies |
|--------|-------------|
| **Ingestion** | Python, requests, BeautifulSoup, feedparser, requests-ratelimiter |
| **Stockage** | PostgreSQL 16, JSONB |
| **Transformation** | dbt-postgres, SQL |
| **NLP** | spaCy 3.8 (fr_core_news_sm, en_core_web_sm) |
| **Dashboard** | Streamlit 1.58, Plotly, SQLAlchemy |
| **Orchestration** | APScheduler |
| **Configuration** | pydantic-settings |
| **Qualité** | pytest, pytest-mock |
| **Infrastructure** | Docker, Docker Compose |
| **Versioning** | Git, GitHub, Git Flow |

---

## 📁 Structure du projet

```
market-intelligence/
├── src/
│   ├── config.py                      ← configuration centralisée (pydantic-settings)
│   ├── monitoring.py                  ← monitoring pipeline et data quality
│   ├── ingestion/
│   │   ├── base_collector.py          ← classe abstraite commune
│   │   ├── france_travail_collector.py ← API officielle OAuth2
│   │   ├── hellowork_collector.py     ← scraping HTML
│   │   ├── remotive_collector.py      ← API REST publique
│   │   ├── wwr_collector.py           ← flux RSS
│   │   ├── greenhouse_collector.py    ← API ATS publique
│   │   ├── skills_dictionary.py       ← dictionnaire curé 40+ skills
│   │   └── skills_extractor.py        ← extraction NLP avec spaCy
│   └── dashboard/
│       ├── app.py                     ← point d'entrée Streamlit
│       ├── db.py                      ← requêtes PostgreSQL centralisées
│       └── views/
│           ├── overview.py            ← KPIs, sources, contrats, localisations
│           ├── skills.py              ← Top skills, comparaison par source
│           └── cooccurrences.py       ← heatmap + graphe réseau
├── dbt/
│   └── market_intelligence/
│       └── models/
│           ├── bronze/                ← vues sur raw_jobs
│           ├── silver/                ← normalisation multi-sources
│           └── gold/                  ← skills_freq, co_occurrences
├── scripts/
│   ├── init_db.py                     ← initialisation BDD (idempotent)
│   └── scheduler.py                   ← orchestration APScheduler
├── tests/
│   └── test_base_collector.py         ← tests unitaires
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

---

## 🚀 Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Python 3.12+
- Git

### 1. Cloner le projet

```bash
git clone https://github.com/thcarole1/market-intelligence.git
cd market-intelligence
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
# Éditer .env avec vos propres valeurs
```

Variables requises :

```bash
# PostgreSQL
POSTGRES_USER=market_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=market_intelligence
POSTGRES_PORT=5432

# pgAdmin
PGADMIN_EMAIL=admin@market.com
PGADMIN_PASSWORD=your_password
PGADMIN_PORT=5050

# France Travail API (https://francetravail.io)
FRANCETRAVAIL_CLIENT_ID=your_client_id
FRANCETRAVAIL_CLIENT_SECRET=your_client_secret
```

### 3. Lancer avec Docker Compose

```bash
docker compose up -d
```

Services disponibles :
- **Dashboard** : http://localhost:8501
- **pgAdmin** : http://localhost:5050
- **PostgreSQL** : localhost:5432

### 4. Initialiser la base de données

```bash
make init-db
```

### 5. Lancer le pipeline complet

```bash
make pipeline
```

---

## 💻 Développement local

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Commandes disponibles

```bash
make help           # Affiche toutes les commandes
make install        # Installe les dépendances
make init-db        # Initialise la base de données

# Collecteurs individuels
make collect-ft         # France Travail
make collect-remotive   # Remotive
make collect-wwr        # We Work Remotely
make collect-greenhouse # Greenhouse
make collect-hellowork  # HelloWork

# Pipeline
make pipeline       # Lance le pipeline complet immédiatement
make scheduler      # Démarre le scheduling nocturne (02:00)

# Transformation
make dbt-run        # Lance dbt (Silver + Gold)
make dbt-test       # Lance les tests dbt

# NLP
make extract-skills # Extrait les skills par NLP

# Dashboard
make dashboard      # Lance le dashboard Streamlit

# Monitoring
make monitoring     # Affiche le rapport de monitoring

# Tests
make test           # Lance les tests unitaires
make lint           # Vérifie la qualité du code
```

---

## 📊 Sources de données

| Source | Méthode | Type d'offres |
|--------|---------|---------------|
| [France Travail](https://francetravail.io) | API officielle OAuth2 | CDI, CDD, alternance France |
| [HelloWork](https://www.hellowork.com) | Scraping HTML | PME, grandes entreprises France |
| [Remotive](https://remotive.com) | API REST publique | Remote, tech international |
| [We Work Remotely](https://weworkremotely.com) | RSS public | Remote, tech international |
| [Greenhouse](https://greenhouse.io) | API ATS publique | Scale-ups, licornes françaises |

> ⚠️ Le scraping respecte les CGU de chaque site. Les sources avec CGU anti-scraping strictes (LinkedIn, Indeed) ont été délibérément exclues.

---

## 🧠 Modèle de données

### Architecture Medallion

```
Bronze  → raw_jobs        (JSONB brut, toutes sources)
Silver  → jobs            (schéma uniforme normalisé)
Gold    → skills_freq     (fréquence des skills par source)
        → co_occurrences  (paires de skills co-occurrents)
Metrics → job_skills      (skills extraits par NLP par offre)
        → pipeline_runs   (historique des exécutions)
        → source_metrics  (métriques par source par run)
```

### Déduplication

Chaque offre brute est hashée (SHA-256) avant insertion. Les doublons sont rejetés automatiquement via `ON CONFLICT (hash) DO NOTHING`.

---

## 🛠️ Extraction NLP des skills

L'extracteur utilise spaCy pour la tokenisation et un dictionnaire curé pour la détection des compétences :

- **40+ hard skills** : Python, SQL, Spark, Kafka, AWS, GCP, Azure, dbt, Docker, etc.
- **8 soft skills** : autonomie, communication, agilité, leadership, etc.
- **Détection multilingue** : FR et EN
- **Word boundaries** : évite les faux positifs (ex: `r` dans `docker`)

### Co-occurrences

Les paires de skills apparaissant ensemble dans la même offre sont calculées via self-join SQL, permettant de répondre à : *"Si une offre demande Python, quels autres skills demande-t-elle ?"*

---

## 📈 Dashboard

Le dashboard Streamlit expose 3 vues :

1. **Vue générale** — KPIs, répartition par source, types de contrats, top localisations
2. **Top Skills** — Classement des compétences, comparaison par source
3. **Co-occurrences** — Heatmap et graphe réseau des associations de skills

Filtres disponibles : source, nombre de skills affichés.

---

## ⏰ Orchestration

Le pipeline complet tourne automatiquement chaque nuit à 02:00 via APScheduler :

```
1. Collecteurs (5 sources en séquence)
2. dbt run (Silver + Gold mis à jour)
3. Extraction NLP (nouveaux skills)
```

En cas d'échec d'une étape, le pipeline s'arrête (fail-fast) et les métriques sont enregistrées en base.

---

## 🔍 Monitoring

```bash
make monitoring
```

Affiche un rapport de santé instantané :

```
📊 RAPPORT DE MONITORING — Market Intelligence
============================================================
Status global : ✅ OK
📈 Métriques :
  Offres par source :
    hellowork            :  1,576 offres
    france_travail       :    496 offres
    wwr                  :     57 offres
    remotive             :     20 offres
    greenhouse           :      6 offres
  Offres Silver     :  2,155
  Offres avec skills:    908
  Total skills      :  3,444
✅ Aucune anomalie détectée
```

---

## 🧪 Tests

```bash
make test
```

Tests unitaires sur `BaseCollector` :
- Déterminisme du hash SHA-256
- Insensibilité à l'ordre des clés JSON
- Détection des doublons
- Insertion en base

---

## 🔧 Configuration avancée

### Ajouter une nouvelle source

1. Créer `src/ingestion/ma_source_collector.py` héritant de `BaseCollector`
2. Implémenter la méthode `collect() -> int`
3. Ajouter un CTE dans `dbt/market_intelligence/models/silver/jobs.sql`
4. Ajouter la commande dans le `Makefile`
5. Ajouter le module dans `scripts/scheduler.py`

### Enrichir le dictionnaire de skills

Éditer `src/ingestion/skills_dictionary.py` — ajouter le skill normalisé et ses variantes dans `HARD_SKILLS` ou `SOFT_SKILLS`.

---

## 📝 Bonnes pratiques appliquées

- **Configuration** : pydantic-settings, `.env` jamais commité
- **Logging** : logging structuré centralisé avec handlers fichier + console
- **Déduplication** : hash SHA-256 + contrainte UNIQUE en base
- **Typage** : type hints sur toutes les fonctions
- **Tests** : pytest + mocking des connexions BDD
- **Git Flow** : branches `main` / `develop` / `feature/*`
- **Commits** : Conventional Commits (`feat:`, `fix:`, `chore:`)
- **Docker** : multi-services, healthcheck, volumes persistants
- **CGU** : sources légalement sûres uniquement

---

## 👤 Auteur

**Thierry** — Data Engineer en reconversion
Projet réalisé dans le cadre d'un portfolio professionnel.

- GitHub : [github.com/thcarole1](https://github.com/thcarole1)

---
