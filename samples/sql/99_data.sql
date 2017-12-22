INSERT INTO plproxy.parts VALUES (0), (1);
INSERT INTO plproxy.key_ranges VALUES (0, 0, 0, 511), (1, 1, 512, 1023);
INSERT INTO plproxy.hosts (host_id, host_name) VALUES
    (1, 'shard01-dc1.pgcheck.net'),
    (2, 'shard01-dc2.pgcheck.net'),
    (3, 'shard01-dc3.pgcheck.net'),
    (4, 'shard02-dc1.pgcheck.net'),
    (5, 'shard02-dc2.pgcheck.net'),
    (6, 'shard02-dc3.pgcheck.net');
INSERT INTO plproxy.connections VALUES
    (1, 'host=shard01-dc1.pgcheck.net port=6432 dbname=db1'),
    (2, 'host=shard01-dc2.pgcheck.net port=6432 dbname=db1'),
    (3, 'host=shard01-dc3.pgcheck.net port=6432 dbname=db1'),
    (4, 'host=shard02-dc1.pgcheck.net port=6432 dbname=db1'),
    (5, 'host=shard02-dc2.pgcheck.net port=6432 dbname=db1'),
    (6, 'host=shard02-dc3.pgcheck.net port=6432 dbname=db1');
INSERT INTO plproxy.priorities VALUES
    (0, 1, 1, 10),
    (0, 2, 2, 10),
    (0, 3, 3, 10),
    (1, 4, 4, 10),
    (1, 5, 5, 10),
    (1, 6, 6, 10);
