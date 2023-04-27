package main

import (
	"log"
	"net/http"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{}

type server struct {
	connections map[uuid.UUID]*(websocket.Conn)
}

func (s *server) createRoom() {
	
}

func main() {
	homeResp := []byte("Hey there!")
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write(homeResp)
	})

	log.Fatal(http.ListenAndServe("localhost:8080", nil))
}