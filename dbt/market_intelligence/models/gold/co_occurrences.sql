{{ config(materialized='table') }}

WITH job_skills_with_source AS (
    SELECT
        js.raw_job_id,
        silver.source,
        silver.dept_code,
        silver.region_nom,
        silver.is_remote,
        js.skill
    FROM job_skills js
    JOIN {{ ref('jobs') }} silver ON silver.raw_id = js.raw_job_id
    WHERE js.skill_type = 'hard'
),

co_occurrences AS (
    SELECT
        s1.source,
        s1.dept_code,
        s1.region_nom,
        s1.is_remote,
        s1.skill AS skill_a,
        s2.skill AS skill_b,
        COUNT(DISTINCT s1.raw_job_id) AS nb_offres
    FROM job_skills_with_source s1
    JOIN job_skills_with_source s2
        ON s1.raw_job_id = s2.raw_job_id
        AND s1.skill < s2.skill
    GROUP BY s1.source, s1.dept_code, s1.region_nom,
             s1.is_remote, s1.skill, s2.skill
)

SELECT
    source,
    dept_code,
    region_nom,
    is_remote,
    skill_a,
    skill_b,
    nb_offres,
    NOW() AS computed_at
FROM co_occurrences
WHERE nb_offres >= 2
ORDER BY nb_offres DESC
