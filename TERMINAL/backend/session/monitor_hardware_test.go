package session

import (
	"reflect"
	"testing"
)

// --- systemctl list-units parsing ---

func TestParseSystemctlUnits(t *testing.T) {
	out := `nginx.service                       loaded    active     running     A high performance web server and a reverse proxy
ssh.service                         loaded    active     running     OpenBSD Secure Shell server
systemd-fsck@dev-sda1.service       loaded    active     exited      File System Check on /dev/sda1
docker.service                      loaded    failed     failed      Docker Application Container Engine
unattended-upgrades.service         loaded    inactive   dead        Unattended Upgrades Shutdown
`
	got := parseSystemctlUnits(out)
	want := []ServiceInfo{
		{Name: "nginx.service", Load: "loaded", Active: "active", Sub: "running", Description: "A high performance web server and a reverse proxy"},
		{Name: "ssh.service", Load: "loaded", Active: "active", Sub: "running", Description: "OpenBSD Secure Shell server"},
		{Name: "systemd-fsck@dev-sda1.service", Load: "loaded", Active: "active", Sub: "exited", Description: "File System Check on /dev/sda1"},
		{Name: "docker.service", Load: "loaded", Active: "failed", Sub: "failed", Description: "Docker Application Container Engine"},
		{Name: "unattended-upgrades.service", Load: "loaded", Active: "inactive", Sub: "dead", Description: "Unattended Upgrades Shutdown"},
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("parseSystemctlUnits mismatch\n got: %#v\nwant: %#v", got, want)
	}
}

func TestParseSystemctlUnitsShortLine(t *testing.T) {
	// A unit whose description is missing must not panic or drop fields.
	out := "foo.service    loaded    active     running\n"
	got := parseSystemctlUnits(out)
	if len(got) != 1 {
		t.Fatalf("want 1 service, got %d", len(got))
	}
	if got[0].Description != "" {
		t.Errorf("want empty description, got %q", got[0].Description)
	}
	if got[0].Name != "foo.service" || got[0].Active != "active" {
		t.Errorf("unexpected service: %#v", got[0])
	}
}

// --- systemctl list-unit-files parsing ---

func TestParseSystemctlUnitFiles(t *testing.T) {
	// Newer systemd prints a VENDOR-PRESET column; older prints only two.
	out := `nginx.service                        enabled      enabled
ssh.service                          enabled      enabled
cups.service                         disabled     disabled
systemd-fsck@dev-sda1.service        static       -
docker.service                       enabled      enabled
`
	got := parseSystemctlUnitFiles(out)
	want := map[string]string{
		"nginx.service":                 "enabled",
		"ssh.service":                   "enabled",
		"cups.service":                  "disabled",
		"docker.service":                "enabled",
		"systemd-fsck@dev-sda1.service": "static",
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("parseSystemctlUnitFiles mismatch\n got: %#v\nwant: %#v", got, want)
	}
}

// --- lspci -mm parsing ---

func TestParseLspciMm(t *testing.T) {
	out := `00:00.0 "Host bridge" "Intel Corporation" "82G33/G31/P35/P31 Express DRAM Controller" -r0a "Dell" "OptiPlex 755"
00:1f.2 "SATA controller" "Intel Corporation" "82801IR/IO/IH (ICH9R/DO/DH) 6 port SATA Controller [AHCI mode]" -r02 "Dell" "OptiPlex 755"
01:00.0 "VGA compatible controller" "NVIDIA Corporation" "GK107 [GeForce GT 640]"
`
	got := parseLspciMm(out)
	if len(got) != 3 {
		t.Fatalf("want 3 devices, got %d", len(got))
	}
	d := got[0]
	if d.ID != "00:00.0" || d.Class != "Host bridge" || d.Vendor != "Intel Corporation" ||
		d.Product != "82G33/G31/P35/P31 Express DRAM Controller" || d.Rev != "0a" {
		t.Errorf("device 0 mismatch: %#v", d)
	}
	if got[2].Rev != "" || got[2].Vendor != "NVIDIA Corporation" {
		t.Errorf("device 2 mismatch: %#v", got[2])
	}
}

