"""Trusted Linux-only controller. Provision manually; NEVER run against project code on host.

Network is available on GitHub-hosted runners. Only approved synthetic, secret-free input.
This controller is not a security sandbox for hostile code on the runner.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import time

FILES = ("calculator.py", "test_calculator.py")
LOG_LIMIT = 16384


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def limits():
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))


def main():
    job, commit, package = (os.environ.get(k, "") for k in ("KAY_JOB", "KAY_COMMIT", "KAY_PACKAGE"))
    if not re.fullmatch(r"[a-f0-9]{32}", job) or not re.fullmatch(r"[a-f0-9]{40}", commit) or not re.fullmatch(r"[a-f0-9]{64}", package):
        raise ValueError("invalid identifiers")
    source = Path("payload")
    if {p.name for p in source.iterdir()} != {*FILES, "manifest.json", ".git"}:
        raise ValueError("unexpected package files")
    for name in (*FILES, "manifest.json"):
        path = source / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16384:
            raise ValueError("invalid package file")
    manifest = json.loads((source / "manifest.json").read_text())
    if digest(manifest) != package or manifest["job"] != job or set(manifest["files"]) != set(FILES):
        raise ValueError("manifest mismatch")
    contents = {name: (source / name).read_bytes() for name in FILES}
    if {n: hashlib.sha256(b).hexdigest() for n, b in contents.items()} != manifest["files"]:
        raise ValueError("file hash mismatch")
    logs = {"stdout": bytearray(), "stderr": bytearray()}
    with tempfile.TemporaryDirectory(prefix="kay-test-") as directory:
        work = Path(directory)
        for name, data in contents.items():
            (work / name).write_bytes(data)
        # No GitHub/Actions environment or App credentials passed to the subprocess.
        env = {"PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin", "HOME": directory,
               "TMPDIR": directory, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONIOENCODING": "utf-8", "LANG": "C.UTF-8"}
        process = subprocess.Popen(["python", "-m", "pytest", "-q"], cwd=directory, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, start_new_session=True, preexec_fn=limits)
        poller = selectors.DefaultSelector()
        poller.register(process.stdout, selectors.EVENT_READ, "stdout")
        poller.register(process.stderr, selectors.EVENT_READ, "stderr")
        deadline = time.monotonic() + 30
        aborted = False
        try:
            while poller.get_map():
                if time.monotonic() >= deadline:
                    aborted = True
                    break
                for key, _ in poller.select(timeout=0.2):
                    data = os.read(key.fileobj.fileno(), 4096)
                    if not data:
                        poller.unregister(key.fileobj)
                    else:
                        target = logs[key.data]
                        remaining = LOG_LIMIT - len(target)
                        target.extend(data[:remaining])
                        if len(data) > remaining:
                            aborted = True
                            break
                if aborted: break
        finally:
            # Kill any surviving descendants, including those holding pipe handles.
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.wait(timeout=5)
            poller.close()
        exit_code = 124 if aborted else process.returncode
    output = Path("output"); output.mkdir(exist_ok=True)
    for name, data in logs.items():
        (output / (name + ".txt")).write_bytes(data)
    stdout = logs["stdout"].decode("utf-8", errors="replace")
    # Strip terminal escapes before reading pytest's fixed summary, never execute log text.
    stdout = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", stdout)
    passed = re.findall(r"\b(\d+) passed\b", stdout)
    failed = re.findall(r"\b(\d+) failed\b", stdout)
    result = {"job": job, "code_commit": commit, "package_sha256": package, "files": manifest["files"],
              "exit_code": exit_code, "passed": int(passed[-1]) if passed else 0,
              "failed": int(failed[-1]) if failed else 0}
    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
    # No untrusted output is printed as GitHub workflow commands.
    return 0 if exit_code == 0 and result["passed"] >= 1 and not result["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
