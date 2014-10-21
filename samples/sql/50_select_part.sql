CREATE OR REPLACE FUNCTION plproxy.select_part(i_key bigint)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
declare
    part bigint;
begin
    select part_id into part from plproxy.key_ranges where i_key between start_key and end_key;
    if (part is null) then
        raise exception 'No range for this key';
    end if;
    return part;
end; 
$function$
