package main

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
)

type testCase struct {
	name       string
	inputState []byte
	neededStat Statistics
}

const shardID = 0

var shardsMap = map[int][]string{
	shardID: {
		"shard01-dc1.pgcheck.net",
		"shard01-dc2.pgcheck.net",
		"shard01-dc3.pgcheck.net",
	},
}

var testCases = []testCase{
	{
		"NormalShard",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": true,
				"primary": true,
				"replication_lag": 0,
				"sessions_ratio": 0.08,
				"needed_prio": 0,
				"current_prio": 0,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": true,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0.05,
				"needed_prio": 20,
				"current_prio": 20,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": true,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0.05,
				"needed_prio": 25,
				"current_prio": 25,
				"last_states": []
			}
		}`),
		Statistics{1, 1, 0, 0, 0, 0, 3, 0},
	},
	{
		"DeadReplica",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": true,
				"primary": true,
				"replication_lag": 0,
				"sessions_ratio": 0.08,
				"needed_prio": 0,
				"current_prio": 0,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": true,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0.05,
				"needed_prio": 25,
				"current_prio": 25,
				"last_states": []
			}
		}`),
		Statistics{1, 1, 0, 0, 0, 0, 2, 1},
	},
	{
		"ReadOnlyShard",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": true,
				"primary": false,
				"replication_lag": 10,
				"sessions_ratio": 0.05,
				"needed_prio": 30,
				"current_prio": 30,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": true,
				"primary": false,
				"replication_lag": 15,
				"sessions_ratio": 0.05,
				"needed_prio": 40,
				"current_prio": 40,
				"last_states": []
			}
		}`),
		Statistics{1, 0, 1, 0, 0, 0, 2, 1},
	},
	{
		"NoReplicShard",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": true,
				"primary": true,
				"replication_lag": 0,
				"sessions_ratio": 0.08,
				"needed_prio": 0,
				"current_prio": 0,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": true,
				"primary": false,
				"replication_lag": 100,
				"sessions_ratio": 0.05,
				"needed_prio": 120,
				"current_prio": 120,
				"last_states": []
			}
		}`),
		Statistics{1, 0, 0, 1, 0, 0, 2, 1},
	},
	{
		"SplitBrainShard",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": true,
				"primary": true,
				"replication_lag": 0,
				"sessions_ratio": 0.08,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": true,
				"primary": true,
				"replication_lag": 0,
				"sessions_ratio": 0.16,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": true,
				"primary": false,
				"replication_lag": 10,
				"sessions_ratio": 0.05,
				"needed_prio": 20,
				"current_prio": 20,
				"last_states": []
			}
		}`),
		Statistics{1, 0, 0, 0, 1, 0, 3, 0},
	},
	{
		"FullyDeadShard",
		[]byte(`{
			"shard01-dc1.pgcheck.net": {
				"name": "shard01-dc1.pgcheck.net",
				"dc": "DC1",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc2.pgcheck.net": {
				"name": "shard01-dc2.pgcheck.net",
				"dc": "DC2",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 100,
				"current_prio": 100,
				"last_states": []
			},
			"shard01-dc3.pgcheck.net": {
				"name": "shard01-dc3.pgcheck.net",
				"dc": "DC3",
				"alive": false,
				"primary": false,
				"replication_lag": 0,
				"sessions_ratio": 0,
				"needed_prio": 0,
				"current_prio": 0,
				"last_states": []
			}
		}`),
		Statistics{1, 0, 0, 0, 0, 1, 0, 3},
	},
}

func TestCountStatsForShard(t *testing.T) {
	for _, test := range testCases {
		testOneCase(t, test)
	}
}

func testOneCase(t *testing.T, test testCase) {
	t.Run(test.name, func(t *testing.T) {
		hostsMap := make(map[string]host)
		err := json.Unmarshal(test.inputState, &hostsMap)
		if err != nil {
			t.Error(err)
		}

		state := StatsState{hostsMap, shardsMap}
		var statistic Statistics
		countStatsForShard(&statistic, &state, shardID)

		assert.Equal(t, test.neededStat, statistic, "Wrong statistics")
	})
}
