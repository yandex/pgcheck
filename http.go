package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
)

type statsState struct {
	dbname    string
	hostsMap  map[string]*host
	shardsMap map[int][]string
}

// StatsState is a type for marshaling to JSON
type StatsState struct {
	HostsMap  map[string]host  `json:"hosts"`
	ShardsMap map[int][]string `json:"shards"`
}

// Statistics contains current statistics
type Statistics struct {
	TotalShards      uint `json:"total_shards"`
	NormalShards     uint `json:"normal_shards"`
	ReadOnlyShards   uint `json:"read_only_shards"`
	NoReplicShards   uint `json:"shards_without_replicas"`
	SplitBrainShards uint `json:"split_brain_shards"`
	FullyDeadShards  uint `json:"fully_dead_shards"`
	AliveHosts       uint `json:"alive_hosts"`
	DeadHosts        uint `json:"dead_hosts"`
}

var currentState = make(map[string]StatsState)

func currentStateHandler(w http.ResponseWriter, r *http.Request) {
	state, err := json.Marshal(currentState)
	if err != nil {
		log.Println(err)
		return
	}
	w.Header().Set("Content-type", "application/json")
	fmt.Fprintf(w, string(state))
}

func statisticsHandler(w http.ResponseWriter, r *http.Request) {
	var statistic Statistics
	for _, state := range currentState {
		for shardID := range state.ShardsMap {
			countStatsForShard(&statistic, &state, shardID)
		}
	}

	stats, err := json.Marshal(statistic)
	if err != nil {
		log.Println(err)
		return
	}
	w.Header().Set("Content-type", "application/json")
	fmt.Fprintf(w, string(stats))
}

func startStatsServer(config Config, ch chan statsState) {
	for db := range config.Databases {
		currentState[db] = StatsState{}
	}

	go startUpdatingStats(ch)

	http.HandleFunc("/state", currentStateHandler)
	http.HandleFunc("/stats", statisticsHandler)
	log.Print(http.ListenAndServe(":8080", nil))
}

func startUpdatingStats(ch chan statsState) {
	for {
		x := <-ch
		currentState[x.dbname] = state2State(x)
	}
}

func countStatsForShard(statistic *Statistics, state *StatsState, shardID int) {
	shardHosts := state.ShardsMap[shardID]
	aliveMasters := 0
	aliveReplics := 0
	notDelayedReplics := 0

	for _, fqdn := range shardHosts {
		hostState := state.HostsMap[fqdn]

		if hostState.IsAlive {
			statistic.AliveHosts++
			if hostState.IsPrimary {
				aliveMasters++
			} else {
				aliveReplics++
				if hostState.ReplicationLag < 90 {
					notDelayedReplics++
				}
			}
		} else {
			statistic.DeadHosts++
		}
	}

	statistic.TotalShards++
	if aliveMasters == 0 {
		if aliveReplics == 0 {
			statistic.FullyDeadShards++
		} else {
			statistic.ReadOnlyShards++
		}
	} else if aliveMasters > 1 {
		statistic.SplitBrainShards++
		// Below aliveMasters == 1
	} else if aliveReplics == 0 || notDelayedReplics == 0 {
		statistic.NoReplicShards++
	} else if aliveReplics > 0 {
		statistic.NormalShards++
	}
}

func state2State(in statsState) StatsState {
	tmpState := StatsState{}
	tmpState.ShardsMap = in.shardsMap

	tmpState.HostsMap = make(map[string]host)
	for k := range in.hostsMap {
		tmpState.HostsMap[k] = *in.hostsMap[k]
	}

	return tmpState
}
