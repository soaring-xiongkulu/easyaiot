package k8s

import (
	"encoding/base64"
	"fmt"
	"testing"
)

const basicKubeconfig = `
apiVersion: v1
kind: Config
current-context: dev
contexts:
- name: dev
  context:
    cluster: dev-cluster
    user: dev-user
    namespace: dev-ns
- name: prod
  context:
    cluster: prod-cluster
    user: prod-user
clusters:
- name: dev-cluster
  cluster:
    server: https://dev.example.com:6443
    certificate-authority-data: %s
- name: prod-cluster
  cluster:
    server: https://prod.example.com
    insecure-skip-tls-verify: true
users:
- name: dev-user
  user:
    token: dev-token-xyz
- name: prod-user
  user:
    client-certificate-data: %s
    client-key-data: %s
`

func TestParseBytesBasic(t *testing.T) {
	caData := base64.StdEncoding.EncodeToString([]byte("FAKE-CA"))
	certData := base64.StdEncoding.EncodeToString([]byte("FAKE-CERT"))
	keyData := base64.StdEncoding.EncodeToString([]byte("FAKE-KEY"))
	raw := []byte(fmt.Sprintf(basicKubeconfig, caData, certData, keyData))

	kc, err := ParseBytes(raw)
	if err != nil {
		t.Fatalf("ParseBytes: %v", err)
	}
	if kc.CurrentContext != "dev" {
		t.Errorf("CurrentContext = %q, want dev", kc.CurrentContext)
	}
	if len(kc.Contexts) != 2 {
		t.Errorf("Contexts len = %d, want 2", len(kc.Contexts))
	}
	if kc.Clusters["dev-cluster"].Server != "https://dev.example.com:6443" {
		t.Errorf("dev cluster server wrong: %v", kc.Clusters["dev-cluster"].Server)
	}
	if string(kc.Clusters["dev-cluster"].CertificateAuthorityData) != "FAKE-CA" {
		t.Errorf("dev CA data not decoded: %q", kc.Clusters["dev-cluster"].CertificateAuthorityData)
	}
	if !kc.Clusters["prod-cluster"].InsecureSkipTLSVerify {
		t.Error("prod-cluster should be insecure")
	}
	if kc.Users["dev-user"].Token != "dev-token-xyz" {
		t.Errorf("dev token wrong: %q", kc.Users["dev-user"].Token)
	}
	if string(kc.Users["prod-user"].ClientCertificateData) != "FAKE-CERT" {
		t.Errorf("prod cert wrong")
	}
}

func TestListContexts(t *testing.T) {
	caData := base64.StdEncoding.EncodeToString([]byte("CA"))
	certData := base64.StdEncoding.EncodeToString([]byte("C"))
	keyData := base64.StdEncoding.EncodeToString([]byte("K"))
	raw := []byte(fmt.Sprintf(basicKubeconfig, caData, certData, keyData))
	kc, err := ParseBytes(raw)
	if err != nil {
		t.Fatal(err)
	}
	ctxs := kc.ListContexts()
	if len(ctxs) != 2 {
		t.Fatalf("len = %d", len(ctxs))
	}
	var dev *ContextInfo
	for i := range ctxs {
		if ctxs[i].Name == "dev" {
			dev = &ctxs[i]
		}
	}
	if dev == nil || !dev.Current || dev.Namespace != "dev-ns" {
		t.Errorf("dev context wrong: %+v", dev)
	}
}
