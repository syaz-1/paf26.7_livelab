# Linux Health Assistant with Private Agent Factory

A 90-minute LiveLabs-style workshop: build a diagnosis-only PAF assistant for one
dedicated Oracle Linux 9 VM, then investigate filesystem capacity, CPU pressure
and a stopped demonstration service. This is a local workshop package, not a
published Oracle LiveLabs offering.

```text
Learner → PAF Chat Input → Agent → Chat Output
                           ↑ Tools
                HTTPS Streamable HTTP /mcp
                           ↓
           Python MCP service on dedicated OL9 VM
                           ↓
             fixed read-only local OS checks
```

The target VM must be separate from the PAF host. Keep your existing database
monitoring workflows unchanged. This lab does not modify databases and requires
no SQL grants or Select AI profile.

PAF registers and calls the MCP endpoint; the Python service supplies the OS
tools. A separate MCP process could share the PAF VM, but these collectors read
the machine where they run. Doing that would monitor the PAF host and put fault
exercises on it. This workshop therefore keeps MCP and the fixtures on the
dedicated target. Hosting MCP beside PAF while checking a remote machine would
require remote collectors, which this version does not implement. See Oracle's
[custom MCP service guide](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/build-your-own-mcp-server.html).

## Prerequisites and instructor setup

Prepare an expendable Oracle Linux 9 VM with systemd, sudo access, at least two
logical CPUs and 2 GiB RAM, and repository access for Python 3.11. Those resources
are for this target only, not PAF/model hosting. PAF and a model supporting tool
calling must already work. Allow 30–45 minutes of instructor preparation outside
the workshop. Use a private IP/DNS route from the PAF container/network to the VM.

1. Copy this `os-lab` directory to the dedicated VM. Run:

   ```bash
   sudo bash instructor/setup.sh --dedicated-lab-vm
   sudo bash instructor/fixtures.sh prepare
   ```

   Setup installs Python 3.11 packages, creates an unprivileged `paf-health`
   account, installs files under `/opt/paf-linux-lab`, generates a private random
   token under `/etc/paf-linux-lab/token`, and starts the demo service. It does
   **not** start MCP until TLS is configured. It refuses an existing installation;
   after a partial failure, inspect installed state rather than deleting it blindly.

2. Obtain a certificate and private key for the VM's actual DNS name from your
   approved CA. Include intermediate certificates in the certificate PEM. Put
   them in `/etc/paf-linux-lab/server.crt` and `server.key`, owned by
   `root:paf-health`, mode `0640`. Keep the directory mode `0750`. Ensure the
   issuing CA is trusted by the PAF runtime/container and by your checker.
   Do not disable TLS verification or use an unrelated server's certificate.

3. Create `/etc/paf-linux-lab/server.env` as root, mode `0600`, with these values,
   replacing the example DNS name:

   ```ini
   PAF_LAB_PUBLIC_URL=https://linux-lab.example.internal:8443/mcp
   PAF_LAB_TOKEN_FILE=/etc/paf-linux-lab/token
   PAF_LAB_TLS_CERT=/etc/paf-linux-lab/server.crt
   PAF_LAB_TLS_KEY=/etc/paf-linux-lab/server.key
   ```

   Only the exact public Host header is accepted. Use the configured name and
   port when connecting. No reverse proxy is required; Uvicorn terminates TLS.

4. Permit TCP 8443 **only from the PAF runtime and instructor checker source**
   through the VM firewall and, on OCI, the relevant NSG/security rules. Retain
   SELinux enforcement. Investigate denied operations in local audit logs;
   do not disable SELinux to work around deployment problems. The service has
   no sudo rights and needs only readable `/proc`, statvfs and read-only systemd
   state. It intentionally does not expose process arguments or environments.

5. Start and inspect the service:

   ```bash
   sudo systemctl enable --now paf-linux-mcp.service
   sudo systemctl status paf-linux-mcp.service --no-pager
   sudo journalctl -u paf-linux-mcp.service -n 30 --no-pager
   ```

   This package uses a pre-shared bearer token for direct PAF authentication,
   not an OAuth authorization server. Transfer the generated token through your
   approved secret channel into PAF's Bearer Token credential field. Do not put
   tokens in command arguments, screenshots, source files or workshop notes.

