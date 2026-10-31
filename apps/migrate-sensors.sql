\connect smarthome
BEGIN;
INSERT INTO devices.devices (id, name, type, location, value, unit, status, last_updated, created_at)
SELECT id, name, type, location, COALESCE(value, 0), COALESCE(unit, ''), status, last_updated, created_at
FROM public.sensors
ON CONFLICT (id) DO NOTHING;
SELECT setval(pg_get_serial_sequence('devices.devices', 'id'),
              GREATEST((SELECT last_value FROM devices.devices_id_seq),
                       COALESCE((SELECT MAX(id) FROM devices.devices), 1)),
              (SELECT is_called FROM devices.devices_id_seq)
              OR EXISTS (SELECT 1 FROM devices.devices));
COMMIT;
