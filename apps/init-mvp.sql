\connect smarthome

CREATE SCHEMA IF NOT EXISTS devices;
CREATE TABLE IF NOT EXISTS devices.homes (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);
INSERT INTO devices.homes (id, name) VALUES (1, 'Demo home') ON CONFLICT DO NOTHING;
SELECT setval(pg_get_serial_sequence('devices.homes', 'id'), (SELECT MAX(id) FROM devices.homes));

CREATE TABLE IF NOT EXISTS devices.devices (
    id BIGSERIAL PRIMARY KEY,
    home_id BIGINT NOT NULL DEFAULT 1 REFERENCES devices.homes(id),
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    location VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL DEFAULT 0,
    unit VARCHAR(20) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'inactive',
    last_updated TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_devices_home ON devices.devices(home_id);

CREATE SCHEMA IF NOT EXISTS telemetry;
CREATE TABLE IF NOT EXISTS telemetry.measurements (
    id UUID PRIMARY KEY,
    device_id BIGINT NOT NULL,
    home_id BIGINT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_measurement_history ON telemetry.measurements(device_id, observed_at DESC);
