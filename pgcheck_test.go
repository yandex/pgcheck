package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

type correctPrioForHostsInShardTestCase struct {
	name             string
	inHostsInfo      map[string]*host
	neededPriorities map[string]priority
}

var correctPrioForHostsInShardTestCases = []correctPrioForHostsInShardTestCase{
	{
		"Normal",
		map[string]*host{
			"shard01-dc1.pgcheck.net": &host{
				hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
				hostState{true, true, 0, 0.08},
				hostPrio{0, 0},
				hostAux{nil, nil, nil},
			},
			"shard01-dc2.pgcheck.net": &host{
				hostInfo{"shard01-dc2.pgcheck.net", "", "DC2", 0, 0},
				hostState{true, false, 1, 0.05},
				hostPrio{11, 11},
				hostAux{nil, nil, nil},
			},
			"shard01-dc3.pgcheck.net": &host{
				hostInfo{"shard01-dc3.pgcheck.net", "", "DC3", 0, 0},
				hostState{true, false, 0, 0.05},
				hostPrio{20, 20},
				hostAux{nil, nil, nil},
			},
		},
		map[string]priority{
			"shard01-dc1.pgcheck.net": 0,
			"shard01-dc2.pgcheck.net": 11,
			"shard01-dc3.pgcheck.net": 20,
		},
	},
	{
		"Split brain without replication lag",
		map[string]*host{
			"shard01-dc1.pgcheck.net": &host{
				hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
				hostState{true, true, 0, 0.08},
				hostPrio{0, 0},
				hostAux{nil, nil, nil},
			},
			"shard01-dc2.pgcheck.net": &host{
				hostInfo{"shard01-dc2.pgcheck.net", "", "DC2", 0, 0},
				hostState{true, true, 0, 0.08},
				hostPrio{0, 0},
				hostAux{nil, nil, nil},
			},
			"shard01-dc3.pgcheck.net": &host{
				hostInfo{"shard01-dc3.pgcheck.net", "", "DC3", 0, 0},
				hostState{true, false, 0, 0.05},
				hostPrio{20, 20},
				hostAux{nil, nil, nil},
			},
		},
		map[string]priority{
			"shard01-dc1.pgcheck.net": 100,
			"shard01-dc2.pgcheck.net": 100,
			"shard01-dc3.pgcheck.net": 20,
		},
	},
	{
		"Split brain with replication lag",
		map[string]*host{
			"shard01-dc1.pgcheck.net": &host{
				hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
				hostState{true, true, 0, 0.08},
				hostPrio{0, 0},
				hostAux{nil, nil, nil},
			},
			"shard01-dc2.pgcheck.net": &host{
				hostInfo{"shard01-dc2.pgcheck.net", "", "DC2", 0, 0},
				hostState{true, true, 0, 0.08},
				hostPrio{0, 0},
				hostAux{nil, nil, nil},
			},
			"shard01-dc3.pgcheck.net": &host{
				hostInfo{"shard01-dc3.pgcheck.net", "", "DC3", 0, 0},
				hostState{true, false, 100500, 0.05},
				hostPrio{100520, 100520},
				hostAux{nil, nil, nil},
			},
		},
		map[string]priority{
			"shard01-dc1.pgcheck.net": 100,
			"shard01-dc2.pgcheck.net": 100,
			"shard01-dc3.pgcheck.net": 20,
		},
	},
	{
		"No master with replication lag",
		map[string]*host{
			"shard01-dc1.pgcheck.net": &host{
				hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
				hostState{false, false, 0, 0},
				hostPrio{100, 100},
				hostAux{nil, nil, nil},
			},
			"shard01-dc2.pgcheck.net": &host{
				hostInfo{"shard01-dc2.pgcheck.net", "", "DC2", 0, 0},
				hostState{true, false, 100500, 0.08},
				hostPrio{100510, 100510},
				hostAux{nil, nil, nil},
			},
			"shard01-dc3.pgcheck.net": &host{
				hostInfo{"shard01-dc3.pgcheck.net", "", "DC3", 0, 0},
				hostState{true, false, 100500, 0.05},
				hostPrio{100520, 100520},
				hostAux{nil, nil, nil},
			},
		},
		map[string]priority{
			"shard01-dc1.pgcheck.net": 100,
			"shard01-dc2.pgcheck.net": 10,
			"shard01-dc3.pgcheck.net": 20,
		},
	},
}

func TestCorrectPrioForHostsInShard(t *testing.T) {
	for _, test := range correctPrioForHostsInShardTestCases {
		t.Run(test.name, func(t *testing.T) {
			// We use shardsMap from http_test.go, ugly but works
			correctPrioForHostsInShard(&shardsMap, &test.inHostsInfo)
			resultPrioritites := make(map[string]priority)
			for h := range test.neededPriorities {
				resultPrioritites[h] = test.inHostsInfo[h].NeededPrio
			}
			assert.Equal(t, test.neededPriorities, resultPrioritites, "Needed priorities mismatch")
		})
	}
}
