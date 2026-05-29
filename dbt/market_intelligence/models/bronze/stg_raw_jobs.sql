-- Modèle Bronze : vue sur la table raw_jobs
-- Expose les données brutes sans transformation
-- Matérialisé en VIEW (pas de copie des données)

{{ config(materialized='view') }}

SELECT
    id,
    source,
    raw_data,
    collected_at,
    hash
FROM {{ source('public', 'raw_jobs') }}
