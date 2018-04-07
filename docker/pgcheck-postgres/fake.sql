CREATE FUNCTION public.pgcheck_poll(
    OUT is_master boolean,
    OUT lag integer,
    OUT sessions_ratio float
) AS $$
DECLARE
    closed boolean;
    sessions integer;
BEGIN
    closed := current_setting('pgcheck.closed', true);
    IF closed IS true THEN
        RAISE EXCEPTION 'Database is closed from load (pgcheck.closed = %)', closed;
    END IF;

    SELECT NOT pg_is_in_recovery()
          INTO is_master;

    IF is_master THEN
        SELECT 0 INTO lag;
    ELSE
        SELECT ROUND(extract(epoch FROM clock_timestamp() - ts))::integer
          FROM public.repl_mon
          INTO lag;
    END IF;

    SELECT count(*)
      FROM pg_stat_activity
      INTO sessions;

    SELECT sessions / setting::float
      FROM pg_settings
      INTO sessions_ratio
     WHERE name = 'max_connections';
END
$$ LANGUAGE plpgsql SECURITY DEFINER;


CREATE VIEW public.repl_mon AS
    SELECT pg_last_xact_replay_timestamp() AS ts,
           pg_last_wal_replay_lsn() AS location,
           2 AS replics,
           'hostname' AS master;


CREATE TABLE tmp_table (ts timestamptz);