func TestParseLspciTextFallback(t *testing.T) {
	out := `00:00.0 Host bridge: Intel Corporation 82G33/G31/P35/P31 Express DRAM Controller (rev 0a)
01:00.0 VGA compatible controller: NVIDIA Corporation GK107 [GeForce GT 640] (rev a1)
`
	got := parseLspciText(out)
	if len(got) != 2 {
		t.Fatalf("want 2 devices, got %d", len(got))
	}
	// The text format has no vendor/device boundary, so the vendor keeps only
	// its first word and everything else lands in Product.
	d := got[0]
	if d.ID != "00:00.0" || d.Class != "Host bridge" || d.Vendor != "Intel" ||
		d.Product != "Corporation 82G33/G31/P35/P31 Express DRAM Controller" || d.Rev != "0a" {
		t.Errorf("device 0 mismatch: %#v", d)
	}
	if got[1].Product != "Corporation GK107 [GeForce GT 640]" {
		t.Errorf("device 1 mismatch: %#v", got[1])
	}
}

// --- ipmitool sensor list parsing ---

func TestParseIpmitoolSensors(t *testing.T) {
	out := `CPU Temp        | 34.000     | degrees C  | ok    | na        | 3.000     | 0.000     | 0.000     | 85.000    | 90.000
SYS FAN1        | 2400.000   | RPM        | cr    | na        | 100.000   | 200.000   | 300.000   | na        | na
+12V            | 12.100     | Volts      | ok    | na        | 0.000     | 0.000     | 0.000     | 11.000    | 13.000
PS Status       | 0x0        | discrete   | 0x0100| na        | na        | na        | na        | na        | na
`
	got := parseIpmitoolSensors(out)
	if len(got) != 4 {
		t.Fatalf("want 4 sensors, got %d", len(got))
	}
	if got[0].Name != "CPU Temp" || got[0].Value != "34.000" || got[0].Unit != "degrees C" || got[0].Status != "ok" {
		t.Errorf("sensor 0 mismatch: %#v", got[0])
	}
	if got[1].Status != "cr" {
		t.Errorf("sensor 1 status mismatch: %#v", got[1])
	}
	if got[3].Status != "0x0100" {
		t.Errorf("discrete status mismatch: %#v", got[3])
	}
}

// --- ipmitool fru print parsing ---

func TestParseIpmiFru(t *testing.T) {
	out := `FRU Device Description : Builtin FRU Device (ID 0)
 Board Product         : PowerEdge R740
 Board Manufacturer    : Dell Inc.
 Board Serial          : BOARD123
 Board Part Number     : 0PART
 Product Manufacturer  : Dell Inc.
 Product Name          : PowerEdge R740
 Product Serial        : SER456
 Product Part Number   : 0PN789
`
	got := parseIpmiFru(out)
	if got == nil {
		t.Fatal("want non-nil FruInfo")
	}
	if got.Product != "PowerEdge R740" || got.Manufacturer != "Dell Inc." ||
		got.Serial != "SER456" || got.PartNumber != "0PN789" {
		t.Errorf("FruInfo mismatch: %#v", got)
	}
}

func TestParseIpmiFruEmpty(t *testing.T) {
	if got := parseIpmiFru(""); got != nil {
		t.Errorf("want nil for empty output, got %#v", got)
	}
	if got := parseIpmiFru("not fru output at all"); got != nil {
		t.Errorf("want nil for non-FRU output, got %#v", got)
	}
}

// --- device category classification ---

func TestDeviceCategory(t *testing.T) {
	cases := map[string]string{
		// lshw classes
		"processor":     "processor",
		"memory":        "memory",
		"disk":          "storage",
		"storage":       "storage",
		"volume":        "storage",
		"tape":          "storage",
		"network":       "network",
		"communication": "network",
		"display":       "display",
		"multimedia":    "display",
		"bus":           "bus",
		"bridge":        "bus",
		"input":         "other",
		"generic":       "other",
		// lspci class texts (fallback path)
		"Host bridge":                    "bus",
		"USB controller":                 "bus",
		"VGA compatible controller":      "display",
		"Audio device":                   "display",
		"Ethernet controller":            "network",
		"Network controller":             "network",
		"SATA controller":                "storage",
		"Non-Volatile memory controller": "storage",
		"RAM memory":                     "memory",
		"ISA bridge":                     "bus",
		"Signal processing controller":   "other",
	}
	for in, want := range cases {
		if got := deviceCategory(in); got != want {
			t.Errorf("deviceCategory(%q) = %q, want %q", in, got, want)
		}
	}
}

// --- lshw -json parsing ---

