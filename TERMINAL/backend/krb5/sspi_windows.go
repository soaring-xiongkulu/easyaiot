//go:build windows

package krb5

import (
	"fmt"

	"github.com/alexbrainman/sspi"
	"github.com/alexbrainman/sspi/kerberos"
)

// SSPIInitiatorClient adapts the Windows Kerberos security package to the
// ssh.GSSAPIClient interface. AcquireCurrentUserCredentials uses the current
// Windows logon session's LSA ticket cache (the MSLSA: cache).
type SSPIInitiatorClient struct {
	creds *sspi.Credentials
	ctx   *kerberos.ClientContext
}

func NewSSPIInitiatorClient() (*SSPIInitiatorClient, error) {
	creds, err := kerberos.AcquireCurrentUserCredentials()
	if err != nil {
		return nil, fmt.Errorf("acquire current Windows Kerberos credentials: %w", err)
	}
	return &SSPIInitiatorClient{creds: creds}, nil
}

func (c *SSPIInitiatorClient) InitSecContext(target string, token []byte, delegate bool) ([]byte, bool, error) {
	if c.creds == nil {
		return nil, false, fmt.Errorf("Windows Kerberos credentials are closed")
	}
	if c.ctx == nil {
		flags := uint32(sspi.ISC_REQ_MUTUAL_AUTH | sspi.ISC_REQ_CONNECTION | sspi.ISC_REQ_INTEGRITY)
		if delegate {
			flags |= sspi.ISC_REQ_DELEGATE
		}
		ctx, complete, output, err := kerberos.NewClientContextWithFlags(
			c.creds, servicePrincipal(target), flags,
		)
		if err != nil {
			return nil, false, fmt.Errorf("initialize Windows Kerberos context (verify the current logon session has a valid ticket with klist): %w", err)
		}
		c.ctx = ctx
		return output, !complete, nil
	}

	complete, output, err := c.ctx.Update(token)
	if err != nil {
		return nil, false, fmt.Errorf("continue Windows Kerberos context: %w", err)
	}
	return output, !complete, nil
}

func (c *SSPIInitiatorClient) GetMIC(field []byte) ([]byte, error) {
	if c.ctx == nil {
		return nil, fmt.Errorf("Windows Kerberos context is not initialized")
	}
	token, err := c.ctx.MakeSignature(field, 0, 0)
	if err != nil {
		return nil, fmt.Errorf("sign SSH Kerberos MIC: %w", err)
	}
	return token, nil
}

func (c *SSPIInitiatorClient) DeleteSecContext() error {
	var firstErr error
	if c.ctx != nil {
		if err := c.ctx.Release(); err != nil {
			firstErr = err
		}
		c.ctx = nil
	}
	if c.creds != nil {
		if err := c.creds.Release(); err != nil && firstErr == nil {
			firstErr = err
		}
		c.creds = nil
	}
	return firstErr
}
