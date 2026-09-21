package k8s

import (
	"encoding/base64"
	"fmt"

	"gopkg.in/yaml.v3"
)

type ContextInfo struct {
	Name      string `json:"name"`
	Cluster   string `json:"cluster"`
	User      string `json:"user"`
	Namespace string `json:"namespace"`
	Current   bool   `json:"current"`
}

type Kubeconfig struct {
	CurrentContext string
	Contexts       map[string]contextEntry
	Clusters       map[string]clusterEntry
	Users          map[string]userEntry
}

type contextEntry struct {
	Cluster   string
	User      string
	Namespace string
}

type clusterEntry struct {
	Server                   string
	CertificateAuthorityData []byte
	CertificateAuthorityFile string
	InsecureSkipTLSVerify    bool
}

type userEntry struct {
	Token                 string
	ClientCertificateData []byte
	ClientCertificateFile string
	ClientKeyData         []byte
	ClientKeyFile         string
	Exec                  *execConfig
}

type execConfig struct {
	Command    string
	Args       []string
	Env        map[string]string
	APIVersion string
}

// yaml 原始结构 —— 只在解析时使用。
type rawConfig struct {
	CurrentContext string         `yaml:"current-context"`
	Contexts       []namedContext `yaml:"contexts"`
	Clusters       []namedCluster `yaml:"clusters"`
	Users          []namedUser    `yaml:"users"`
}

type namedContext struct {
	Name    string `yaml:"name"`
	Context struct {
		Cluster   string `yaml:"cluster"`
		User      string `yaml:"user"`
		Namespace string `yaml:"namespace"`
	} `yaml:"context"`
}

type namedCluster struct {
	Name    string `yaml:"name"`
	Cluster struct {
		Server                   string `yaml:"server"`
		CertificateAuthorityData string `yaml:"certificate-authority-data"`
		CertificateAuthority     string `yaml:"certificate-authority"`
		InsecureSkipTLSVerify    bool   `yaml:"insecure-skip-tls-verify"`
	} `yaml:"cluster"`
}

type namedUser struct {
	Name string `yaml:"name"`
	User struct {
		Token                 string `yaml:"token"`
		ClientCertificateData string `yaml:"client-certificate-data"`
		ClientCertificate     string `yaml:"client-certificate"`
		ClientKeyData         string `yaml:"client-key-data"`
		ClientKey             string `yaml:"client-key"`
		Exec                  *struct {
			Command    string              `yaml:"command"`
			Args       []string            `yaml:"args"`
			Env        []map[string]string `yaml:"env"`
			APIVersion string              `yaml:"apiVersion"`
		} `yaml:"exec"`
	} `yaml:"user"`
}

func ParseBytes(data []byte) (*Kubeconfig, error) {
	var raw rawConfig
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("kubeconfig yaml: %w", err)
	}
	kc := &Kubeconfig{
		CurrentContext: raw.CurrentContext,
		Contexts:       make(map[string]contextEntry, len(raw.Contexts)),
		Clusters:       make(map[string]clusterEntry, len(raw.Clusters)),
		Users:          make(map[string]userEntry, len(raw.Users)),
	}
	for _, c := range raw.Contexts {
		kc.Contexts[c.Name] = contextEntry{
			Cluster: c.Context.Cluster, User: c.Context.User, Namespace: c.Context.Namespace,
		}
	}
	for _, c := range raw.Clusters {
		ce := clusterEntry{
			Server:                   c.Cluster.Server,
			CertificateAuthorityFile: c.Cluster.CertificateAuthority,
			InsecureSkipTLSVerify:    c.Cluster.InsecureSkipTLSVerify,
		}
		if c.Cluster.CertificateAuthorityData != "" {
			decoded, err := base64.StdEncoding.DecodeString(c.Cluster.CertificateAuthorityData)
			if err != nil {
				return nil, fmt.Errorf("cluster %q CA data: %w", c.Name, err)
			}
			ce.CertificateAuthorityData = decoded
		}
		kc.Clusters[c.Name] = ce
	}
	for _, u := range raw.Users {
		ue := userEntry{
			Token:                 u.User.Token,
			ClientCertificateFile: u.User.ClientCertificate,
			ClientKeyFile:         u.User.ClientKey,
		}
		if u.User.ClientCertificateData != "" {
			decoded, err := base64.StdEncoding.DecodeString(u.User.ClientCertificateData)
			if err != nil {
				return nil, fmt.Errorf("user %q cert data: %w", u.Name, err)
			}
			ue.ClientCertificateData = decoded
		}
		if u.User.ClientKeyData != "" {
			decoded, err := base64.StdEncoding.DecodeString(u.User.ClientKeyData)
			if err != nil {
				return nil, fmt.Errorf("user %q key data: %w", u.Name, err)
			}
			ue.ClientKeyData = decoded
		}
		if u.User.Exec != nil {
			env := make(map[string]string, len(u.User.Exec.Env))
			for _, kv := range u.User.Exec.Env {
				env[kv["name"]] = kv["value"]
			}
			ue.Exec = &execConfig{
				Command: u.User.Exec.Command, Args: u.User.Exec.Args,
				Env: env, APIVersion: u.User.Exec.APIVersion,
			}
		}
		kc.Users[u.Name] = ue
	}
	return kc, nil
}

// ListContexts 返回不含敏感数据的上下文元信息。
func (k *Kubeconfig) ListContexts() []ContextInfo {
	out := make([]ContextInfo, 0, len(k.Contexts))
	for name, c := range k.Contexts {
		out = append(out, ContextInfo{
			Name:      name,
			Cluster:   c.Cluster,
			User:      c.User,
			Namespace: c.Namespace,
			Current:   name == k.CurrentContext,
		})
	}
	return out
}
