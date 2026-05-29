-- Modèle Gold : co-occurrences de skills
-- Identifie les paires de skills apparaissant ensemble dans une même offre

{{ config(materialized='table') }}

WITH skill_dictionary AS (
    SELECT unnest(ARRAY[
        'python', 'sql', 'scala', 'java', 'spark', 'pyspark',
        'kafka', 'airflow', 'dbt', 'aws', 'gcp', 'azure',
        'snowflake', 'docker', 'kubernetes', 'git',
        'postgresql', 'mongodb', 'elasticsearch',
        'databricks', 'bigquery', 'redshift',
        'machine learning', 'pandas', 'power bi', 'tableau'
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

job_skills AS (
    SELECT
        j.id,
        j.source,
        sd.skill
    FROM jobs_with_text j
    CROSS JOIN skill_dictionary sd
    WHERE j.full_text ~* ('(^|[^a-z])' || sd.skill || '([^a-z]|$)')
),

co_occurrences AS (
    SELECT
        s1.source,
        s1.skill AS skill_a,
        s2.skill AS skill_b,
        COUNT(DISTINCT s1.id) AS nb_offres
    FROM job_skills s1
    JOIN job_skills s2
        ON s1.id = s2.id
        AND s1.skill < s2.skill  -- évite les doublons (A,B) et (B,A)
    GROUP BY s1.source, s1.skill, s2.skill
)

SELECT
    source,
    skill_a,
    skill_b,
    nb_offres,
    NOW() AS computed_at
FROM co_occurrences
WHERE nb_offres >= 2  -- filtre le bruit
ORDER BY nb_offres DESC
