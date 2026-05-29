-- Modèle Gold : fréquence des skills
-- Détecte les skills par correspondance avec un dictionnaire curé
-- dans les titres et descriptions des offres

{{ config(materialized='table') }}

WITH skill_dictionary AS (
    SELECT unnest(ARRAY[
        -- Languages
        'python', 'sql', 'scala', 'java', 'langage r', 'bash', 'javascript',
        -- Big Data
        'spark', 'pyspark', 'hadoop', 'hive', 'kafka', 'flink',
        -- Cloud
        'aws', 'gcp', 'azure', 'snowflake', 's3', 'redshift', 'bigquery',
        -- Orchestration
        'airflow', 'dbt', 'prefect', 'dagster', 'luigi',
        -- Databases
        'postgresql', 'postgres', 'mongodb', 'elasticsearch', 'redis',
        'mysql', 'cassandra', 'neo4j',
        -- Data Warehouse
        'databricks', 'synapse', 'fivetran', 'stitch',
        -- Containers & DevOps
        'docker', 'kubernetes', 'git', 'gitlab', 'github', 'terraform',
        'jenkins', 'ci/cd',
        -- ML & Analytics
        'machine learning', 'deep learning', 'mlflow', 'pandas',
        'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
        'matplotlib', 'tableau', 'power bi', 'looker',
        -- Soft skills
        'autonomie', 'communication', 'travail en équipe', 'agilité',
        'scrum', 'kanban', 'leadership'
    ]) AS skill
),

jobs_with_text AS (
    SELECT
        id,
        source,
        LOWER(
            COALESCE(titre, '') || ' ' ||
            COALESCE(description, '')
        ) AS full_text
    FROM {{ ref('jobs') }}
),

skill_matches AS (
    SELECT
        j.source,
        sd.skill,
        COUNT(DISTINCT j.id) AS nb_offres
    FROM jobs_with_text j
    CROSS JOIN skill_dictionary sd
    WHERE j.full_text ~* ('(^|[^a-z])' || sd.skill || '([^a-z]|$)')
    GROUP BY j.source, sd.skill
),

total_per_source AS (
    SELECT source, COUNT(*) AS total_offres
    FROM {{ ref('jobs') }}
    GROUP BY source
)

SELECT
    sm.source,
    sm.skill,
    sm.nb_offres,
    t.total_offres,
    ROUND(sm.nb_offres * 100.0 / t.total_offres, 2) AS pct_offres,
    NOW() AS computed_at
FROM skill_matches sm
JOIN total_per_source t ON sm.source = t.source
ORDER BY nb_offres DESC
