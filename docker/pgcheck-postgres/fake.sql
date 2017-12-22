CREATE OR REPLACE FUNCTION public.is_master(i_key bigint)
RETURNS boolean
LANGUAGE plpgsql AS
$function$
DECLARE
    read_only boolean;
    closed boolean;
BEGIN
    closed := current_setting('pgcheck.closed', true);
    IF closed IS true
    THEN
        RAISE EXCEPTION 'database closed from load (pgcheck.closed = %)', closed;
    END IF;
    read_only := current_setting('transaction_read_only');
    RETURN NOT read_only;
END
$function$;

CREATE VIEW public.repl_mon AS
    SELECT pg_last_xact_replay_timestamp() AS ts,
           pg_last_wal_replay_lsn() AS location,
           2 AS replics,
           'hostname' AS master;

CREATE TABLE tmp_table (ts timestamptz);
