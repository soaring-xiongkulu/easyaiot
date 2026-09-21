package session

// ProbeConnection tests whether a connection config can actually connect /
// authenticate, WITHOUT opening a persistent session. It powers the frontend's
// "Test connection" button (issue #377): the App.TestConnection Wails method
// first materializes identity/proxy references (which requires the store), then
// dispatches session-owned protocols to this function.
//
// Return values: on success a short human-readable description; on failure a
// readable error that must NOT echo the password (Protocol errors are wrapped
// as-is so drivers do the talking, but we never interpolate config.Password).

import (
	"context"
	"crypto/tls"
	"fmt"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/jlaffaye/ftp"
	"github.com/pkg/sftp"
	"github.com/redis/go-redis/v9"
	"github.com/rhnvrm/simples3"
	"github.com/studio-b12/gowebdav"
	"golang.org/x/crypto/ssh"

	"github.com/cloudsoda/go-smb2"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"easyaiot/terminal/backend/database"
)

// ProbeConnection dispatches a connectivity probe by config.Type.
// Types owned by the App dispatcher (k8s / container) are not handled here.
func ProbeConnection(config ConnectionConfig) (string, error) {
	switch config.Type {
	case "ssh":
		return probeSSH(config)
	case "telnet":
		return probeTelnet(config)
	case "tcp":
		return probeTCP(config)
	case "ftp":
		return probeFTP(config)
	case "sftp":
		return probeSFTP(config)
	case "scp":
		return probeSCP(config)
	case "s3":
		return probeS3(config)
	case "webdav":
		return probeWebDAV(config)
	case "smb":
		return probeSMB(config)
	case "redis":
		return probeRedis(config)
	case "mongodb":
		return probeMongo(config)
	case "elasticsearch":
		return probeElasticsearch(config)
	case "database":
		// redis/mongodb/elasticsearch are stored as type "database" with a
		// dbType discriminator (mirroring the SQL family). Route them to their
		// dedicated probes; the rest go through the SQL provider registry.
		switch config.DBType {
		case "redis":
			return probeRedis(config)
		case "mongodb":
			return probeMongo(config)
		case "elasticsearch":
			return probeElasticsearch(config)
		}
		return probeDatabase(config)
	default:
		return "", fmt.Errorf("connection type %q does not support connection testing", config.Type)
	}
}

func probeSSH(config ConnectionConfig) (string, error) {
	// Non-interactive: keyboard-interactive challenges are rejected so a test
	// can never block waiting for typed input in a modal dialog.
	kb := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, fmt.Errorf("interactive auth not allowed during connection test")
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{User: config.User, Auth: authMethods, Timeout: 15 * time.Second, HostKeyCallback: ssh.InsecureIgnoreHostKey()}, cleanup, nil
		}
	}
	// Honor a materialized proxy (set by App.materializeProxy) on the first hop,
	// mirroring the terminal session's dial path.
	var keyboardConfig sshClientConfigFactory
	if config.AuthType != "kerberos" {
		keyboardConfig = newConfig(kb)
	}
	client, err := dialSSHWithAuthRetry(addr, newConfig(nil), keyboardConfig, func() (net.Conn, error) {
		return dialFirstHop(addr, config.Proxy)
	})
	if err != nil {
		return "", fmt.Errorf("ssh: %w", err)
	}
	defer client.Close()
	return fmt.Sprintf("ssh: connected as %s@%s:%d", config.User, config.Host, config.Port), nil
}

// probeSFTP verifies SSH connectivity AND completes the SFTP subsystem
// handshake, so a failed test reports hosts where the subsystem is disabled
// (those hosts should use an SCP connection instead).
func probeSFTP(config ConnectionConfig) (string, error) {
	kb := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, fmt.Errorf("interactive auth not allowed during connection test")
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{User: config.User, Auth: authMethods, Timeout: 15 * time.Second, HostKeyCallback: ssh.InsecureIgnoreHostKey()}, cleanup, nil
		}
	}
	var keyboardConfig sshClientConfigFactory
	if config.AuthType != "kerberos" {
		keyboardConfig = newConfig(kb)
	}
	client, err := dialSSHWithAuthRetry(addr, newConfig(nil), keyboardConfig, func() (net.Conn, error) {
		return dialFirstHop(addr, config.Proxy)
	})
	if err != nil {
		return "", fmt.Errorf("sftp: %w", err)
	}
	defer client.Close()
	sc, err := sftp.NewClient(client)
	if err != nil {
		return "", fmt.Errorf("sftp: %w", err)
	}
	_ = sc.Close()
	return fmt.Sprintf("sftp: connected as %s@%s:%d", config.User, config.Host, config.Port), nil
}

