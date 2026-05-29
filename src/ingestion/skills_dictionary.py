"""
Dictionnaire curé de skills Data Engineer.
Chaque entrée : (skill_normalisé, [variantes], type)
"""

HARD_SKILLS = {
    # Langages
    "python":           ["python", "py", "python3"],
    "sql":              ["sql", "mysql", "t-sql", "pl/sql"],
    "scala":            ["scala"],
    "java":             ["java"],
    "bash":             ["bash", "shell", "linux"],
    "javascript":       ["javascript", "js", "typescript"],
    "langage r":        ["langage r", " r ", "rlang"],

    # Big Data
    "spark":            ["spark", "apache spark", "pyspark", "spark streaming"],
    "kafka":            ["kafka", "apache kafka"],
    "hadoop":           ["hadoop", "hdfs", "mapreduce", "hive"],
    "flink":            ["flink", "apache flink"],
    "airflow":          ["airflow", "apache airflow"],

    # Cloud
    "aws":              ["aws", "amazon web services", "ec2", "lambda", "emr"],
    "gcp":              ["gcp", "google cloud", "bigquery", "dataflow", "dataproc"],
    "azure":            ["azure", "microsoft azure", "synapse", "data factory", "adf"],
    "snowflake":        ["snowflake"],
    "databricks":       ["databricks"],

    # Bases de données
    "postgresql":       ["postgresql", "postgres"],
    "mongodb":          ["mongodb", "mongo"],
    "elasticsearch":    ["elasticsearch", "elastic", "opensearch"],
    "redis":            ["redis"],
    "cassandra":        ["cassandra"],
    "neo4j":            ["neo4j", "graph database"],

    # Orchestration & DataOps
    "dbt":              ["dbt", "data build tool"],
    "prefect":          ["prefect"],
    "dagster":          ["dagster"],
    "mlflow":           ["mlflow"],
    "fivetran":         ["fivetran"],

    # DevOps & Infra
    "docker":           ["docker", "dockerfile", "docker-compose"],
    "kubernetes":       ["kubernetes", "k8s", "helm"],
    "git":              ["git", "github", "gitlab", "bitbucket"],
    "terraform":        ["terraform"],
    "ci/cd":            ["ci/cd", "cicd", "jenkins", "github actions", "gitlab ci"],

    # BI & Dataviz
    "power bi":         ["power bi", "powerbi"],
    "tableau":          ["tableau"],
    "looker":           ["looker"],
    "matplotlib":       ["matplotlib", "seaborn", "plotly"],

    # ML
    "machine learning": ["machine learning", "ml", "deep learning", "ia", "llm"],
    "pandas":           ["pandas"],
    "scikit-learn":     ["scikit-learn", "sklearn"],
    "tensorflow":       ["tensorflow", "keras"],
    "pytorch":          ["pytorch"],
}

SOFT_SKILLS = {
    "autonomie":            ["autonomie", "autonome"],
    "communication":        ["communication", "communicant"],
    "travail en équipe":    ["travail en équipe", "esprit d'équipe", "teamwork"],
    "agilité":              ["agilité", "agile", "scrum", "kanban"],
    "leadership":           ["leadership", "management", "encadrement"],
    "curiosité":            ["curiosité", "curieux", "veille technologique"],
    "rigueur":              ["rigueur", "rigoureux", "méthodique"],
    "adaptabilité":         ["adaptabilité", "adaptable", "flexibilité"],
}

# Index inversé : variante → skill normalisé
HARD_SKILLS_INDEX = {
    variant.lower(): skill
    for skill, variants in HARD_SKILLS.items()
    for variant in variants
}

SOFT_SKILLS_INDEX = {
    variant.lower(): skill
    for skill, variants in SOFT_SKILLS.items()
    for variant in variants
}
