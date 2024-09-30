package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"math"
	"math/rand"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"time"
)

var action string
var useConfig bool
var noSleep bool

var currentDate = time.Now().Local()

type config struct {
	ApiUrl      string `json:"api_url"`
	DashboardId string `json:"dashboard_id"`
}

var rtoConfig = config{}

func init() {

	flag.BoolVar(&useConfig, "config", false, "Use a configuration file")
	flag.StringVar(&action, "action", "checkin", "Action to perform (checkin, stats or init)")
	flag.StringVar(&rtoConfig.ApiUrl, "api", "", "API Endpoint in the https://rtoapi.example.com/ format")
	flag.StringVar(&rtoConfig.DashboardId, "id", "", "Your Dashboard Id")
	flag.BoolVar(&noSleep, "nosleep", false, "Whether to perform a random sleep before checking in")

	flag.Parse()

	ex, _ := os.Executable()
	pwd := filepath.Dir(ex)
	configPath := filepath.Join(pwd, "rtoconfig.json")

	if action == "init" {
		_, err := os.Open(configPath)

		if err != nil {
			file, _ := os.Create(configPath)
			newConfigJson, _ := json.Marshal(rtoConfig)

			file.Write(newConfigJson)
			file.Close()

			fmt.Println("Config file created successfully and saved to:")
			fmt.Println(configPath)
			fmt.Println("Please fill in your unique dashboard details into this file.")

			os.Exit(0)
		} else {
			panic("Config file already exists")
		}
	}

	if useConfig {
		configFile, err := os.Open(configPath)

		if err != nil {
			panic("Error opening config file")
		}

		configFileBytes, _ := io.ReadAll(configFile)
		json.Unmarshal(configFileBytes, &rtoConfig)
	}

	if rtoConfig.ApiUrl == "" {
		panic("API Endpoint is required")
	}
	if rtoConfig.DashboardId == "" {
		panic("Dashboard Id is required")
	}
}

func checkin(parsedUri *url.URL) {

	if !noSleep {
		r := rand.Intn(60)
		fmt.Println("Sleeping for :", r, "seconds")
		time.Sleep(time.Duration(r) * time.Second)
	}

	fullUrl, _ := url.JoinPath("https://", parsedUri.Host, "/checkin/", rtoConfig.DashboardId)

	fmt.Println("Checkin URL detected to be:", fullUrl)

	req, err := http.NewRequest("POST", fullUrl, nil)
	if err != nil {
		panic(err)
	}

	client := http.Client{
		Timeout: 30 * time.Second,
	}

	res, err := client.Do(req)
	if err != nil {
		panic("client: error making http request: " + err.Error())
	}

	fmt.Println("Checkin was successful with a response code of:", res.Status)
}

type RtoStats struct {
	Attendance float64 `json:"attendance"`
}

func stats(parsedUri *url.URL) {
	fullUrl, _ := url.JoinPath("https://", parsedUri.Host, "/stats/", rtoConfig.DashboardId, "/", currentDate.Format("2006/01"))

	fmt.Println("Stats URL detected to be:", fullUrl)

	req, err := http.NewRequest("GET", fullUrl, nil)
	if err != nil {
		panic(err)
	}

	client := http.Client{
		Timeout: 30 * time.Second,
	}

	res, err := client.Do(req)
	if err != nil {
		panic("client: error making http request: " + err.Error())
	}

	if res.StatusCode >= 200 && res.StatusCode <= 299 {
		fmt.Println("Stats request was successful with a response code of:", res.Status)
		bodyBytes, err := io.ReadAll(res.Body)
		if err != nil {
			log.Fatal(err)
		}
		stats := RtoStats{}
		json.Unmarshal(bodyBytes, &stats)

		fmt.Println("Your attendance is currently at", math.Floor(stats.Attendance), "percent")
	}
}

func main() {

	parsedUri, err := url.ParseRequestURI(rtoConfig.ApiUrl)
	if err != nil {
		panic(err)
	}

	if action == "checkin" {
		checkin(parsedUri)
	} else if action == "stats" {
		stats(parsedUri)
	} else {
		fmt.Println("Invalid action")
	}
}