const lshwSample = `{
  "id": "machine", "class": "system", "description": "Computer",
  "children": [
    {
      "id": "core", "class": "bus", "description": "Motherboard",
      "children": [
        {
          "id": "usb", "class": "bus", "description": "USB controller",
          "businfo": "pci@0000:00:14.0", "vendor": "Intel Corp.",
          "product": "8000 Series USB Controller", "version": "00",
          "configuration": {"driver": "xhci_hcd", "latency": "0"},
          "children": [
            {
              "id": "usbhost", "class": "bus", "description": "USB mass storage",
              "businfo": "usb@1:3", "vendor": "SanDisk",
              "product": "Ultra USB 3.0", "serial": "ABC123"
            }
          ]
        },
        {
          "id": "nvme", "class": "storage", "description": "Non-Volatile memory controller",
          "businfo": "pci@0000:01:00.0", "vendor": "Samsung",
          "product": "NVMe Controller", "configuration": {"driver": "nvme"},
          "children": [
            {
              "id": "namespace", "class": "disk", "description": "NVMe disk",
              "businfo": "nvme@0:1", "logicalname": ["nvme0n1"],
              "product": "Samsung SSD 970 EVO", "serial": "S123456",
              "version": "1B2QEXM7", "size": 512110190592
            }
          ]
        },
        {
          "id": "pci", "class": "bridge", "description": "PCI bridge",
          "businfo": "pci@0000:00:1c.0", "vendor": "Intel Corp.",
          "product": "6th Gen PCI Express Root Port", "configuration": {"driver": "pcieport"}
        },
        {
          "id": "sda", "class": "disk", "description": "SATA disk",
          "businfo": "scsi@0:0.0.0", "logicalname": ["/dev/sda"],
          "product": "SATA SSD", "size": 250059350016
        }
      ]
    }
  ]
}`

func TestParseLshwDevices(t *testing.T) {
	got := parseLshwDevices(lshwSample)
	// Every tree node becomes a row, in tree order; no filtering by bus type.
	if len(got) != 8 {
		t.Fatalf("want 8 devices, got %d: %#v", len(got), got)
	}
	d := got[2] // USB controller
	if d.ID != "pci@0000:00:14.0" || d.Vendor != "Intel Corp." ||
		d.Product != "8000 Series USB Controller" || d.Driver != "xhci_hcd" || d.Rev != "00" {
		t.Errorf("usb controller mismatch: %#v", d)
	}
	if got[3].ID != "usb@1:3" || got[3].Vendor != "SanDisk" || got[3].Serial != "ABC123" {
		t.Errorf("usb device mismatch: %#v", got[3])
	}
	if got[4].ID != "pci@0000:01:00.0" || got[4].Driver != "nvme" {
		t.Errorf("nvme controller mismatch: %#v", got[4])
	}
	nvmeDisk := got[5]
	if nvmeDisk.ID != "nvme0n1" || nvmeDisk.Serial != "S123456" ||
		nvmeDisk.Rev != "1B2QEXM7" || nvmeDisk.Capacity == "" {
		t.Errorf("nvme disk mismatch: %#v", nvmeDisk)
	}
	if got[6].ID != "pci@0000:00:1c.0" {
		t.Errorf("pci bridge mismatch: %#v", got[6])
	}
	if got[7].ID != "/dev/sda" || got[7].Capacity == "" {
		t.Errorf("sata disk mismatch: %#v", got[7])
	}
}

func TestParseLshwDevicesInvalid(t *testing.T) {
	if got := parseLshwDevices("lshw: not json"); len(got) != 0 {
		t.Errorf("want empty for non-JSON output, got %#v", got)
	}
	if got := parseLshwDevices(""); len(got) != 0 {
		t.Errorf("want empty for empty output, got %#v", got)
	}
}

// --- ipmitool lan print parsing ---

