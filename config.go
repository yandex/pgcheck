package main

import (
	"log"

	"github.com/spf13/viper"
)

//
// We declare all types here and all fields in them exportable
// so that viper module could unmarshal to them
//

// Config is (surprise) for storing configuration
type Config struct {
	LogFile   string `mapstructure:"log_file"`
	DC        string `mapstructure:"my_dc"`
	Timeout   int    `mapstructure:"iteration_timeout"`
	Databases map[string]DBConfig
}

// DBConfig stores config of a single DB
type DBConfig struct {
	LocalConnString  string `mapstructure:"local_conn_string"`
	AppendConnString string `mapstructure:"append_conn_string"`
	Quorum           uint
	Hysterisis       uint
}

func parseConfig() Config {
	viper.SetConfigName("pgcheck")
	viper.SetConfigType("yaml")
	viper.AddConfigPath("/etc/")
	err := viper.ReadInConfig()
	if err != nil {
		log.Fatal(err)
	}

	var config Config
	err = viper.Unmarshal(&config)
	if err != nil {
		log.Fatal(err)
	}
	return config
}