6. Run the protocol checker from an approved machine on the PAF network, using
   a private token file and optionally your CA PEM:

   ```bash
   python3.11 -m venv /tmp/linux-lab-check
   /tmp/linux-lab-check/bin/python -m pip install -r requirements.txt
   /tmp/linux-lab-check/bin/python check_mcp.py \
     --url https://linux-lab.example.internal:8443/mcp \
     --token-file /secure/path/linux-lab-token \
     --ca-file /secure/path/approved-ca.pem
   ```

   Omit `--ca-file` when the CA is already trusted. The checker rejects missing
   and invalid credentials, negotiates MCP, verifies the exact five-tool
   inventory, calls each tool sequentially and tests parameter bounds. All
   collectors must return complete evidence for this baseline check. A stopped
   demo unit is valid evidence; a missing unit/mount is incomplete evidence.

The 64 MiB tmpfs is recreated with `fixtures.sh prepare` after every VM reboot.
It is deliberately not mounted through `/etc/fstab`.

## Lab 1 — Connect and build the assistant (15 minutes)

1. In PAF, create an MCP source named **Linux Health Lab** with the instructor's
   `https://...:8443/mcp` endpoint, Streamable HTTP transport and Bearer Token
   authentication. Validate discovery of exactly the five tools below.
2. Create a separate workflow named **Linux Health Assistant Lab**. Connect
   **Chat Input Message → Agent Prompt**, **MCP Server Tools → Agent Tools**,
   and **Agent Message → Chat Output Message**.
3. Select all five diagnostic tools and the approved tool-calling model. Use a
   low temperature, disable memory and paste [agent-instructions.txt](agent-instructions.txt)
   into the Agent instructions. Save as a draft and use Playground.
4. Ask “Which host can you check?” and inspect the actual tool invocation.

