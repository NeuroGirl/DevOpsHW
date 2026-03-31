import os
import sys
import json
import ctypes

libc = ctypes.CDLL('libc.so.6', use_errno=True)

CLONE_NEWUTS = 0x04000000
CLONE_NEWPID = 0x20000000
CLONE_NEWNS = 0x00020000


def limit_resources(container_id, resources):
    cpath = f"/sys/fs/cgroup/{container_id}"
    os.makedirs(cpath, exist_ok=True)
    mem_cfg = resources.get("memory", {})
    mem_limit = str(mem_cfg["limit"])
    with open(f"{cpath}/memory.max", "w") as f: f.write(mem_limit)
    cpu_cfg = resources.get("cpu", {})
    cpu_quota  = str(cpu_cfg["quota"])
    cpu_period = str(cpu_cfg["period"])
    with open(f"{cpath}/cpu.max", "w") as f: f.write(f"{cpu_quota} {cpu_period}")
    with open(f"{cpath}/cgroup.procs", "w") as f: f.write(str(os.getpid()))

def setup_overlay(container_id):
    base = f"/var/lib/my-tool/{container_id}"
    lower = "/tmp/alpine/rootfs"
    upper, work, merged = f"{base}/upper", f"{base}/work", f"{base}/merged"
    for d in [upper, work, merged]: os.makedirs(d, exist_ok=True)

    opts = f"lowerdir={lower},upperdir={upper},workdir={work}"
    libc.mount(b"overlay", merged.encode(), b"overlay", 0, opts.encode())
    return merged


def child_process(container_id):
    config = json.load(open('config.json'))
    resources = config.get("linux", {}).get("resources", {})
    limit_resources(container_id, resources)

    hostname = config.get('hostname', 'container')
    libc.sethostname(hostname.encode(), len(hostname))

    merged_path = setup_overlay(container_id)

    proc_path = os.path.join(merged_path, 'proc')
    os.makedirs(proc_path, exist_ok=True)
    libc.mount(b"proc", proc_path.encode(), b"proc", 0, None)

    os.chroot(merged_path)
    os.chdir("/")

    args = config['process']['args']
    os.execvp(args[0], args)


def main():
    try:
        libc.unshare(CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS)
    except Exception as error:
        print(f"{error}")
        return

    pid = os.fork()
    if pid == 0:
        child_process(sys.argv[2])
    else:
        os.waitpid(pid, 0)
        print("\n[Контейнер завершен]")


if __name__ == "__main__":
    main()
