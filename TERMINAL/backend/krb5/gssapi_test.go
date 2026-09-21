package krb5

import (
	"testing"
	"time"

	"github.com/jcmturner/gofork/encoding/asn1"
	"github.com/jcmturner/gokrb5/v8/asn1tools"
	"github.com/jcmturner/gokrb5/v8/crypto"
	"github.com/jcmturner/gokrb5/v8/gssapi"
	"github.com/jcmturner/gokrb5/v8/iana/asnAppTag"
	"github.com/jcmturner/gokrb5/v8/iana/etypeID"
	"github.com/jcmturner/gokrb5/v8/iana/keyusage"
	"github.com/jcmturner/gokrb5/v8/messages"
	"github.com/jcmturner/gokrb5/v8/types"
)

func TestServicePrincipal(t *testing.T) {
	tests := []struct {
		target string
		want   string
	}{
		{"host@server.example.com", "host/server.example.com"},
		{"host@192.0.2.10@EXAMPLE.COM", "host/192.0.2.10@EXAMPLE.COM"},
		{"host@2001:db8::10@EXAMPLE.COM", "host/2001:db8::10@EXAMPLE.COM"},
	}
	for _, tt := range tests {
		if got := servicePrincipal(tt.target); got != tt.want {
			t.Errorf("servicePrincipal(%q) = %q, want %q", tt.target, got, tt.want)
		}
	}
}

func TestVerifyAPReply(t *testing.T) {
	ticketKey := types.EncryptionKey{KeyType: etypeID.AES256_CTS_HMAC_SHA1_96, KeyValue: []byte("0123456789abcdef0123456789abcdef")}
	initiatorSubkey := types.EncryptionKey{KeyType: etypeID.AES256_CTS_HMAC_SHA1_96, KeyValue: []byte("abcdef0123456789abcdef0123456789")}
	acceptorSubkey := types.EncryptionKey{KeyType: etypeID.AES128_CTS_HMAC_SHA1_96, KeyValue: []byte("0123456789abcdef")}
	authTime := time.Date(2026, time.September, 9, 1, 2, 3, 456789000, time.UTC)

	makeReply := func(t *testing.T, ctime time.Time, cusec int, subkey types.EncryptionKey) messages.APRep {
		t.Helper()
		plain, err := asn1.Marshal(messages.EncAPRepPart{CTime: ctime, Cusec: cusec, Subkey: subkey})
		if err != nil {
			t.Fatal(err)
		}
		plain = asn1tools.AddASNAppTag(plain, asnAppTag.EncAPRepPart)
		enc, err := crypto.GetEncryptedData(plain, ticketKey, keyusage.AP_REP_ENCPART, 0)
		if err != nil {
			t.Fatal(err)
		}
		return messages.APRep{EncPart: enc}
	}

	reply := makeReply(t, authTime.Truncate(time.Second), 456789, acceptorSubkey)
	got, usedAcceptorSubkey, err := verifyAPReply(reply, ticketKey, initiatorSubkey, authTime, 456789)
	if err != nil {
		t.Fatalf("verifyAPReply() error = %v", err)
	}
	if !usedAcceptorSubkey || string(got.KeyValue) != string(acceptorSubkey.KeyValue) {
		t.Fatalf("verifyAPReply() did not select acceptor subkey")
	}
	withoutSubkey := makeReply(t, authTime.Truncate(time.Second), 456789, types.EncryptionKey{})
	got, usedAcceptorSubkey, err = verifyAPReply(withoutSubkey, ticketKey, initiatorSubkey, authTime, 456789)
	if err != nil {
		t.Fatalf("verifyAPReply() without acceptor subkey error = %v", err)
	}
	if usedAcceptorSubkey || string(got.KeyValue) != string(initiatorSubkey.KeyValue) {
		t.Fatalf("verifyAPReply() did not retain initiator subkey")
	}

	wrongTime := makeReply(t, authTime.Add(time.Second), 456789, acceptorSubkey)
	if _, _, err := verifyAPReply(wrongTime, ticketKey, initiatorSubkey, authTime, 456789); err == nil {
		t.Fatal("verifyAPReply() accepted a mismatched authenticator timestamp")
	}

	tampered := reply
	tampered.EncPart.Cipher = append([]byte(nil), reply.EncPart.Cipher...)
	tampered.EncPart.Cipher[len(tampered.EncPart.Cipher)-1] ^= 1
	if _, _, err := verifyAPReply(tampered, ticketKey, initiatorSubkey, authTime, 456789); err == nil {
		t.Fatal("verifyAPReply() accepted a tampered encrypted reply")
	}
}

func TestGetMICMarksAcceptorSubkey(t *testing.T) {
	key := types.EncryptionKey{KeyType: etypeID.AES256_CTS_HMAC_SHA1_96, KeyValue: []byte("0123456789abcdef0123456789abcdef")}
	client := &InitiatorClient{subkey: key, acceptorSubkey: true}
	payload := []byte("ssh authentication request")
	encoded, err := client.GetMIC(payload)
	if err != nil {
		t.Fatal(err)
	}
	var mic gssapi.MICToken
	if err := mic.Unmarshal(encoded, false); err != nil {
		t.Fatal(err)
	}
	if mic.Flags&gssapi.MICTokenFlagAcceptorSubkey == 0 {
		t.Fatal("MIC token does not mark use of the acceptor subkey")
	}
	mic.Payload = payload
	if ok, err := mic.Verify(key, keyusage.GSSAPI_INITIATOR_SIGN); err != nil || !ok {
		t.Fatalf("MIC verification failed: ok=%v err=%v", ok, err)
	}
}
