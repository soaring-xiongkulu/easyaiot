package session

import "fmt"

// Identity 是一个可复用的登录凭证，存于 identities.json。
type Identity struct {
	ID       string `json:"id"`
	Name     string `json:"name"`
	Username string `json:"username"`
	AuthType   string `json:"authType"`           // "password" | "key" | "keyText"
	Password   string `json:"password,omitempty"` // 解密后的密码 / key passphrase
	KeyPath    string `json:"keyPath,omitempty"`  // key 类型：私钥文件路径
	KeyContent string `json:"keyContent,omitempty"` // keyText 类型：私钥文本内容（PEM）
}

// IdentityStoreData 是 identities.json 的顶层结构。
type IdentityStoreData struct {
	Identities []Identity `json:"identities"`
}

// IdentityResolver 由 App 从 identity store 提供，返回解密后的身份。
type IdentityResolver func(id string) (Identity, bool)

// MaterializeIdentity 把「引用身份」的连接物化为普通 password/key 配置：
// 覆盖用户名、解密凭据。非 identity 连接原样返回。
func MaterializeIdentity(config ConnectionConfig, resolve IdentityResolver) (ConnectionConfig, error) {
	if config.AuthType != "identity" {
		return config, nil
	}
	id, ok := resolve(config.IdentityId)
	if !ok {
		return config, fmt.Errorf("referenced identity not found: %s", config.IdentityId)
	}
	config.User = id.Username
	switch id.AuthType {
	case "password":
		config.AuthType = "password"
		config.Password = id.Password
	case "key":
		config.AuthType = "key"
		config.KeyPath = id.KeyPath
		config.Password = id.Password // passphrase
	case "keyText":
		config.AuthType = "keyText"
		config.KeyContent = id.KeyContent
		config.Password = id.Password // passphrase
	default:
		return config, fmt.Errorf("identity %q has unknown authType %q", id.ID, id.AuthType)
	}
	return config, nil
}
