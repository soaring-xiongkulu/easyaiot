package com.basiclab.iot.node.util;

import cn.hutool.core.util.StrUtil;
import com.basiclab.iot.node.domain.vo.NodeOnboardPreflightRespVO;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.jcraft.jsch.JSchException;
import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.List;

/**
 * 纳管前预检：SSH、Python、磁盘、Agent 端口、控制面连通、功能依赖（Docker/GPU）。
 * 运行时由控制面离线分发，公网探测仅作提示，不阻断纳管。
 */
@Slf4j
public final class NodeOnboardPreflight {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final long MIN_DISK_BYTES = 2L * 1024 * 1024 * 1024;

    private NodeOnboardPreflight() {
    }

    public static NodeOnboardPreflightRespVO run(
            String host, int sshPort, String username, String authType,
            String password, String privateKey, int agentPort,
            boolean needDocker, boolean needGpu, String controlPlaneUrl) {
        NodeOnboardPreflightRespVO resp = new NodeOnboardPreflightRespVO();
        try (SshSessionHelper ssh = SshSessionHelper.connect(
                host, sshPort, username, authType, password, privateKey)) {
            String script = buildRemoteScript(agentPort, needDocker, needGpu, controlPlaneUrl);
            SshSessionHelper.SshExecResult exec = ssh.exec(script, 45000);
            return parse(exec.combinedOutput(), exec.getExitCode());
        } catch (JSchException e) {
            resp.setOk(false);
            resp.setMessage("SSH 连接失败 " + username + "@" + host + ":" + sshPort + " — " + e.getMessage());
            NodeOnboardPreflightRespVO.Check check = new NodeOnboardPreflightRespVO.Check();
            check.setName("ssh");
            check.setOk(false);
            check.setDetail(e.getMessage());
            resp.getChecks().add(check);
            return resp;
        } catch (Exception e) {
            log.warn("节点预检异常 {}:{} {}", host, sshPort, e.getMessage());
            resp.setOk(false);
            resp.setMessage("节点预检异常: " + e.getMessage());
            return resp;
        }
    }

    private static String buildRemoteScript(int agentPort, boolean needDocker, boolean needGpu, String controlPlaneUrl) {
        String cp = controlPlaneUrl == null ? "" : controlPlaneUrl.replace("\\", "\\\\").replace("'", "\\'");
        return "python3 - <<'PY'\n"
                + "import json, os, shutil, socket, subprocess, sys, urllib.request\n"
                + "from urllib.parse import urlparse\n"
                + "agent_port = " + agentPort + "\n"
                + "need_docker = " + (needDocker ? "True" : "False") + "\n"
                + "need_gpu = " + (needGpu ? "True" : "False") + "\n"
                + "cp_url = '" + cp + "'\n"
                + "min_disk = " + MIN_DISK_BYTES + "\n"
                + "checks = []\n"
                + "ok_all = True\n"
                + "def add(name, ok, detail, required=True):\n"
                + "    global ok_all\n"
                + "    checks.append({'name': name, 'ok': bool(ok), 'detail': str(detail), 'required': bool(required)})\n"
                + "    if required and not ok:\n"
                + "        ok_all = False\n"
                + "add('python3', True, sys.version.split()[0])\n"
                + "st = os.statvfs('/')\n"
                + "avail = st.f_bavail * st.f_frsize\n"
                + "add('disk', avail >= min_disk, f'{avail // (1024**3)}GB 可用（至少 2GB）')\n"
                + "def port_busy(port):\n"
                + "    s = socket.socket()\n"
                + "    s.settimeout(0.4)\n"
                + "    try:\n"
                + "        r = s.connect_ex(('127.0.0.1', port))\n"
                + "        return r == 0\n"
                + "    finally:\n"
                + "        s.close()\n"
                + "busy = port_busy(agent_port)\n"
                + "add('agentPort', not busy, f'{agent_port} 已被占用' if busy else f'{agent_port} 空闲')\n"
                + "def reachable(url):\n"
                + "    try:\n"
                + "        urllib.request.urlopen(url, timeout=8)\n"
                + "        return True, '可达'\n"
                + "    except Exception as e:\n"
                + "        return False, str(e)\n"
                + "pypi_ok, pypi_d = reachable('https://pypi.org')\n"
                + "gh_ok, gh_d = reachable('https://github.com') if not pypi_ok else (True, '跳过')\n"
                + "add('resourcePull', pypi_ok or gh_ok,\n"
                + "    (f'pypi {pypi_d}' if pypi_ok else f'公网不可达 pypi={pypi_d}; github={gh_d}（离线分发，不阻断）'),\n"
                + "    False)\n"
                + "if need_docker:\n"
                + "    docker = shutil.which('docker')\n"
                + "    add('docker', bool(docker), docker or '未安装 docker，直播/物联功能无法拉起容器')\n"
                + "if need_gpu:\n"
                + "    gpu = shutil.which('nvidia-smi') is not None\n"
                + "    if gpu:\n"
                + "        p = subprocess.run(['nvidia-smi', '-L'], capture_output=True, text=True, timeout=8)\n"
                + "        gpu = p.returncode == 0 and bool((p.stdout or '').strip())\n"
                + "        add('gpu', gpu, (p.stdout or p.stderr or '').strip()[:200] or 'nvidia-smi 无输出')\n"
                + "    else:\n"
                + "        add('gpu', False, '未检测到 NVIDIA GPU，训练/大模型功能无法调度')\n"
                + "if cp_url:\n"
                + "    u = urlparse(cp_url)\n"
                + "    h, p = u.hostname or '', (u.port or (443 if u.scheme=='https' else 80))\n"
                + "    if not h or h in ('127.0.0.1','localhost','::1'):\n"
                + "        add('controlPlane', False, f'控制面地址 {cp_url} 是回环，远程节点无法上报心跳')\n"
                + "    else:\n"
                + "        s = socket.socket(); s.settimeout(5)\n"
                + "        try:\n"
                + "            s.connect((h, int(p)))\n"
                + "            add('controlPlane', True, f'{h}:{p} 可达')\n"
                + "        except Exception as e:\n"
                + "            add('controlPlane', False, f'无法连接控制面 {h}:{p}，心跳无法上报: {e}')\n"
                + "        finally:\n"
                + "            s.close()\n"
                + "print('PREFLIGHT_JSON=' + json.dumps({'ok': ok_all, 'checks': checks}, ensure_ascii=False))\n"
                + "sys.exit(0 if ok_all else 2)\n"
                + "PY\n";
    }

