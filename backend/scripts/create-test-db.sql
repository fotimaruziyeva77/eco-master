-- Runs once when the dev database volume is first created.
-- A separate database keeps pytest runs away from development data.
CREATE DATABASE ekoustoz_test OWNER ekoustoz;
