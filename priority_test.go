package main

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

type stateToPrioTestCase struct {
	name       string
	inHost     host
	inState    hostState
	inDC       string
	neededPrio priority
}

var stateToPrioTestCases = []stateToPrioTestCase{
	{
		"Alive master",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, true, 0, 0.08},
		"DC2",
		0,
	},
	{
		"Dead host",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{false, false, 0, 0},
		"DC2",
		100,
	},
	{
		"Alive replica in other DC",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, false, 0, 0.08},
		"DC2",
		24,
	},
	{
		"Alive replica in same DC",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, false, 0, 0.08},
		"DC1",
		14,
	},
	{
		"Alive replica with replication lag",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, false, 10, 0.08},
		"DC2",
		34,
	},
	{
		"Alive overloaded replica",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, false, 0, 0.9},
		"DC2",
		65,
	},
	{
		"Alive delayed and overloaded replica",
		host{
			hostInfo{"shard01-dc1.pgcheck.net", "", "DC1", 0, 0},
			hostState{},
			hostPrio{},
			hostAux{},
		},
		hostState{true, false, 50, 0.9},
		"DC2",
		115,
	},
}

func TestStateToPrio(t *testing.T) {
	for _, test := range stateToPrioTestCases {
		t.Run(test.name, func(t *testing.T) {
			prio := stateToPrio(&test.inHost, &test.inState, &test.inDC)
			assert.Equal(t, int(test.neededPrio), int(prio), "Wrong priority")
		})
	}
	assert.Equal(t, 1, 1, "Shit")
}
