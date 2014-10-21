CREATE OR REPLACE FUNCTION plproxy.inc_cluster_version()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    update plproxy.versions set version = version + 1;
    return null;
END;
$function$;

DROP TRIGGER IF EXISTS update_cluster_version on plproxy.priorities;
CREATE TRIGGER update_cluster_version AFTER INSERT or DELETE or UPDATE on plproxy.priorities for each statement execute procedure plproxy.inc_cluster_version();
