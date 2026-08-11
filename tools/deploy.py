# -*- coding: utf-8 -*-
"""One-command deploy of the Munjiz workflows into the running n8n container.

    python tools/deploy.py                          # import + publish as-is
    python tools/deploy.py --spreadsheet-id <ID>    # also wire the Google Sheet

Run it AFTER you have created the n8n owner account at http://localhost:<port>
(n8n does not register webhooks on an instance that has not been set up).

Never touches credentials: the Gemini / Sheets / Gmail keys are entered by you in
the n8n UI and stay encrypted inside the n8n_data volume.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_DIR = os.path.join(ROOT, "workflow")
PLACEHOLDER = "REPLACE_WITH_SPREADSHEET_ID"


def run(args, check=True, quiet=False):
    """subprocess with a list argv — no shell, so Git Bash never rewrites /container/paths."""
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not quiet and p.stdout.strip():
        print("   " + p.stdout.strip().replace("\n", "\n   "))
    if check and p.returncode != 0:
        print("!! command failed: %s" % " ".join(args))
        if p.stderr.strip():
            print("   " + p.stderr.strip().replace("\n", "\n   "))
        sys.exit(1)
    return p


def env_port(default="5678"):
    envf = os.path.join(ROOT, "docker", ".env")
    if os.path.exists(envf):
        for line in open(envf, encoding="utf-8"):
            if line.strip().startswith("N8N_PORT="):
                return line.split("=", 1)[1].strip()
    return default


def wait_healthy(port, timeout=180):
    url = "http://localhost:%s/healthz" % port
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def owner_exists(port):
    """False while n8n still shows the first-run setup screen."""
    try:
        with urllib.request.urlopen("http://localhost:%s/rest/settings" % port, timeout=10) as r:
            data = json.load(r).get("data", {})
        return not data.get("userManagement", {}).get("showSetupOnFirstLoad", True)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spreadsheet-id", default=None,
                    help="Google Sheet id of your Munjiz Registry (replaces %s)" % PLACEHOLDER)
    ap.add_argument("--container", default="munjiz-n8n")
    ap.add_argument("--port", default=None)
    ap.add_argument("--skip-owner-check", action="store_true")
    a = ap.parse_args()
    port = a.port or env_port()

    print("== Munjiz deploy ==")
    print("container: %s | n8n port: %s" % (a.container, port))

    if not wait_healthy(port):
        print("!! n8n is not answering on :%s — start it with:  cd docker && docker compose up -d" % port)
        sys.exit(1)
    print("-> n8n healthy")

    if not a.skip_owner_check and not owner_exists(port):
        print("")
        print("!! No owner account yet. Open http://localhost:%s, create the owner" % port)
        print("   account (email + password of your choosing), then re-run this script.")
        print("   n8n does not register webhooks until the instance is set up.")
        sys.exit(2)

    # 1. stage the workflows, substituting the only remaining placeholder
    tmp = tempfile.mkdtemp(prefix="munjiz-deploy-")
    staged, wired = 0, 0
    for fn in sorted(os.listdir(WORKFLOW_DIR)):
        if not fn.endswith(".json"):
            continue
        text = open(os.path.join(WORKFLOW_DIR, fn), encoding="utf-8").read()
        if a.spreadsheet_id and PLACEHOLDER in text:
            text = text.replace(PLACEHOLDER, a.spreadsheet_id)
            wired += 1
        open(os.path.join(tmp, fn), "w", encoding="utf-8").write(text)
        staged += 1
    print("-> staged %d workflows%s" % (staged, " (sheet id wired into %d)" % wired if wired else ""))
    if not a.spreadsheet_id:
        print("   note: no --spreadsheet-id given; Sheets nodes keep the placeholder")

    # 2. copy into the container and import (stable ids => updates in place, no duplicates)
    run(["docker", "exec", a.container, "rm", "-rf", "/tmp/munjiz-deploy"], check=False, quiet=True)
    run(["docker", "cp", tmp, "%s:/tmp/munjiz-deploy" % a.container], quiet=True)
    print("-> importing")
    run(["docker", "exec", a.container, "n8n", "import:workflow",
         "--separate", "--input=/tmp/munjiz-deploy"])

    # 3. activate every workflow.
    #    On n8n 2.x a sub-workflow must ALSO be active or its caller fails with
    #    "Workflow is not active and cannot be executed" — so 00 Data IO and
    #    02 Service Gateway are activated too, not just the trigger workflows.
    all_ids = ["munjizDataIo0000", "munjizChatAgent1", "munjizGateway002",
               "munjizApprovals3", "munjizSlaChaser4", "munjizDashApi005",
               "munjizErrorHnd06", "munjizDemoReset7"]
    for wid in all_ids:
        run(["docker", "exec", a.container, "n8n", "publish:workflow", "--id=" + wid],
            check=False, quiet=True)
        run(["docker", "exec", a.container, "n8n", "update:workflow",
             "--id=" + wid, "--active=true"], check=False, quiet=True)
    print("-> activated all %d workflows (sub-workflows included)" % len(all_ids))

    # 4. restart so the activation takes effect, then verify the plumbing
    print("-> restarting n8n")
    run(["docker", "restart", a.container], quiet=True)
    if not wait_healthy(port):
        print("!! n8n did not come back up")
        sys.exit(1)

    shutil.rmtree(tmp, ignore_errors=True)
    url = "http://localhost:%s/webhook/munjiz/state" % port
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            body = r.read(300).decode("utf-8", "replace")
        print("-> GET /webhook/munjiz/state : HTTP %s" % r.status)
        print("")
        if body.strip():
            print("   %s" % body[:200])
            print("READY. Portal: http://localhost:%s" % (os.environ.get("PORTAL_PORT") or "8080"))
        else:
            print("Workflows are live, but the response body is empty: the workflow ran and")
            print("stopped before responding - almost always a missing credential.")
            print("Add the Gemini / Sheets / Gmail credentials in the n8n UI (and pass")
            print("--spreadsheet-id), then re-run. See n8n -> Executions for the failing node.")
    except urllib.error.HTTPError as e:
        print("-> webhook responded HTTP %s (workflow reached, likely missing credentials)" % e.code)
        print("   add the Gemini / Sheets / Gmail credentials in the n8n UI, then retry")
    except Exception as e:
        print("!! webhook not reachable: %s" % e)
        print("   check that workflow 05 shows as Active in the n8n UI")


if __name__ == "__main__":
    main()
