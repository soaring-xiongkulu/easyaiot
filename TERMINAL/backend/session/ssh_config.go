package session

import "golang.org/x/crypto/ssh"

// sshKeyExchanges returns the KEX algorithm list for SSH connections,
// including legacy algorithms for compatibility with older servers.
func sshKeyExchanges() []string {
	return []string{
		"mlkem768x25519-sha256",
		"curve25519-sha256",
		"curve25519-sha256@libssh.org",
		"ecdh-sha2-nistp256",
		"ecdh-sha2-nistp384",
		"ecdh-sha2-nistp521",
		"diffie-hellman-group14-sha256",
		"diffie-hellman-group16-sha512",
		"diffie-hellman-group-exchange-sha256",
		// Legacy algorithms for old servers (issue #208)
		ssh.InsecureKeyExchangeDH14SHA1,
		ssh.InsecureKeyExchangeDHGEXSHA1,
		ssh.InsecureKeyExchangeDH1SHA1,
	}
}

// sshCiphers returns the cipher list, including legacy CBC/3DES ciphers
// for compatibility with old servers (issue #497).
//
// The default order prefers AEAD ciphers. Some old SSH servers advertise GCM
// but close the connection when it is negotiated; callers retry those EOF
// handshakes once with sshAlgorithmsCTRFirst.
func sshCiphers() []string {
	return []string{
		ssh.CipherAES128GCM,
		ssh.CipherAES256GCM,
		ssh.CipherChaCha20Poly1305,
		ssh.CipherAES128CTR,
		ssh.CipherAES192CTR,
		ssh.CipherAES256CTR,
		// Legacy CBC/3DES ciphers for old servers (issue #497)
		ssh.InsecureCipherAES128CBC,
		ssh.InsecureCipherTripleDESCBC,
	}
}

func sshCiphersCTRFirst() []string {
	return []string{
		ssh.CipherAES128CTR,
		ssh.CipherAES192CTR,
		ssh.CipherAES256CTR,
		ssh.CipherChaCha20Poly1305,
		ssh.CipherAES128GCM,
		ssh.CipherAES256GCM,
		ssh.InsecureCipherAES128CBC,
		ssh.InsecureCipherTripleDESCBC,
	}
}

// sshMACs returns the MAC list, including legacy algorithms
// for compatibility with old servers (issue #497).
func sshMACs() []string {
	return []string{
		ssh.HMACSHA256ETM,
		ssh.HMACSHA512ETM,
		ssh.HMACSHA256,
		ssh.HMACSHA512,
		ssh.HMACSHA1,
		ssh.InsecureHMACSHA196,
	}
}

// sshAlgorithms returns the full algorithm configuration for SSH connections.
func sshAlgorithms() ssh.Config {
	return ssh.Config{
		KeyExchanges: sshKeyExchanges(),
		Ciphers:      sshCiphers(),
		MACs:         sshMACs(),
	}
}

func sshAlgorithmsCTRFirst() ssh.Config {
	cfg := sshAlgorithms()
	cfg.Ciphers = sshCiphersCTRFirst()
	return cfg
}