    private static NodeOnboardPreflightRespVO parse(String output, int exitCode) {
        NodeOnboardPreflightRespVO resp = new NodeOnboardPreflightRespVO();
        String json = extractJson(output);
        if (StrUtil.isBlank(json)) {
            resp.setOk(false);
            resp.setMessage("预检脚本无有效输出。请确认目标机已安装 python3。\n" + StrUtil.maxLength(output, 800));
            return resp;
        }
        try {
            JsonNode root = MAPPER.readTree(json);
            boolean ok = root.path("ok").asBoolean(false);
            List<NodeOnboardPreflightRespVO.Check> checks = new ArrayList<>();
            List<String> failed = new ArrayList<>();
            if (root.path("checks").isArray()) {
                for (JsonNode n : root.path("checks")) {
                    NodeOnboardPreflightRespVO.Check c = new NodeOnboardPreflightRespVO.Check();
                    c.setName(n.path("name").asText());
                    c.setOk(n.path("ok").asBoolean(false));
                    c.setDetail(n.path("detail").asText());
                    c.setRequired(n.path("required").asBoolean(true));
                    checks.add(c);
                    if (!Boolean.TRUE.equals(c.getOk()) && !Boolean.FALSE.equals(c.getRequired())) {
                        failed.add(labelOf(c.getName()) + "：" + c.getDetail());
                    }
                }
            }
            resp.setChecks(checks);
            resp.setOk(ok && failed.isEmpty() && exitCode != 2);
            if (Boolean.TRUE.equals(resp.getOk())) {
                resp.setMessage("预检通过，可安装 Sentinel（运行时由控制面离线分发，不要求节点访问公网）");
            } else {
                resp.setMessage("节点预检未通过，无法添加：" + String.join("；", failed));
            }
            return resp;
        } catch (Exception e) {
            resp.setOk(false);
            resp.setMessage("预检结果解析失败: " + e.getMessage());
            return resp;
        }
    }

    private static String extractJson(String output) {
        if (output == null) {
            return "";
        }
        int idx = output.lastIndexOf("PREFLIGHT_JSON=");
        if (idx < 0) {
            return "";
        }
        return output.substring(idx + "PREFLIGHT_JSON=".length()).trim();
    }

    private static String labelOf(String name) {
        if ("python3".equals(name)) return "Python";
        if ("disk".equals(name)) return "磁盘";
        if ("agentPort".equals(name)) return "Agent 端口";
        if ("resourcePull".equals(name)) return "外网资源拉取";
        if ("docker".equals(name)) return "Docker";
        if ("gpu".equals(name)) return "GPU";
        if ("controlPlane".equals(name)) return "控制面连通";
        return name;
    }
}
