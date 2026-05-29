{{ config(materialized='table') }}

WITH job_skills_with_source AS (
    SELECT
        js.raw_job_id,
        j.source,
        js.skill
    FROM job_skills js
    JOIN raw_jobs j ON js.raw_job_id = j.id
    WHERE js.skill_type = 'hard'
),

co_occurrences AS (
    SELECT
        s1.source,
        s1.skill AS skill_a,
        s2.skill AS skill_b,
        COUNT(DISTINCT s1.raw_job_id) AS nb_offres
    FROM job_skills_with_source s1
    JOIN job_skills_with_source s2
        ON s1.raw_job_id = s2.raw_job_id
        AND s1.skill < s2.skill
    GROUP BY s1.source, s1.skill, s2.skill
)

SELECT
    source,
    skill_a,
    skill_b,
    nb_offres,
    NOW() AS computed_at
FROM co_occurrences
WHERE nb_offres >= 2
ORDER BY nb_offres DESC
