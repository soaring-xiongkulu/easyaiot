package main
import (
 "os"
 "os/signal"
 mqtt "github.com/mochi-mqtt/server/v2"
 "github.com/mochi-mqtt/server/v2/hooks/auth"
 "github.com/mochi-mqtt/server/v2/listeners"
)
func main(){s:=mqtt.New(nil);if err:=s.AddHook(new(auth.AllowHook),nil);err!=nil{panic(err)};if err:=s.AddListener(listeners.NewTCP(listeners.Config{ID:"regression",Address:"127.0.0.1:18883"}));err!=nil{panic(err)};if err:=s.Serve();err!=nil{panic(err)};ch:=make(chan os.Signal,1);signal.Notify(ch,os.Interrupt);<-ch;s.Close()}
