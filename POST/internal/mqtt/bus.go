package mqttbus

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"strings"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"

	"easyaiot/post/internal/config"
	"easyaiot/post/internal/metrics"
)

// Bus wraps MQTT client for subscribe/publish.
type Bus struct {
	cfg    config.Config
	client mqtt.Client
	mu     sync.Mutex
}

func New(cfg config.Config) *Bus {
	return &Bus{cfg: cfg}
}

func (b *Bus) Connect() error {
	opts := mqtt.NewClientOptions()
	broker := b.cfg.MQTTBroker
	if !strings.Contains(broker, "://") {
		broker = "tcp://" + broker
	}
	opts.AddBroker(broker)
	opts.SetClientID(b.cfg.InstanceID)
	if b.cfg.MQTTUsername != "" {
		opts.SetUsername(b.cfg.MQTTUsername)
		opts.SetPassword(b.cfg.MQTTPassword)
	}
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(3 * time.Second)
	opts.SetKeepAlive(30 * time.Second)
	opts.SetOrderMatters(false)

	b.client = mqtt.NewClient(opts)
	token := b.client.Connect()
	if !token.WaitTimeout(15 * time.Second) {
		return fmt.Errorf("mqtt connect timeout broker=%s (set MQTT_BROKER, local default tcp://127.0.0.1:1883)", broker)
	}
	if err := token.Error(); err != nil {
		return err
	}
	slog.Info("mqtt_connected", "broker", broker, "client_id", b.cfg.InstanceID)
	return nil
}

func (b *Bus) Connected() bool {
	return b.client != nil && b.client.IsConnected()
}

func (b *Bus) Close() {
	if b.client != nil && b.client.IsConnected() {
		b.client.Disconnect(250)
	}
}

func (b *Bus) ShareTopic(topic string) string {
	return fmt.Sprintf("$share/%s/%s", b.cfg.MQTTShareGroup, topic)
}

func (b *Bus) Subscribe(topic string, qos byte, handler mqtt.MessageHandler) error {
	token := b.client.Subscribe(topic, qos, handler)
	token.Wait()
	return token.Error()
}

func (b *Bus) Publish(topic string, qos byte, payload any) error {
	var data []byte
	var err error
	switch v := payload.(type) {
	case []byte:
		data = v
	case string:
		data = []byte(v)
	default:
		data, err = json.Marshal(v)
		if err != nil {
			return err
		}
	}
	token := b.client.Publish(topic, qos, false, data)
	ok := token.WaitTimeout(5 * time.Second)
	if !ok {
		metrics.MQTTPublishError.WithLabelValues(topic).Inc()
		return fmt.Errorf("publish timeout topic=%s", topic)
	}
	if err := token.Error(); err != nil {
		metrics.MQTTPublishError.WithLabelValues(topic).Inc()
		return err
	}
	return nil
}

func (b *Bus) PublishJSON(topic string, qos byte, v any) error {
	return b.Publish(topic, qos, v)
}
