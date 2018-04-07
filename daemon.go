package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"
)

func initLogging(config *Config) {
	if config.LogFile == "" {
		return
	}

	f, err := os.OpenFile(config.LogFile, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0644)
	if err != nil {
		log.Fatal("Error opening file: ", err)
	}

	log.SetOutput(f)
}

func handleSignals() {
	sigChannel := make(chan os.Signal)
	signal.Notify(sigChannel,
		syscall.SIGHUP,
		syscall.SIGINT,
		syscall.SIGTERM,
		syscall.SIGQUIT,
	)
	for {
		sig := <-sigChannel
		log.Println("Got signal: ", sig)
		// TODO: handle signals properly
		if sig != syscall.SIGHUP {
			break
		}
	}
}
