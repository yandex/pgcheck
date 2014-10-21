CREATE OR REPLACE FUNCTION plproxy.get_cluster_partitions(i_cluster_name text)
 RETURNS SETOF text
 LANGUAGE plpgsql
AS $function$
declare
    r record;
    min_priority integer;
    tmp integer;
begin
    if (i_cluster_name = 'rw') then
        min_priority:=0;
    elsif (i_cluster_name = 'ro') then
        min_priority:=1;
    else
        raise exception 'Unknown cluster';
    end if;
    for r in
        select distinct(part_id) from plproxy.parts order by part_id
    loop
        select min(priority) into tmp from plproxy.priorities p where p.part_id=r.part_id and priority>=min_priority;
        if (tmp is null or tmp >= 100) then
            min_priority:=0;
        end if;
        return next (select conn_string from plproxy.connections c, plproxy.priorities p where p.part_id=r.part_id and p.conn_id=c.conn_id and priority>=min_priority order by priority limit 1);
    end loop;
    return;
end; 
$function$
