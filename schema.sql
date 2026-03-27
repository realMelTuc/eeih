-- EEIH — EVE Exploration Intel Hub
-- Run this against Supabase to create required tables.

CREATE TABLE IF NOT EXISTS eeih_runs (
    id               SERIAL PRIMARY KEY,
    site_type        VARCHAR(20)     NOT NULL DEFAULT 'relic' CHECK (site_type IN ('relic','data')),
    site_name        VARCHAR(200),
    region_name      VARCHAR(100)    NOT NULL,
    system_name      VARCHAR(100),
    security_class   VARCHAR(10)     NOT NULL DEFAULT 'NS' CHECK (security_class IN ('HS','LS','NS','WH')),
    difficulty       VARCHAR(20)     NOT NULL DEFAULT 'standard' CHECK (difficulty IN ('easy','standard','superior','ghost')),
    run_date         DATE            NOT NULL DEFAULT CURRENT_DATE,
    run_time_seconds INTEGER,
    total_loot_value NUMERIC(20,2)   NOT NULL DEFAULT 0,
    notes            TEXT,
    created_at       TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS eeih_loot (
    id             SERIAL PRIMARY KEY,
    run_id         INTEGER         NOT NULL REFERENCES eeih_runs(id) ON DELETE CASCADE,
    item_name      VARCHAR(200)    NOT NULL,
    item_category  VARCHAR(50)     NOT NULL DEFAULT 'misc' CHECK (item_category IN ('artifacts','blueprints','datacores','salvage','modules','misc')),
    quantity       INTEGER         NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price     NUMERIC(20,2)   NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS eeih_runs_region_idx    ON eeih_runs(region_name);
CREATE INDEX IF NOT EXISTS eeih_runs_date_idx      ON eeih_runs(run_date);
CREATE INDEX IF NOT EXISTS eeih_runs_type_idx      ON eeih_runs(site_type);
CREATE INDEX IF NOT EXISTS eeih_runs_created_idx   ON eeih_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS eeih_loot_run_id_idx    ON eeih_loot(run_id);
CREATE INDEX IF NOT EXISTS eeih_loot_category_idx  ON eeih_loot(item_category);