// probeSCP verifies SSH connectivity AND that the exec channel (which the SCP
// transfer engine drives) is usable — a plain shell command round-trip.
func probeSCP(config ConnectionConfig) (string, error) {
	kb := func(user, instruction string, questions []string, echos []bool) ([]string, error) {
		return nil, fmt.Errorf("interactive auth not allowed during connection test")
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	newConfig := func(challenge ssh.KeyboardInteractiveChallenge) sshClientConfigFactory {
		return func() (*ssh.ClientConfig, func(), error) {
			authMethods, cleanup, err := makeSSHAuthMethodsForAttempt(config, challenge)
			if err != nil {
				return nil, nil, err
			}
			return &ssh.ClientConfig{User: config.User, Auth: authMethods, Timeout: 15 * time.Second, HostKeyCallback: ssh.InsecureIgnoreHostKey()}, cleanup, nil
		}
	}
	var keyboardConfig sshClientConfigFactory
	if config.AuthType != "kerberos" {
		keyboardConfig = newConfig(kb)
	}
	client, err := dialSSHWithAuthRetry(addr, newConfig(nil), keyboardConfig, func() (net.Conn, error) {
		return dialFirstHop(addr, config.Proxy)
	})
	if err != nil {
		return "", fmt.Errorf("scp: %w", err)
	}
	defer client.Close()
	sess, err := client.NewSession()
	if err != nil {
		return "", fmt.Errorf("scp: exec channel: %w", err)
	}
	defer sess.Close()
	if _, err := sess.Output("pwd"); err != nil {
		return "", fmt.Errorf("scp: exec channel: %w", err)
	}
	return fmt.Sprintf("scp: connected as %s@%s:%d", config.User, config.Host, config.Port), nil
}

func probeTelnet(config ConnectionConfig) (string, error) {
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	conn, err := net.DialTimeout("tcp", addr, 15*time.Second)
	if err != nil {
		return "", fmt.Errorf("telnet: %w", err)
	}
	conn.Close()
	return fmt.Sprintf("telnet: %s:%d reachable", config.Host, config.Port), nil
}

// probeTCP checks that a plain TCP socket to host:port can be established.
func probeTCP(config ConnectionConfig) (string, error) {
	addr := net.JoinHostPort(config.Host, strconv.Itoa(config.Port))
	conn, err := net.DialTimeout("tcp", addr, 15*time.Second)
	if err != nil {
		return "", fmt.Errorf("tcp: %w", err)
	}
	conn.Close()
	return fmt.Sprintf("tcp: %s:%d reachable", config.Host, config.Port), nil
}

func probeFTP(config ConnectionConfig) (string, error) {
	addr := fmt.Sprintf("%s:%d", config.Host, config.Port)
	if config.Port <= 0 {
		addr = fmt.Sprintf("%s:21", config.Host)
	}
	encryption := config.FtpEncryption
	if encryption == "" {
		encryption = "none"
	}
	tlsConfig := &tls.Config{InsecureSkipVerify: config.FtpSkipVerify}

	var conn *ftp.ServerConn
	var err error
	switch encryption {
	case "required":
		conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second), ftp.DialWithExplicitTLS(tlsConfig))
	case "auto":
		conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second), ftp.DialWithExplicitTLS(tlsConfig))
		if err != nil {
			conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second))
		}
	default:
		conn, err = ftp.Dial(addr, ftp.DialWithTimeout(30*time.Second))
	}
	if err != nil {
		return "", fmt.Errorf("ftp: %w", err)
	}
	defer conn.Quit()
	if err := conn.Login(config.User, config.Password); err != nil {
		return "", fmt.Errorf("ftp login: %w", err)
	}
	return fmt.Sprintf("ftp: logged in as %s@%s", config.User, config.Host), nil
}

func probeS3(config ConnectionConfig) (string, error) {
	c := simples3.New(config.S3Region, config.User, config.Password)
	c.Endpoint = strings.TrimSuffix(config.Host, "/")
	if config.S3URLStyle != "path" {
		c.SetVirtualHostedStyle(true)
	}
	// ListBuckets is the lightest probe that validates endpoint reachability AND
	// access-key validity.
	if _, err := c.ListBuckets(simples3.ListBucketsInput{}); err != nil {
		return "", fmt.Errorf("s3: %w", err)
	}
	return fmt.Sprintf("s3: credentials valid for %s", config.Host), nil
}

func probeWebDAV(config ConnectionConfig) (string, error) {
	url := strings.TrimSuffix(config.Host, "/")
	client := gowebdav.NewClient(url, config.User, config.Password)
	if err := client.Connect(); err != nil {
		return "", fmt.Errorf("webdav: %w", err)
	}
	return fmt.Sprintf("webdav: connected to %s", url), nil
}

