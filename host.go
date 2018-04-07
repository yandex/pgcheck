package main

import (
	"database/sql"
	"fmt"
	"log"
	"time"
)

type hostInfo struct {
	name     string
	connStr  string
	dc       string
	prioDiff int
	partID   int
}

type hostState struct {
	isAlive        bool
	isPrimary      bool
	replicationLag uint
	sessionsRatio  float64
}

var defaultHostState = hostState{
	isAlive:        false,
	isPrimary:      false,
	replicationLag: 0,
	sessionsRatio:  0,
}

type hostAux struct {
	connectionPool *sql.DB
	statesChan     chan hostState
	lastStates     []hostState
}

type host struct {
	hostInfo
	hostState
	hostPrio
	hostAux
}

func buildHostInfo(db *database, hostname string) *host {
	var host host
	var (
		dc       sql.NullString
		prioDiff sql.NullInt64
	)
	// We assume here that one host may be strictly in one shard
	row := db.pool.QueryRow(
		`SELECT h.host_name, c.conn_string, h.dc, h.prio_diff, p.part_id
		   FROM plproxy.priorities p JOIN
				plproxy.hosts h USING (host_id) JOIN
				plproxy.connections c USING (conn_id)
		  WHERE host_name = $1`, hostname)
	err := row.Scan(&host.name, &host.connStr, &dc, &prioDiff, &host.partID)
	if err != nil {
		log.Printf("Host %s is wrong: %v", hostname, err)
	}

	if dc.Valid {
		host.dc = dc.String
	}
	if prioDiff.Valid {
		host.prioDiff = int(prioDiff.Int64)
	}
	host.connStr = fmt.Sprintf("%s %s", host.connStr, db.config.AppendConnString)

	maxStatesCount := int(db.config.Quorum + db.config.Hysterisis)
	host.statesChan = make(chan hostState, maxStatesCount*3)
	host.lastStates = make([]hostState, 0, maxStatesCount)

	host.connectionPool, err = createPool(&host.connStr, false)
	if err != nil {
		log.Printf("Could not create connection pool for %s", hostname)
	}

	return &host
}

func getHostState(host *host, config *Config, dbname string) *hostState {
	dbConfig := config.Databases[dbname]
	maxStatesCount := int(dbConfig.Quorum + dbConfig.Hysterisis)
	go sendStateToStatesChan(host, &config.DC)

	if len(host.statesChan) > maxStatesCount {
		for i := maxStatesCount; i < len(host.statesChan); i++ {
			<-host.statesChan
		}
	}

	var state hostState
	timeout := time.Second*time.Duration(config.Timeout) + 100*time.Millisecond
	select {
	case x := <-host.statesChan:
		state = x
	case <-time.After(timeout):
		log.Printf("Getting status of %s timed out", host.name)
		state = defaultHostState
	}

	return &state
}

func sendStateToStatesChan(host *host, myDC *string) {
	c := host.statesChan

	db, err := getPool(host)
	if err != nil {
		log.Printf("Connection to %s failed: %v", host.name, err)
		c <- defaultHostState
		return
	}

	state := fillState(db, host)
	c <- state
}

func fillState(db *sql.DB, host *host) hostState {
	state := defaultHostState

	var isMaster bool
	var replicationLag uint
	var sessionsRatio float64
	row := db.QueryRow(`SELECT is_master, lag, sessions_ratio
		FROM public.pgcheck_poll()`)
	err := row.Scan(&isMaster, &replicationLag, &sessionsRatio)
	if err != nil {
		log.Printf("Checking %s failed: %v", host.name, err)
		return state
	}

	state.isAlive = true
	state.isPrimary = isMaster
	state.replicationLag = replicationLag
	state.sessionsRatio = sessionsRatio
	return state
}

func updateLastStates(host *host, state *hostState, maxStatesCount int) *[]hostState {
	var startFrom int
	if len(host.lastStates) != maxStatesCount {
		startFrom = 0
	} else {
		startFrom = 1
	}
	result := append(host.lastStates[startFrom:], *state)
	//log.Printf("Last states of %s are: %v", host.name, result)
	return &result
}

func updateState(hostsInfo *map[string]*host, hostname string, state *hostState, quorum uint, myDC string) {
	hosts := *hostsInfo
	host := hosts[hostname]
	neededPrio := stateToPrio(host, state, &myDC)

	if prioIsNear(host.currentPrio, neededPrio) {
		hosts[hostname].hostState = *state
		return
	}

	var cnt uint
	for i := range hosts[hostname].lastStates {
		prio := stateToPrio(host, &host.lastStates[i], &myDC)
		if prioIsNear(prio, neededPrio) {
			cnt++
		}
	}
	if cnt >= quorum {
		hosts[hostname].neededPrio = neededPrio
		hosts[hostname].hostState = *state
	} else {
		hosts[hostname].neededPrio = hosts[hostname].currentPrio
	}
}
