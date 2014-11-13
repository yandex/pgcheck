# Pgcheck

Tool for monitoring backend databases from PL/Proxy hosts and changing `plproxy.get_cluster_partitions` function output.

## How does it work?

Pgcheck checks health status of each host of PostgreSQL clusters and assigns them priorities. Right now the assigned priorities are:
* `0` - the master,
* `10` - the synchronous replica,
* `20` - asynchronous replica in the same (as plproxy-host) datacenter,
* `30` - asynchronous replica in any other datacenter,
* `100` - dead hosts.

In our environment plproxy-host, when taking decision where to route the query, by default takes host with the lowest priority. So in general all queries go to the master. If it fails, the queries are routed to one of the replicas. This gives us read-only degradation in case of master fail.

If you set `replics_weights = yes` in config-file, replics priorities diffs would be calculated depending on its load. The resulting priority is increase by this diff. The load of the replica right now can be calculated in two simple ways depending on `load_calculation` parameter:
* `load_calculation = pgbouncer` - will be calculated depending on pgbouncer client connections,
* `load_calculation = postgres` - will be calculated depending on PostgreSQL client connections (all connections from pg_stat_activity, not only in `active` state).

If you set `account_replication_lag = yes`, replics priorities would be also increased by one for each megabyte of replication relay delay.

In our environment information about shards, hosts and their priorities is kept in special tables (you can see sqls for creating them in `samples/sql` directory). Pgcheck forks two processes on each cluster defined in config-file - one for getting current priorities of hosts and one for calculating the so-called base priorities.
First loop is executed very fast (every second with timeout of one second for every operation), in order to lose as little queries as possible in case of problems with any host. It refreshes the value for field `priority` in the `priorities` table and assigns next values:
* `0` if the host is master, not depending on the value of `base_prio`,
* `100` if the host is dead, in any case,
* `base_prio+prio_diff`, if the host is replica and alive.
Because of network flaps frequent changes of priorities may occur, there are parameters `quorum` and `hysterisis` for every cluster. Details for them are below.

The second loop is executed once in `base_prio_timeout` seconds and it refreshes values of field `base_prio` in table `hosts`. Because this information does not change frequently this loop is executed less often and timeouts are not so aggressive. If for some host in this loop priority could not be calculated, none of the priorities would be changed.

Also there is `prio_diff` field in table `hosts`, which is taken in account when assigning current priorities for replics. It may be needed for changing priority of any host by hand.

## Installation

For RedHat-based systems you can use spec-file from the repo to build a package. For other distroes you can build needed packages with `setup.py`.
The package will install all needed libraries and dependencies, but it will not create database(s) with needed tables and functions and it will not install needed config-files. Samples for sql-files (creating needed schema and functions) and config files can be found in the `samples` directory. In our environment they come from different package and are managed by our SCM.

## Short tutorial

```
yum -y install pgcheck
vim /etc/pgcheck.conf
/etc/init.d/pgcheck start
tail -f /var/log/pgcheck/pgcheck.log
```

## Config-file

Sample config file can be found in `samples/etc/pgcheck.conf`. All the parameters have comments with explanations except for two of them - `quorum` and `hysteris`.

For each host in memory there will be stored information about `quorum+hysterisis` last priorities. If `quorum` of them are the same as the last one, it will be assigned. For example, if `quorum = 3` and `hysterisis = 2`, there will be floating window of 5 last priorities and the logic will be next:
* `[0, 100, 0, 100, 100]` - priority `100` will be assigned,
* `[100, 100, 0, 100, 0]` - priority will not be changed,
* `[100, 100, 0, 0, 0]` - priority will be changed to `0`.