PAF's labels may vary by release; use its MCP registration and Agent tool
connection rather than a database/Select AI node. See the
[Oracle component guide](https://docs.oracle.com/en/database/oracle/agent-factory/26.7/paias/agent-builder-components.html).

| Tool | Parameters and evidence |
|---|---|
| `get_host_summary` | No arguments; identity, kernel, uptime, logical CPUs and load averages. |
| `sample_performance` | `seconds`: integer 1–5, default 2; host CPU busy/iowait, available memory, swap activity rates. |
| `get_filesystem_usage` | No arguments; root and lab mount capacity/inodes only. Missing lab mount is an error. |
| `get_top_processes` | `limit`: integer 1–10, default 5; approximately one-second CPU sample, names/PIDs/RSS only; up to 4096 scanned processes. |
| `get_demo_service_status` | No arguments; only `paf-lab-demo.service` load/active/substate/result. |

Each result includes host, UTC observation time, measurement duration, data and
errors with `ok`, `partial` or `unavailable` status. Results are separate snapshots.
Collectors serialize sampling; concurrent excess calls return busy, not healthy.

## Lab 2 — Establish baseline health (15 minutes)

Ask: **“Check this server's current health.”** Inspect traces for summary,
performance, filesystem and service calls. Compare storage evidence with
`df -h / /var/lib/paf-linux-lab/disk` and inode evidence with `df -i` on the VM.
The demo service should be active and lab capacity mostly free.

Discuss available versus free RAM, used swap versus active swap traffic, and
load average versus logical CPU count. Agree that a short sample cannot prove
all aspects of a server are healthy.

## Lab 3 — Diagnose filesystem pressure (20 minutes)

Instructor creates the fault:

```bash
sudo bash instructor/fixtures.sh disk-full
```

Ask: **“Which filesystem needs attention? Is it capacity or inodes?”** Expect
about 91% usage on the dedicated mount, crossing the lab warning threshold of
85%. Critical is 95%. Root usage should be evaluated separately. The fixture
consumes at most 58 MiB in a 64 MiB tmpfs; it never fills the root filesystem.
This demonstrates capacity diagnosis, not physical disk throughput.

Ask the agent to delete the file: it must explain its diagnosis-only capability.
Instructor resets and learners verify usage clears:

```bash
sudo bash instructor/fixtures.sh reset
```

## Lab 4 — Diagnose CPU pressure (20 minutes)

```bash
sudo bash instructor/fixtures.sh cpu-load
```

Immediately ask: **“Why is this server slow? Show the busiest processes.”**
The busy Python process should appear at roughly 100% of one logical CPU.
Overall CPU utilization may be much lower on a multi-core VM; this fixture does
not guarantee host-wide saturation. CPU sampling and process ranking occur at
different times, so they support correlation rather than an atomic proof.

The workload has a 120-second systemd runtime limit and one-core CPU quota.
Repeat the fixture if it expires before the check. It refuses a concurrently
running unit of the same name. Ask the agent to kill it: no action is available.
Reset manually and verify the workload stops with another live sample.

## Lab 5 — Diagnose a stopped service (15 minutes)

```bash
sudo bash instructor/fixtures.sh service-stop
```

Ask: **“Is the demo service running?”** Expect `ActiveState=inactive`. This is
a demonstration sleep service, not an application availability probe. Ask the
agent to restart it and confirm it offers advice without claiming execution.
Instructor runs reset; a new tool call must show it active.

## Lab 6 — Reset and acceptance review (5 minutes)

```bash
sudo bash instructor/fixtures.sh reset
```

Confirm low lab mount usage, no fixture CPU process and active demo service.
Ask **“Was it slower yesterday?”** Expect an explicit lack-of-history explanation.
Use [acceptance-prompts.md](acceptance-prompts.md) for the complete instructor
acceptance suite, including unavailable/partial evidence and denied access.

To release the tmpfs after the workshop, run `fixtures.sh unmount` with sudo
after reset. Stop/disable `paf-linux-mcp.service` if the endpoint is no longer
needed, remove its PAF credential/source when unused, and retire the dedicated
VM according to your normal process. Do not delete shared PAF resources.
To rotate the token, generate a replacement into a root-private temporary file,
install it as `root:paf-health` mode `0640`, update PAF's secret and restart MCP.

## Validation and boundaries

Run local tests on Python 3.11+:

```bash
python3.11 -m venv /tmp/linux-lab-tests
/tmp/linux-lab-tests/bin/python -m pip install -r os-lab/requirements.txt
/tmp/linux-lab-tests/bin/python -m unittest discover -s os-lab/tests -v
bash -n os-lab/instructor/setup.sh os-lab/instructor/fixtures.sh
```

Local tests cover collector errors, parameter bounds, authorization and MCP
discovery/calls. On 15 October 2026, **17 tests passed** on Python 3.11.17,
including a real SDK client against a loopback HTTPS server with an ephemeral
test certificate. That check rejected an untrusted certificate and missing/wrong
bearer tokens, then completed discovery and five tool calls. Filesystem/service
results in that HTTPS check were synthetic; CPU/memory/process collection ran
locally. Shell syntax and Git whitespace checks also passed. Threaded protocol
tests required execution outside the restricted sandbox. The SDK emitted a
Pydantic settings forward-reference warning and a client API deprecation warning;
neither caused test failures.

These checks do not certify OL9 package installation, systemd hardening,
SELinux behavior, fixture execution, certificate trust, routing or PAF behavior.
Those require the prepared VM and live PAF traces. No live deployment or fixture
has been executed by adding this package. No PAF workflow has been created by
the local implementation; Lab 1 supplies the exact configuration.

The SDK is pinned to its 1.x maintenance API to keep this lab's FastMCP imports
reproducible; see [the SDK v1 documentation](https://py.sdk.modelcontextprotocol.io/v1/).
The five-tool allowlist and unprivileged OS account enforce the execution
boundary; model instructions alone are not authorization. Requests and returned
host data go to the configured model and PAF traces: use approved destinations.
Historical monitoring, directory/log inspection, network diagnosis, arbitrary
service management, automatic fixes and multi-host operation are extensions.
