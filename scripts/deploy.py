"""Deploy one immutable image using Martin's existing EC2 SSM script."""

import json
import os
import re
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def aws(*arguments):
    result = subprocess.run(
        ["aws", *arguments, "--output", "json", "--no-cli-pager"],
        check=True, capture_output=True, text=True, timeout=45,
    )
    return json.loads(result.stdout)


def validate_config(environ):
    for key in (
        "AWS_REGION", "EC2_INSTANCE_ID", "IMAGE_REFERENCE",
        "DEPLOYMENT_URL", "EXPECTED_ENV", "EXPECTED_SHA",
    ):
        if not environ.get(key):
            raise ValueError(f"Missing required variable: {key}")
    if not re.fullmatch(
        r"[a-z0-9][a-z0-9_-]*/studyboard@sha256:[0-9a-f]{64}",
        environ["IMAGE_REFERENCE"],
    ):
        raise ValueError("IMAGE_REFERENCE must be a studyboard Docker Hub digest")
    if not re.fullmatch(r"i-[0-9a-f]{17}", environ["EC2_INSTANCE_ID"]):
        raise ValueError("Invalid EC2_INSTANCE_ID")
    if not re.fullmatch(r"[0-9a-f]{40}", environ["EXPECTED_SHA"]):
        raise ValueError("EXPECTED_SHA must be a full commit SHA")
    if environ["EXPECTED_ENV"] not in ("staging", "production"):
        raise ValueError("Invalid EXPECTED_ENV")
    url = urlsplit(environ["DEPLOYMENT_URL"])
    if url.scheme not in ("http", "https") or not url.netloc:
        raise ValueError("DEPLOYMENT_URL must be an HTTP(S) URL")


def deploy(environ):
    image = environ["IMAGE_REFERENCE"]
    instance = environ["EC2_INSTANCE_ID"]
    response = aws(
        "ssm", "send-command",
        "--instance-ids", instance,
        "--document-name", "AWS-RunShellScript",
        "--timeout-seconds", "120",
        "--parameters", json.dumps({
            "commands": [f"/usr/local/bin/studyboard-deploy '{image}'"],
            "executionTimeout": ["600"],
        }),
    )
    command_id = response["Command"]["CommandId"]
    print(f"SSM command: {command_id}; image: {image}", flush=True)
    deadline = time.monotonic() + 720
    while time.monotonic() < deadline:
        try:
            invocation = aws(
                "ssm", "get-command-invocation",
                "--command-id", command_id, "--instance-id", instance,
            )
        except subprocess.CalledProcessError as error:
            if "InvocationDoesNotExist" not in error.stderr:
                raise
            time.sleep(5)
            continue
        status = invocation["Status"]
        if status not in ("Pending", "InProgress", "Delayed", "Cancelling"):
            print(invocation.get("StandardOutputContent", ""))
            print(invocation.get("StandardErrorContent", ""))
            if status != "Success" or invocation.get("ResponseCode") != 0:
                raise RuntimeError(f"SSM deployment failed: {status}")
            return
        time.sleep(5)
    raise TimeoutError(f"SSM command {command_id} did not finish within 12 minutes")


def verify_health(environ):
    url = environ["DEPLOYMENT_URL"].rstrip("/") + "/health"
    expected = {
        "status": "ok", "database": "ok",
        "env": environ["EXPECTED_ENV"], "sha": environ["EXPECTED_SHA"],
    }
    last_error = "No health response"
    for attempt in range(18):
        try:
            with urlopen(url, timeout=10) as response:
                health = json.load(response)
                if response.status == 200 and all(
                    health.get(key) == value for key, value in expected.items()
                ):
                    print(f"Verified {url}: {json.dumps(health)}")
                    return
                last_error = f"Expected {expected}, received {health}"
        except (URLError, TimeoutError, ValueError) as error:
            last_error = str(error)
        if attempt < 17:
            time.sleep(5)
    raise RuntimeError(f"Deployment health/version verification failed: {last_error}")


def main():
    validate_config(os.environ)
    if "--health-only" not in sys.argv:
        deploy(os.environ)
    verify_health(os.environ)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        print(error.stderr, file=sys.stderr)
        raise SystemExit(error.returncode) from error
