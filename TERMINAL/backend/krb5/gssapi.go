/*
MIT License

Copyright (c) 2022-2025 wencaiwulue
Copyright (c) 2026 windtear

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

// Package krb5 implements the client side of the Kerberos GSSAPI exchange
// required by SSH's gssapi-with-mic authentication method.
package krb5

import (
	"encoding/binary"
	"fmt"
	"strings"
	"time"

	"github.com/jcmturner/gokrb5/v8/client"
	"github.com/jcmturner/gokrb5/v8/config"
	"github.com/jcmturner/gokrb5/v8/credentials"
	"github.com/jcmturner/gokrb5/v8/crypto"
	"github.com/jcmturner/gokrb5/v8/gssapi"
	"github.com/jcmturner/gokrb5/v8/iana/chksumtype"
	"github.com/jcmturner/gokrb5/v8/iana/flags"
	"github.com/jcmturner/gokrb5/v8/iana/keyusage"
	"github.com/jcmturner/gokrb5/v8/messages"
	"github.com/jcmturner/gokrb5/v8/spnego"
	"github.com/jcmturner/gokrb5/v8/types"
)

type clientState int

const (
	contextFlagReady             = 128
	initiatorStart   clientState = iota
	initiatorWaitForMutual
	initiatorReady
)

// InitiatorClient adapts gokrb5 to golang.org/x/crypto/ssh.GSSAPIClient.
type InitiatorClient struct {
	state          clientState
	client         *client.Client
	sessionKey     types.EncryptionKey
	subkey         types.EncryptionKey
	authTime       time.Time
	authUsec       int
	acceptorSubkey bool
}

func servicePrincipal(target string) string {
	return strings.Replace(target, "@", "/", 1)
}

// NewInitiatorClientWithCache loads an existing Kerberos credential cache.
// The caller is expected to have obtained a TGT already (for example via kinit).
func NewInitiatorClientWithCache(configFile, cacheFile string) (*InitiatorClient, error) {
	cfg, err := config.Load(configFile)
	if err != nil {
		return nil, fmt.Errorf("load Kerberos config: %w", err)
	}
	cache, err := credentials.LoadCCache(cacheFile)
	if err != nil {
		return nil, fmt.Errorf("load Kerberos credential cache: %w", err)
	}
	cl, err := client.NewFromCCache(cache, cfg)
	if err != nil {
		return nil, fmt.Errorf("create Kerberos client: %w", err)
	}
	if err := cl.Login(); err != nil {
		cl.Destroy()
		return nil, fmt.Errorf("Kerberos login: %w", err)
	}
	if err := cl.AffirmLogin(); err != nil {
		cl.Destroy()
		return nil, fmt.Errorf("validate Kerberos login: %w", err)
	}
	return &InitiatorClient{client: cl, state: initiatorStart}, nil
}

func authenticatorChecksum(gssFlags []int) []byte {
	checksum := make([]byte, 24)
	binary.LittleEndian.PutUint32(checksum[:4], 16)
	for _, flag := range gssFlags {
		if flag == gssapi.ContextFlagDeleg {
			checksum = append(checksum, make([]byte, 28-len(checksum))...)
		}
		value := binary.LittleEndian.Uint32(checksum[20:24])
		binary.LittleEndian.PutUint32(checksum[20:24], value|uint32(flag))
	}
	return checksum
}

// InitSecContext implements ssh.GSSAPIClient.
func (k *InitiatorClient) InitSecContext(target string, token []byte, delegate bool) ([]byte, bool, error) {
	gssFlags := []int{contextFlagReady, gssapi.ContextFlagInteg, gssapi.ContextFlagMutual}
	if delegate {
		gssFlags = append(gssFlags, gssapi.ContextFlagDeleg)
	}
	apOptions := []int{flags.APOptionMutualRequired}

	switch k.state {
	case initiatorStart:
		// crypto/ssh passes host@target. Replace only that separator so an
		// explicit realm in target (host@IP@REALM) becomes host/IP@REALM.
		ticket, sessionKey, err := k.client.GetServiceTicket(servicePrincipal(target))
		if err != nil {
			return nil, false, err
		}
		krbToken, err := spnego.NewKRB5TokenAPREQ(k.client, ticket, sessionKey, gssFlags, apOptions)
		if err != nil {
			return nil, false, fmt.Errorf("generate Kerberos token: %w", err)
		}
		creds := k.client.Credentials
		auth, err := types.NewAuthenticator(creds.Domain(), creds.CName())
		if err != nil {
			return nil, false, fmt.Errorf("generate Kerberos authenticator: %w", err)
		}
		auth.Cksum = types.Checksum{CksumType: chksumtype.GSSAPI, Checksum: authenticatorChecksum(gssFlags)}
		etype, err := crypto.GetEtype(sessionKey.KeyType)
		if err != nil {
			return nil, false, err
		}
		if err := auth.GenerateSeqNumberAndSubKey(sessionKey.KeyType, etype.GetKeyByteSize()); err != nil {
			return nil, false, err
		}
		k.subkey = auth.SubKey
		k.sessionKey = sessionKey
		k.authTime = auth.CTime
		k.authUsec = auth.Cusec
		apReq, err := messages.NewAPReq(ticket, sessionKey, auth)
		if err != nil {
			return nil, false, fmt.Errorf("generate Kerberos AP request: %w", err)
		}
		for _, option := range apOptions {
			types.SetFlag(&apReq.APOptions, option)
		}
		krbToken.APReq = apReq
		out, err := krbToken.Marshal()
		if err != nil {
			return nil, false, err
		}
		k.state = initiatorWaitForMutual
		return out, true, nil

	case initiatorWaitForMutual:
		var krbToken spnego.KRB5Token
		if err := krbToken.Unmarshal(token); err != nil {
			return nil, false, fmt.Errorf("unmarshal Kerberos AP reply: %w", err)
		}
		if !krbToken.IsAPRep() {
			return nil, false, fmt.Errorf("Kerberos mutual authentication returned a non-AP-REP token")
		}
		contextKey, acceptorSubkey, err := verifyAPReply(krbToken.APRep, k.sessionKey, k.subkey, k.authTime, k.authUsec)
		if err != nil {
			return nil, false, err
		}
		k.subkey = contextKey
		k.acceptorSubkey = acceptorSubkey
		k.state = initiatorReady
		return nil, false, nil

	default:
		return nil, false, fmt.Errorf("Kerberos security context is already initialized")
	}
}

// GetMIC implements ssh.GSSAPIClient.
func (k *InitiatorClient) GetMIC(field []byte) ([]byte, error) {
	if !k.acceptorSubkey {
		mic, err := gssapi.NewInitiatorMICToken(field, k.subkey)
		if err != nil {
			return nil, err
		}
		return mic.Marshal()
	}
	mic := &gssapi.MICToken{
		Flags:   gssapi.MICTokenFlagAcceptorSubkey,
		Payload: field,
	}
	if err := mic.SetChecksum(k.subkey, keyusage.GSSAPI_INITIATOR_SIGN); err != nil {
		return nil, err
	}
	return mic.Marshal()
}

func verifyAPReply(apRep messages.APRep, ticketKey, initiatorSubkey types.EncryptionKey, authTime time.Time, authUsec int) (types.EncryptionKey, bool, error) {
	plain, err := crypto.DecryptEncPart(apRep.EncPart, ticketKey, keyusage.AP_REP_ENCPART)
	if err != nil {
		return types.EncryptionKey{}, false, fmt.Errorf("decrypt Kerberos AP reply: %w", err)
	}
	var reply messages.EncAPRepPart
	if err := reply.Unmarshal(plain); err != nil {
		return types.EncryptionKey{}, false, fmt.Errorf("unmarshal encrypted Kerberos AP reply: %w", err)
	}
	// KerberosTime is encoded with second precision; Cusec carries the
	// microsecond component separately.
	if reply.CTime.Unix() != authTime.Unix() || reply.Cusec != authUsec {
		return types.EncryptionKey{}, false, fmt.Errorf("Kerberos AP reply does not match the client authenticator")
	}
	if len(reply.Subkey.KeyValue) > 0 {
		return reply.Subkey, true, nil
	}
	return initiatorSubkey, false, nil
}

// DeleteSecContext implements ssh.GSSAPIClient.
func (k *InitiatorClient) DeleteSecContext() error {
	if k.client != nil {
		k.client.Destroy()
		k.client = nil
	}
	return nil
}
