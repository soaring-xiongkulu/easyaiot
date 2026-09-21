package container

import (
	"context"
	"fmt"
	"strings"
)

type Provider struct {
	rt     Runtime
	ns     string
	runner Runner
}

func NewProvider(rt Runtime, ns string, r Runner) *Provider {
	if rt == RuntimeNerdctl && ns == "" {
		ns = "default"
	}
	return &Provider{rt: rt, ns: ns, runner: r}
}

func (p *Provider) Runtime() Runtime  { return p.rt }
func (p *Provider) Namespace() string { return p.ns }

func (p *Provider) List(ctx context.Context) ([]Container, error) {
	out, err := p.runner.Run(ctx, psArgs(p.rt, p.ns))
	if err != nil {
		return nil, err
	}
	return ParseContainers(p.rt, out)
}

func (p *Provider) Inspect(ctx context.Context, id string) (InspectResult, error) {
	out, err := p.runner.Run(ctx, inspectArgs(p.rt, p.ns, id))
	if err != nil {
		return InspectResult{}, err
	}
	d, err := ParseInspect(p.rt, out)
	if err != nil {
		return InspectResult{}, err
	}
	return InspectResult{Detail: d, Raw: string(out)}, nil
}

func (p *Provider) Action(ctx context.Context, id, action string) error {
	argv, err := actionArgs(p.rt, p.ns, action, id)
	if err != nil {
		return err
	}
	_, err = p.runner.Run(ctx, argv)
	return err
}

func (p *Provider) Rename(ctx context.Context, id, newName string) error {
	if strings.TrimSpace(newName) == "" {
		return fmt.Errorf("name required")
	}
	argv, err := renameArgs(p.rt, p.ns, id, newName)
	if err != nil {
		return err
	}
	_, err = p.runner.Run(ctx, argv)
	return err
}

func (p *Provider) Stats(ctx context.Context) ([]Stats, error) {
	out, err := p.runner.Run(ctx, statsArgs(p.rt, p.ns))
	if err != nil {
		return nil, err
	}
	return ParseStats(p.rt, out)
}

func (p *Provider) Images(ctx context.Context) ([]Image, error) {
	out, err := p.runner.Run(ctx, imagesArgs(p.rt, p.ns))
	if err != nil {
		return nil, err
	}
	return ParseImages(p.rt, out)
}

func (p *Provider) RemoveImage(ctx context.Context, imageID string) error {
	_, err := p.runner.Run(ctx, removeImageArgs(p.rt, p.ns, imageID))
	return err
}

func (p *Provider) Create(ctx context.Context, o CreateOptions) error {
	if strings.TrimSpace(o.Image) == "" {
		return fmt.Errorf("image required")
	}
	_, err := p.runner.Run(ctx, createArgs(p.rt, p.ns, o))
	return err
}

func (p *Provider) Logs(ctx context.Context, id string, tail int, follow, timestamps bool) (LineStream, error) {
	return p.runner.RunStream(ctx, logsArgs(p.rt, p.ns, id, tail, follow, timestamps))
}

func (p *Provider) Pull(ctx context.Context, image string) (LineStream, error) {
	if strings.TrimSpace(image) == "" {
		return nil, fmt.Errorf("image required")
	}
	return p.runner.RunStream(ctx, pullArgs(p.rt, p.ns, image))
}

func (p *Provider) Exec(ctx context.Context, id, shell string, cols, rows int) (PTYStream, error) {
	if shell == "" {
		shell = "sh"
	}
	return p.runner.RunPTY(ctx, execArgs(p.rt, p.ns, id, shell), cols, rows)
}

// Namespaces 仅 nerdctl 有意义。
func (p *Provider) Namespaces(ctx context.Context) ([]string, error) {
	if p.rt != RuntimeNerdctl {
		return nil, fmt.Errorf("namespaces only supported on nerdctl")
	}
	out, err := p.runner.Run(ctx, []string{p.rt.Bin(), "namespace", "ls"})
	if err != nil {
		return nil, err
	}
	return ParseNamespaces(out), nil
}

// DetectRuntimes 探测候选运行时中哪些可用（用于连接失败时的诊断）。
func DetectRuntimes(ctx context.Context, r Runner) []Runtime {
	var found []Runtime
	for _, rt := range []Runtime{RuntimeDocker, RuntimePodman, RuntimeNerdctl, RuntimeWSLC} {
		if _, err := r.Run(ctx, detectArgs(rt)); err == nil {
			found = append(found, rt)
		}
	}
	return found
}

// ValidateRuntime 校验所选运行时可用；不可用则探测其他并返回诊断错误。
func ValidateRuntime(ctx context.Context, rt Runtime, r Runner) error {
	if _, err := r.Run(ctx, detectArgs(rt)); err == nil {
		return nil
	}
	found := DetectRuntimes(ctx, r)
	if len(found) == 0 {
		return fmt.Errorf("container runtime %q not found; none of docker/podman/nerdctl/wslc detected", rt)
	}
	names := make([]string, len(found))
	for i, f := range found {
		names[i] = string(f)
	}
	return fmt.Errorf("container runtime %q not found; detected available: %s", rt, strings.Join(names, ", "))
}
