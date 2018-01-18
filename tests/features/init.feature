Feature: Infrastructure works correctly

    Scenario: Pgcheck initial values are correct
        Given a deployed cluster
         Then connection strings for "rw" cluster are:
            | get_cluster_partitions                            |
            | host=shard01-dc1.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc2.pgcheck.net port=6432 dbname=db1 |
          And connection strings for "ro" cluster are:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc1.pgcheck.net port=6432 dbname=db1 |
