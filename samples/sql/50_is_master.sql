CREATE OR REPLACE FUNCTION plproxy.is_master(i_key bigint)
RETURNS smallint AS $$
    CLUSTER 'rw';
    RUN ON plproxy.select_part(i_key);
    TARGET public.is_master;
$$ LANGUAGE plproxy;
