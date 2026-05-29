{{ config(materialized='table') }}

WITH skills_with_source AS (
    SELECT
        silver.source,
        silver.dept_code,
        silver.region_nom,
        silver.is_remote,
        js.skill,
        js.skill_type,
        COUNT(DISTINCT js.raw_job_id) AS nb_offres
    FROM job_skills js
    JOIN {{ ref('jobs') }} silver ON silver.raw_id = js.raw_job_id
    GROUP BY silver.source, silver.dept_code, silver.region_nom,
             silver.is_remote, js.skill, js.skill_type
),

total_per_source AS (
    SELECT source, COUNT(*) AS total_offres
    FROM {{ ref('jobs') }}
    GROUP BY source
)

SELECT
    s.source,
    s.dept_code,
    s.region_nom,
    s.is_remote,
    s.skill,
    s.skill_type,
    s.nb_offres,
    t.total_offres,
    ROUND(s.nb_offres * 100.0 / t.total_offres, 2) AS pct_offres,
    NOW()                                            AS computed_at
FROM skills_with_source s
JOIN total_per_source t ON s.source = t.source
ORDER BY nb_offres DESC
