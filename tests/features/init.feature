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

    Scenario: Dead host is handled correctly
        Given a deployed cluster
         When we pause "shard01-dc1" container
         Then within 5 seconds connection strings for "rw" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc2.pgcheck.net port=6432 dbname=db1 |

         When we unpause "shard01-dc1" container
         Then within 5 seconds connection strings for "rw" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc1.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc2.pgcheck.net port=6432 dbname=db1 |

         When we pause "shard01-dc2" container
         Then within 5 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc3.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc1.pgcheck.net port=6432 dbname=db1 |

         When we unpause "shard01-dc2" container
         Then within 12 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc1.pgcheck.net port=6432 dbname=db1 |

    Scenario: Delayed replica is handled correctly
        Given a deployed cluster
         When we pause replay on "shard02-dc1"
         Then within 20 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc3.pgcheck.net port=6432 dbname=db1 |

         When we resume replay on "shard02-dc1"
          Then within 20 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc1.pgcheck.net port=6432 dbname=db1 |

    @long
    Scenario: All delayed replics are handled correctly
        Given a deployed cluster
         When we pause replay on "shard02-dc1"
          And we pause replay on "shard02-dc3"
         Then within 100 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc2.pgcheck.net port=6432 dbname=db1 |

         When we resume replay on "shard02-dc1"
          And we resume replay on "shard02-dc3"
          Then within 10 seconds connection strings for "ro" cluster changes to:
            | get_cluster_partitions                            |
            | host=shard01-dc2.pgcheck.net port=6432 dbname=db1 |
            | host=shard02-dc1.pgcheck.net port=6432 dbname=db1 |