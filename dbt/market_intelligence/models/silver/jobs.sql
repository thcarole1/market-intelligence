-- Modèle Silver : normalisation des offres brutes
-- Unifie les 5 sources en un schéma commun
-- Matérialisé en TABLE (données copiées et indexées)

{{ config(materialized='table') }}

WITH france_travail AS (
    SELECT
        id                                              AS raw_id,
        'france_travail'                                AS source,
        raw_data->>'id'                                 AS source_id,
        raw_data->>'intitule'                           AS titre,
        raw_data->'entreprise'->>'nom'                  AS entreprise,
        raw_data->'lieuTravail'->>'libelle'             AS localisation,
        raw_data->>'typeContrat'                        AS type_contrat,
        raw_data->>'description'                        AS description,
        (raw_data->>'dateCreation')::date               AS date_publication,
        raw_data->>'origineOffre'                       AS url
    FROM {{ source('public', 'raw_jobs') }}
    WHERE source = 'france_travail'
),

hellowork AS (
    SELECT
        id                                              AS raw_id,
        'hellowork'                                     AS source,
        raw_data->>'offer_id'                           AS source_id,
        -- Extraction titre depuis aria_label si title vide
        CASE
            WHEN raw_data->>'title' != '' THEN raw_data->>'title'
            WHEN raw_data->>'aria_label' LIKE 'Voir offre de%'
            THEN TRIM(
                SPLIT_PART(
                    SPLIT_PART(raw_data->>'aria_label', 'Voir offre de ', 2),
                    ' à ', 1
                )
            )
            ELSE NULL
        END                                             AS titre,
        -- Extraction entreprise depuis aria_label
        CASE
            WHEN raw_data->>'aria_label' LIKE '%chez %'
            THEN TRIM(
                SPLIT_PART(
                    SPLIT_PART(raw_data->>'aria_label', 'chez ', 2),
                    ',', 1
                )
            )
            ELSE NULL
        END                                             AS entreprise,
        raw_data->>'location'                           AS localisation,
        raw_data->>'contract'                           AS type_contrat,
        raw_data->>'aria_label'                         AS description,
        NULL::date                                      AS date_publication,
        raw_data->>'url'                                AS url
    FROM {{ source('public', 'raw_jobs') }}
    WHERE source = 'hellowork'
),

remotive AS (
    SELECT
        id                                              AS raw_id,
        'remotive'                                      AS source,
        (raw_data->>'id')::text                         AS source_id,
        raw_data->>'title'                              AS titre,
        raw_data->>'company_name'                       AS entreprise,
        raw_data->>'candidate_required_location'        AS localisation,
        raw_data->>'job_type'                           AS type_contrat,
        raw_data->>'description'                        AS description,
        (raw_data->>'publication_date')::date           AS date_publication,
        raw_data->>'url'                                AS url
    FROM {{ source('public', 'raw_jobs') }}
    WHERE source = 'remotive'
),

wwr AS (
    SELECT
        id                                              AS raw_id,
        'wwr'                                           AS source,
        raw_data->>'link'                               AS source_id,
        raw_data->>'title'                              AS titre,
        raw_data->>'company'                            AS entreprise,
        'Remote'                                        AS localisation,
        'Remote'                                        AS type_contrat,
        raw_data->>'summary'                            AS description,
        (raw_data->>'published')::date                  AS date_publication,
        raw_data->>'link'                               AS url
    FROM {{ source('public', 'raw_jobs') }}
    WHERE source = 'wwr'
),

greenhouse AS (
    SELECT
        id                                              AS raw_id,
        'greenhouse'                                    AS source,
        (raw_data->>'id')::text                         AS source_id,
        raw_data->>'title'                              AS titre,
        raw_data->>'board_token'                        AS entreprise,
        raw_data->'location'->>'name'                   AS localisation,
        NULL                                            AS type_contrat,
        raw_data->>'content'                            AS description,
        (raw_data->>'updated_at')::date                 AS date_publication,
        raw_data->>'absolute_url'                       AS url
    FROM {{ source('public', 'raw_jobs') }}
    WHERE source = 'greenhouse'
),

unioned AS (
    SELECT * FROM france_travail
    UNION ALL
    SELECT * FROM hellowork
    UNION ALL
    SELECT * FROM remotive
    UNION ALL
    SELECT * FROM wwr
    UNION ALL
    SELECT * FROM greenhouse
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY
                LOWER(TRIM(COALESCE(titre, ''))),
                LOWER(TRIM(COALESCE(entreprise, ''))),
                LOWER(TRIM(COALESCE(localisation, '')))
            ORDER BY
                CASE source
                    WHEN 'france_travail' THEN 1
                    WHEN 'hellowork'      THEN 2
                    WHEN 'greenhouse'     THEN 3
                    WHEN 'remotive'       THEN 4
                    WHEN 'wwr'            THEN 5
                    ELSE 6
                END
        ) AS row_num
    FROM unioned
    WHERE titre IS NOT NULL
      AND titre != ''
)

SELECT
    gen_random_uuid()                                   AS id,
    source,
    source_id,
    TRIM(titre)                                         AS titre,
    TRIM(entreprise)                                    AS entreprise,
    TRIM(localisation)                                  AS localisation,
    UPPER(TRIM(type_contrat))                           AS type_contrat,
    description,
    date_publication,
    url,
    raw_id,
    NOW()                                               AS created_at,
    -- Clé de déduplication pour audit
    LOWER(TRIM(COALESCE(titre, ''))) || '|' ||
    LOWER(TRIM(COALESCE(entreprise, ''))) || '|' ||
    LOWER(TRIM(COALESCE(localisation, '')))             AS dedup_key,

    -- ── Géolocalisation ───────────────────────────────────────────────────────

    -- Détection Remote
    CASE
        WHEN LOWER(TRIM(COALESCE(localisation, ''))) IN ('remote', 'international', 'worldwide', '')
          OR LOWER(TRIM(COALESCE(localisation, ''))) LIKE '%remote%'
          OR LOWER(TRIM(COALESCE(localisation, ''))) LIKE '%télétravail%'
        THEN TRUE
        ELSE FALSE
    END                                                 AS is_remote,

    -- Extraction code département
    -- Format France Travail : "75 - Paris" ou "75 - Paris 12e"
    -- Format HelloWork : "Paris - 75" ou "Cesson-Sévigné - 35"
    CASE
        -- Format "XX - Ville" (France Travail)
        WHEN TRIM(localisation) ~ '^[0-9]{2,3}\s*-'
        THEN REGEXP_REPLACE(TRIM(localisation), '^([0-9]{2,3})\s*-.*', '\1')
        -- Format "Ville - XX" (HelloWork)
        WHEN TRIM(localisation) ~ '-\s*[0-9]{2,3}$'
        THEN REGEXP_REPLACE(TRIM(localisation), '.*-\s*([0-9]{2,3})$', '\1')
        ELSE NULL
    END                                                 AS dept_code,

    -- Jointure avec le seed pour enrichir département et région
    d.dept_nom,
    d.region_nom

FROM ranked r
LEFT JOIN {{ ref('departements') }} d
    ON d.dept_code = CASE
        WHEN TRIM(r.localisation) ~ '^[0-9]{2,3}\s*-'
        THEN REGEXP_REPLACE(TRIM(r.localisation), '^([0-9]{2,3})\s*-.*', '\1')
        WHEN TRIM(r.localisation) ~ '-\s*[0-9]{2,3}$'
        THEN REGEXP_REPLACE(TRIM(r.localisation), '.*-\s*([0-9]{2,3})$', '\1')
        ELSE NULL
    END
WHERE row_num = 1
