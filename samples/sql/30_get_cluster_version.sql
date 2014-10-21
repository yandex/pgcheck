CREATE OR REPLACE FUNCTION plproxy.get_cluster_version(i_cluster_name text)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
        ver integer;
BEGIN
    IF i_cluster_name in ('rw', 'ro') THEN
        select version into ver from plproxy.versions;
        RETURN ver;
    END IF;
    RAISE EXCEPTION 'Unknown cluster';
END;
$function$
