# Pgcheck
[![Go Report Card](https://goreportcard.com/badge/github.com/yandex/pgcheck)](https://goreportcard.com/report/github.com/yandex/pgcheck)
[![Build Status](https://travis-ci.org/yandex/pgcheck.svg?branch=master)](https://travis-ci.org/yandex/pgcheck)

Tool for monitoring backend databases from PL/Proxy hosts and changing `plproxy.get_cluster_partitions` function output.

## How does it work?

Pgcheck checks health status of each host of PostgreSQL clusters and assigns them priorities. Right now the assigned priorities are:
* `0` - the master,
* `10` - asynchronous replica in the same (as plproxy-host) datacenter,
* `20` - asynchronous replica in any other datacenter,
* `100` - dead hosts.

In our environment plproxy-host, when taking decision where to route the query, by default takes host with the lowest priority. So in general all queries go to the master. If it fails, the queries are routed to one of the replicas. This gives us read-only degradation in case of master fail.

If you set `replics_weights = yes` in config-file, replics priorities diffs would be calculated depending on its load. The resulting priority is increase by this diff. The load of the replica will be calculated depending on PostgreSQL client connections (all connections from pg_stat_activity, not only in `active` state).

If you set `account_replication_lag = yes`, replics priorities would be also increased by one for each second of replication replay delay. Replication delay in seconds is measured with [repl_mon](https://github.com/dev1ant/repl_mon).

In our environment information about shards, hosts and their priorities is kept in special tables (you can see sqls for creating them in `samples/sql` directory). Pgcheck created a goroutine for each cluster defined in config-file.
The loop inside the goroutine is executed every `iteration_timeout` and it refreshes the value for field `priority` in the `priorities` table and assigns next values:
* `0` if the host is master,
* `100` if the host is dead, in any case,
* `calculated_prio+prio_diff`, if the host is replica and alive.
Because of network flaps frequent changes of priorities may occur, so there are parameters `quorum` and `hysterisis` for every cluster. Details for them are below.

The `prio_diff` field in table `hosts` is taken in account when assigning current priorities for replics. It may be needed for changing priority of any host by hand.

## Installation

Compile the binary with standard `go build` and install it where you want.
The binary will be statically linked, so without any dependencies but it will not create database(s) with needed tables and functions and it will not install needed config-files. Samples for sql-files (creating needed schema and functions) and config files can be found in the `samples` directory. In our environment they come from different package and are managed by our SCM.

You could also see an example of deploying pgcheck in tests infrastructure.

## Config-file

Sample config file can be found in `samples/etc/pgcheck.yml`. All the parameters have comments with explanations except for two of them - `quorum` and `hysteris`.

For each host in memory there will be stored information about `quorum+hysterisis` last priorities. If `quorum` of them are the same as the last one, it will be assigned. For example, if `quorum = 3` and `hysterisis = 2`, there will be floating window of 5 last priorities and the logic will be next:
* `[0, 100, 0, 100, 100]` - priority `100` will be assigned,
* `[100, 100, 0, 100, 0]` - priority will not be changed,
* `[100, 100, 0, 0, 0]` - priority will be changed to `0`,
* `[100, 100, 0, 0, 100]` - priority will be changed to `100`.
