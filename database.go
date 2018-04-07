package main

import (
	"database/sql"
	"log"
	"time"
)

type database struct {
	name   string
	config DBConfig
	pool   *sql.DB
}

func createPool(connStr *string, wait bool) (*sql.DB, error) {
	for {
		db, err := sql.Open("postgres", *connStr)
		if err == nil {
			db.SetConnMaxLifetime(time.Hour)
			db.SetMaxIdleConns(5)
			return db, err
		}

		if !wait {
			return nil, err
		}

		log.Printf("Connection to '%s' failed: %s", *connStr, err)
		time.Sleep(time.Second)
		defer db.Close()
	}
}

func getPool(host *host) (*sql.DB, error) {
	var db *sql.DB
	var err error
	if host.connectionPool != nil {
		// Reuse already created connection pool if possible
		return host.connectionPool, nil
	}

	db, err = createPool(&host.connStr, false)
	if err != nil {
		return nil, err
	}
	host.connectionPool = db
	return db, nil
}
