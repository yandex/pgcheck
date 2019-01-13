package main

import (
	"database/sql"
	"log"
	"time"

	_ "github.com/lib/pq"
)

func main() {
	var config Config
	config = parseConfig()
	initLogging(&config)

	for db := range config.Databases {
		go processDB(db, &config)
	}

	handleSignals()
}

func processDB(dbname string, config *Config) {
	var db database
	db.name = dbname
	db.config = config.Databases[dbname]
	db.pool, _ = createPool(&db.config.LocalConnString, true)
	defer db.pool.Close()

	hosts := buildInitialHostsInfo(&db)
	shards := buildShardsInfo(hosts)

	for {
		updateHostsState(hosts, config, dbname)
		correctPrioForHostsInShard(shards, hosts)
		updatePriorities(db.pool, hosts)
		time.Sleep(time.Second)
	}
}

func buildInitialHostsInfo(db *database) *map[string]*host {
	rows, err := db.pool.Query("SELECT distinct(host_name) FROM plproxy.hosts")
	if err != nil {
		log.Printf("%s: %s", db.name, err)
	}
	defer rows.Close()

	hosts := make(map[string]*host)

	for rows.Next() {
		var hostname string
		if err := rows.Scan(&hostname); err != nil {
			log.Printf("%s: %s", db.name, err)
		}

		hosts[hostname] = buildHostInfo(db, hostname)
	}

	if err := rows.Err(); err != nil {
		log.Printf("%s: %s", db.name, err)
	}

	return &hosts
}

func buildShardsInfo(hostsInfo *map[string]*host) *map[int][]string {
	hosts := *hostsInfo
	shards := make(map[int][]string)
	for hostname := range hosts {
		shard := hosts[hostname].partID
		shards[shard] = append(shards[shard], hostname)
	}
	return &shards
}

func updateHostsState(hostsInfo *map[string]*host, wholeConfig *Config, dbname string) {
	config := wholeConfig.Databases[dbname]
	maxStatesCount := int(config.Quorum + config.Hysterisis)

	hosts := *hostsInfo
	for hostname := range hosts {
		host := hosts[hostname]
		state := getHostState(host, wholeConfig, dbname)
		hosts[hostname].LastStates = *updateLastStates(host, state, maxStatesCount)
		updateState(&hosts, hostname, state, config.Quorum, wholeConfig.DC)
	}
}

func correctPrioForHostsInShard(shardsInfo *map[int][]string, hostsInfo *map[string]*host) {
	shards := *shardsInfo
	hosts := *hostsInfo

	// TODO: write tests for this feature
	for partID, hostsList := range shards {
		var masters []string
		for _, h := range hostsList {
			if hosts[h].IsAlive && hosts[h].IsPrimary {
				masters = append(masters, h)
			}
		}
		//log.Printf("%d: %d masters", partID, len(masters))
		if len(masters) > 1 {
			log.Printf("%d masters in shard %d. Changing priority for "+
				"all of them to %d", len(masters), partID, deadHostPrio)
			for _, h := range masters {
				hosts[h].NeededPrio = deadHostPrio
			}
		}

		if len(masters) == 0 {
			for _, h := range hostsList {
				if !hosts[h].IsPrimary && hosts[h].IsAlive {
					// Do not account replication lag since master is dead
					// and nothing is written
					hosts[h].NeededPrio =
						hosts[h].NeededPrio - priority(hosts[h].ReplicationLag)
				}
			}
		}
	}
}

func updatePriorities(db *sql.DB, hostsInfo *map[string]*host) {
	hosts := *hostsInfo
	for hostname := range hosts {
		s := hosts[hostname]
		//log.Printf("%s: current %d, needed %d", s.name, s.currentPrio, s.neededPrio)
		if s.CurrentPrio != s.NeededPrio {
			hosts[hostname].CurrentPrio = s.NeededPrio
			updateHostPriority(db, hostname, s.NeededPrio)
			log.Printf("Priority of host %s has been changed to %d ",
				hostname, s.NeededPrio)
		}
	}
}
