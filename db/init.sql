-- HydroViz PostGIS Schema Initialisation
-- Auto-run on first container start via docker-entrypoint-initdb.d

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Job tracking
CREATE TABLE jobs (
    job_id          UUID PRIMARY KEY,
    bbox            GEOMETRY(Polygon, 4326) NOT NULL,
    event_date      DATE NOT NULL,
    osm_snapshot    DATE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'queued',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    options         JSONB DEFAULT '{}'
);

-- Provenance log (one row per input per job)
CREATE TABLE provenance (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    source          TEXT NOT NULL,  -- 's1', 's2', 'dem', 'osm', 'model'
    acquisition_id  TEXT,
    datetime        TIMESTAMPTZ,
    platform        TEXT,
    relative_orbit  INTEGER,
    direction       TEXT,
    snapshot_date   DATE,
    model_version   TEXT,
    model_sha256    TEXT,
    file_path       TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Flood/debris mask statistics
CREATE TABLE flood_stats (
    job_id              UUID REFERENCES jobs(job_id),
    flooded_area_km2    REAL,
    debris_area_km2     REAL,
    mean_confidence     REAL,
    mode                TEXT,  -- 'sar_only' | 'sar_s2'
    mask_cog_path       TEXT,
    debris_cog_path     TEXT,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- OSM-derived features
CREATE TABLE buildings (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    osm_id          BIGINT,
    geom            GEOMETRY(Polygon, 4326),
    exposure        TEXT,  -- 'exposed_high' | 'exposed_medium' | 'unaffected'
    confidence      REAL
);

CREATE TABLE roads (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    osm_id          BIGINT,
    geom            GEOMETRY(LineString, 4326),
    highway_type    TEXT,
    total_length_m  REAL,
    exposed_length_m REAL
);

CREATE TABLE bridges (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    osm_id          BIGINT,
    geom            GEOMETRY(Geometry, 4326),
    status          TEXT,  -- 'likely_damaged' | 'exposed' | 'unaffected'
    confidence      REAL,
    hand_height     REAL
);

CREATE TABLE settlements (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    osm_id          BIGINT,
    name            TEXT,
    name_ne         TEXT,
    geom            GEOMETRY(Point, 4326),
    place_type      TEXT,
    cutoff_status_strict       TEXT,  -- 'isolated' | 'detour' | 'reachable' | 'unknown'
    cutoff_status_conservative TEXT,
    nearest_town    TEXT,
    nearest_hospital TEXT,
    detour_factor_strict       REAL,
    detour_factor_conservative REAL
);

-- Flood path (bonus)
CREATE TABLE flood_paths (
    id              SERIAL PRIMARY KEY,
    job_id          UUID REFERENCES jobs(job_id),
    origin          GEOMETRY(Point, 4326),
    path            GEOMETRY(LineString, 4326),
    corridor        GEOMETRY(Polygon, 4326),
    hand_threshold  REAL,
    agreement_pct   REAL  -- agreement with observed mask
);

CREATE TABLE flood_path_settlements (
    id              SERIAL PRIMARY KEY,
    flood_path_id   INTEGER REFERENCES flood_paths(id),
    settlement_id   INTEGER REFERENCES settlements(id),
    distance_downstream_m REAL,
    order_index     INTEGER
);

-- Materialised facts view
CREATE TABLE facts (
    job_id          UUID PRIMARY KEY REFERENCES jobs(job_id),
    facts_json      JSONB NOT NULL,
    generated_at    TIMESTAMPTZ DEFAULT now()
);

-- Spatial indexes for query performance
CREATE INDEX idx_buildings_geom ON buildings USING GIST (geom);
CREATE INDEX idx_roads_geom ON roads USING GIST (geom);
CREATE INDEX idx_bridges_geom ON bridges USING GIST (geom);
CREATE INDEX idx_settlements_geom ON settlements USING GIST (geom);
CREATE INDEX idx_flood_paths_corridor ON flood_paths USING GIST (corridor);
CREATE INDEX idx_jobs_bbox ON jobs USING GIST (bbox);

-- Functional indexes for common lookups
CREATE INDEX idx_provenance_job ON provenance (job_id);
CREATE INDEX idx_buildings_job ON buildings (job_id);
CREATE INDEX idx_roads_job ON roads (job_id);
CREATE INDEX idx_bridges_job ON bridges (job_id);
CREATE INDEX idx_settlements_job ON settlements (job_id);