func TestParseIpmiLan(t *testing.T) {
	out := `Set in Progress         : Set Complete
Auth Type Support       :
Auth Type Enable        : Callback :
                        : MD2 :
                        : MD5 :
IP Address Source       : Static Address
IP Address              : 192.168.1.100
Subnet Mask             : 255.255.255.0
MAC Address             : 0c:c4:7a:11:22:33
SNMP Community String   : public
IP Header               : TTL=0x40 Flags=0x40 Precedence=0x00 TOS=0x10
Default Gateway IP      : 192.168.1.1
Default Gateway MAC     : 00:00:00:00:00:00
`
	got := parseIpmiLan(out)
	// Continuation lines (empty key) and empty values must be skipped.
	want := []LanField{
		{Key: "Set in Progress", Value: "Set Complete"},
		{Key: "Auth Type Enable", Value: "Callback :"},
		{Key: "IP Address Source", Value: "Static Address"},
		{Key: "IP Address", Value: "192.168.1.100"},
		{Key: "Subnet Mask", Value: "255.255.255.0"},
		{Key: "MAC Address", Value: "0c:c4:7a:11:22:33"},
		{Key: "SNMP Community String", Value: "public"},
		{Key: "IP Header", Value: "TTL=0x40 Flags=0x40 Precedence=0x00 TOS=0x10"},
		{Key: "Default Gateway IP", Value: "192.168.1.1"},
		{Key: "Default Gateway MAC", Value: "00:00:00:00:00:00"},
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("parseIpmiLan mismatch\n got: %#v\nwant: %#v", got, want)
	}
}

func TestParseIpmiLanEmpty(t *testing.T) {
	if got := parseIpmiLan(""); len(got) != 0 {
		t.Errorf("want empty for empty output, got %#v", got)
	}
}

func TestStandardLanFields(t *testing.T) {
	in := []LanField{
		{Key: "Set in Progress", Value: "Set Complete"},
		{Key: "IP Address Source", Value: "Static Address"},
		{Key: "IP Address", Value: "192.168.1.100"},
		{Key: "Subnet Mask", Value: "255.255.255.0"},
		{Key: "MAC Address", Value: "0c:c4:7a:11:22:33"},
		{Key: "SNMP Community String", Value: "public"},
		{Key: "Default Gateway IP", Value: "192.168.1.1"},
		{Key: "Default Gateway MAC", Value: "00:00:00:00:00:00"},
	}
	got := standardLanFields(in)
	// Only the standard network fields, in a fixed display order.
	want := []LanField{
		{Key: "IP Address", Value: "192.168.1.100"},
		{Key: "Subnet Mask", Value: "255.255.255.0"},
		{Key: "MAC Address", Value: "0c:c4:7a:11:22:33"},
		{Key: "Default Gateway IP", Value: "192.168.1.1"},
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("standardLanFields mismatch\n got: %#v\nwant: %#v", got, want)
	}
}

// --- systemctl show parsing ---

func TestParseSystemctlShow(t *testing.T) {
	out := `LoadState=loaded
ActiveState=active
SubState=running
UnitFileState=enabled
Description=OpenBSD Secure Shell server
ExecMainPID=1234
MemoryCurrent=15728640
`
	got := parseSystemctlShow(out)
	if got["LoadState"] != "loaded" || got["ActiveState"] != "active" ||
		got["Description"] != "OpenBSD Secure Shell server" || got["MemoryCurrent"] != "15728640" {
		t.Errorf("parseSystemctlShow mismatch: %#v", got)
	}
}

// --- service log line clamping ---

func TestClampLogLines(t *testing.T) {
	cases := []struct{ in, want int }{
		{0, defaultLogLines},
		{-5, defaultLogLines},
		{50, 50},
		{200, 200},
		{100000, maxLogLines},
	}
	for _, c := range cases {
		if got := clampLogLines(c.in); got != c.want {
			t.Errorf("clampLogLines(%d) = %d, want %d", c.in, got, c.want)
		}
	}
}

// --- service action / unit name validation ---

func TestValidateServiceAction(t *testing.T) {
	for _, a := range []string{"start", "stop", "restart", "enable", "disable"} {
		if !validServiceAction(a) {
			t.Errorf("action %q should be valid", a)
		}
	}
	for _, a := range []string{"", "reboot", "start;", "mask", "START"} {
		if validServiceAction(a) {
			t.Errorf("action %q should be invalid", a)
		}
	}
}

func TestValidUnitName(t *testing.T) {
	for _, n := range []string{"nginx.service", "systemd-fsck@dev-sda1.service", "user@1000.service", "php8.2-fpm.service"} {
		if !validUnitName(n) {
			t.Errorf("unit %q should be valid", n)
		}
	}
	for _, n := range []string{"", "nginx;reboot", "a b", "$(reboot)", "a/b", "nginx\n", "a`id`", ".ssh/authorized_keys"} {
		if validUnitName(n) {
			t.Errorf("unit %q should be invalid", n)
		}
	}
}