func probeSMB(config ConnectionConfig) (string, error) {
	port := config.Port
	if port <= 0 {
		port = 445
	}
	addr := net.JoinHostPort(config.Host, strconv.Itoa(port))
	conn, err := net.DialTimeout("tcp", addr, 15*time.Second)
	if err != nil {
		return "", fmt.Errorf("smb dial: %w", err)
	}
	d := &smb2.Dialer{
		Initiator: &smb2.NTLMInitiator{
			User:     config.User,
			Password: config.Password,
			Domain:   config.SmbDomain,
		},
	}
	sess, err := d.DialConn(context.Background(), conn, addr)
	if err != nil {
		conn.Close()
		return "", fmt.Errorf("smb handshake: %w", err)
	}
	defer func() {
		_ = sess.Logoff()
		conn.Close()
	}()
	return fmt.Sprintf("smb: authenticated as %s@%s", config.User, config.Host), nil
}

func probeRedis(config ConnectionConfig) (string, error) {
	var client *redis.Client
	if config.RedisMode == "sentinel" {
		var addrs []string
		for _, a := range strings.Split(config.RedisSentinels, ",") {
			if a = strings.TrimSpace(a); a != "" {
				addrs = append(addrs, a)
			}
		}
		if len(addrs) == 0 {
			return "", fmt.Errorf("redis sentinel: no sentinel addresses")
		}
		if config.RedisMasterName == "" {
			return "", fmt.Errorf("redis sentinel: master name required")
		}
		client = redis.NewFailoverClient(&redis.FailoverOptions{
			MasterName:       config.RedisMasterName,
			SentinelAddrs:    addrs,
			SentinelUsername: config.SentinelUser,
			SentinelPassword: config.SentinelPassword,
			Username:         config.User,
			Password:         config.Password,
			DB:               0,
		})
	} else {
		client = redis.NewClient(&redis.Options{
			Addr:     fmt.Sprintf("%s:%d", config.Host, config.Port),
			Username: config.User,
			Password: config.Password,
			DB:       0,
		})
	}
	defer client.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if _, err := client.Ping(ctx).Result(); err != nil {
		return "", fmt.Errorf("redis ping: %w", err)
	}
	return fmt.Sprintf("redis: connected to %s", probeRedisAddr(config)), nil
}

// probeRedisAddr describes the probe target: sentinel connections report the
// master name (the actual master can change), standalone reports host:port.
func probeRedisAddr(config ConnectionConfig) string {
	if config.RedisMode == "sentinel" {
		return "sentinel master " + config.RedisMasterName
	}
	return fmt.Sprintf("%s:%d", config.Host, config.Port)
}

func probeMongo(config ConnectionConfig) (string, error) {
	uri := buildMongoURI(config)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		return "", fmt.Errorf("mongodb connect: %w", err)
	}
	defer client.Disconnect(context.Background())
	if err := client.Ping(ctx, nil); err != nil {
		return "", fmt.Errorf("mongodb ping: %w", err)
	}
	return fmt.Sprintf("mongodb: connected to %s:%d", config.Host, config.Port), nil
}

// probeElasticsearch probes the cluster with GET / using the same URL, TLS and
// auth construction as ElasticsearchSession.Connect (basic and ApiKey auth).
func probeElasticsearch(config ConnectionConfig) (string, error) {
	host := config.Host
	if host == "" {
		host = "127.0.0.1"
	}
	port := config.Port
	if port == 0 {
		port = 9200
	}
	scheme := "http"
	if config.EsUseSSL {
		scheme = "https"
	}
	prefix := strings.TrimSuffix(config.EsPathPrefix, "/")
	if prefix != "" && !strings.HasPrefix(prefix, "/") {
		prefix = "/" + prefix
	}

	transport := &http.Transport{
		Proxy: http.ProxyFromEnvironment,
		DialContext: (&net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		TLSHandshakeTimeout: 10 * time.Second,
	}
	if config.EsUseSSL {
		transport.TLSClientConfig = &tls.Config{
			InsecureSkipVerify: config.EsSkipVerify, //nolint:gosec // intentional user opt-in
		}
	}
	client := &http.Client{
		Timeout:   15 * time.Second,
		Transport: transport,
	}

	req, err := http.NewRequest(http.MethodGet, fmt.Sprintf("%s://%s:%d%s", scheme, host, port, prefix), nil)
	if err != nil {
		return "", fmt.Errorf("elasticsearch connect: %w", err)
	}
	if auth := buildEsAuthHeader(config); auth != "" {
		req.Header.Set("Authorization", auth)
	}
	req.Header.Set("Accept", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("elasticsearch connect: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("elasticsearch connect: HTTP %s", resp.Status)
	}
	return fmt.Sprintf("elasticsearch: connected to %s:%d", host, port), nil
}

func probeDatabase(config ConnectionConfig) (string, error) {
	dsn, err := database.BuildDSN(config.DBType, config.Host, config.User, config.Password, config.DBName, config.DBParams, config.Port)
	if err != nil {
		return "", err
	}
	db, err := database.NewDB(config.DBType, dsn)
	if err != nil {
		return "", err
	}
	defer db.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		return "", fmt.Errorf("ping %s: %w", config.DBType, err)
	}
	return fmt.Sprintf("%s: connected to %s:%d", config.DBType, config.Host, config.Port), nil
}
