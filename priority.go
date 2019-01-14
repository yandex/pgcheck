package main

import (
	"database/sql"
	"log"
)

type priority uint

const (
	alivePrimaryPrio priority = 0
	aliveStandbyPrio priority = 10
	deadHostPrio     priority = 100
)

type hostPrio struct {
	CurrentPrio priority
	NeededPrio  priority
}

func prioIsNear(currentPrio, newPrio priority) bool {
	const magic = 5
	lower := int(currentPrio) - magic
	upper := int(currentPrio) + magic
	if int(newPrio) >= lower && int(newPrio) <= upper {
		return true
	}
	return false
}

func stateToPrio(host *host, state *hostState, myDC *string) priority {
	if !state.IsAlive {
		return deadHostPrio
	} else if state.IsPrimary {
		return alivePrimaryPrio
	}

	prio := aliveStandbyPrio
	if host.DC != *myDC {
		prio += 10
	}
	prio += priority(state.ReplicationLag)
	prio += priority(state.SessionsRatio * 100.0 / 2)

	// prioDiff may be negative so we cast everything to int first
	// and then back to priority type
	p := int(prio) + host.prioDiff
	if p < 0 {
		p = int(deadHostPrio) - p
	}
	prio = priority(p)

	return prio
}

func updateHostPriority(db *sql.DB, hostname string, prio priority) {
	_, err := db.Exec(
		`UPDATE plproxy.priorities
		    SET priority = $1
		  WHERE host_id = (
			  SELECT host_id FROM plproxy.hosts WHERE host_name = $2
			)`, prio, hostname)
	if err != nil {
		log.Printf("Setting priority for %s failed: %v", hostname, err)
	}
}
