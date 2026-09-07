# -*- coding: utf-8 -*-
"""One-command deploy of the Munjiz workflows into the running n8n container.

    python tools/deploy.py            # import, activate, bind credentials, seed
    python tools/deploy.py --split    # deploy the 10-file granular set instead

Run it AFTER you have created the n8n owner account at http://localhost:<port>
(n8n does not register webhooks on an instance that has not been set up).

Never touches credentials: the Gemini key is entered by you in the n8n UI and
stays encrypted inside the n8n_data volume. There is no other credential - the
datastore is n8n's own Data Tables, provisioned by this script.
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
SPLIT_DIR = os.path.join(ROOT, "workflow-split")

# Two interchangeable sets. Import ONE: they publish the same webhook paths, so
# having both active at once makes n8n serve whichever registered first.


def wf_ids_in(d):
    """Read the ids out of the workflow files themselves rather than repeating them
    here. A hardcoded list silently went stale once 08 Reflection and 09 Patch Review
    were added: --split activated only 8 of the 10, and a merged deploy left those two
    behind as duplicate handlers for /munjiz/reflect and /munjiz/patch."""
    ids = []
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(d, fn), encoding="utf-8") as f:
            wid = json.load(f).get("id")
        if wid and wid not in ids:
            ids.append(wid)
    return ids


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


# The datastore is n8n's own Data Tables, so Gemini is the only credential.
CRED_TYPES = {
    "googlePalmApi": "Google Gemini (AI Studio)",
}


def read_credentials(container, workdir):
    """Map credential type -> (id, name) by reading n8n's own database.

    Only ids/types/names are read; the secret payload stays encrypted and is
    never touched. Lets the deploy point every node at the credentials you
    created in the UI, instead of you selecting them node by node.
    """
    dbfile = os.path.join(workdir, "n8n.sqlite")
    p = subprocess.run(["docker", "cp", "%s:/home/node/.n8n/database.sqlite" % container, dbfile],
                       capture_output=True, text=True)
    if p.returncode != 0 or not os.path.exists(dbfile):
        return {}
    try:
        import sqlite3
        con = sqlite3.connect(dbfile)
        rows = con.execute("SELECT id, type, name FROM credentials_entity").fetchall()
        con.close()
    except Exception:
        return {}
    out = {}
    for cid, ctype, cname in rows:
        out.setdefault(ctype, (cid, cname))  # first of each type wins
    return out


def wire_credentials(doc, creds):
    """Point every node's credential reference at the real credential id."""
    hits = 0
    for node in doc.get("nodes", []):
        for ctype, ref in (node.get("credentials") or {}).items():
            if ctype in creds:
                cid, cname = creds[ctype]
                if ref.get("id") != cid:
                    ref["id"], ref["name"] = cid, cname
                    hits += 1
    return hits


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
    ap.add_argument("--no-seed", action="store_true",
                    help="skip provisioning/seeding the data tables")
    ap.add_argument("--container", default="munjiz-n8n")
    ap.add_argument("--port", default=None)
    ap.add_argument("--skip-owner-check", action="store_true")
    ap.add_argument("--split", action="store_true",
                    help="import the 10-file granular set instead of the merged 4-file set")
    a = ap.parse_args()
    port = a.port or env_port()
    src_dir = SPLIT_DIR if a.split else WORKFLOW_DIR
    want_ids = wf_ids_in(src_dir)
    stale_ids = [w for w in wf_ids_in(WORKFLOW_DIR if a.split else SPLIT_DIR)
                 if w not in want_ids]

    print("== Munjiz deploy ==")
    print("set: %s/%d (%s)" % ("split" if a.split else "merged",
                               len(want_ids), os.path.basename(src_dir)))
    print("container: %s | n8n port: %s" % (a.container, port))

    if not wait_healthy(port):
        print("!! n8n is not answering on :%s — start it with:  docker compose -f docker/docker-compose.yml up -d" % port)
        sys.exit(1)
    print("-> n8n healthy")

    if not a.skip_owner_check and not owner_exists(port):
        print("")
        print("!! No owner account yet. Open http://localhost:%s, create the owner" % port)
        print("   account (email + password of your choosing), then re-run this script.")
        print("   n8n does not register webhooks until the instance is set up.")
        sys.exit(2)

    # 1. stage the workflows: substitute the sheet id and bind real credentials
    tmp = tempfile.mkdtemp(prefix="munjiz-deploy-")
    creds = read_credentials(a.container, tmp)
    missing = [t for t in CRED_TYPES if t not in creds]
    if creds:
        print("-> credentials in n8n: %s" % ", ".join(sorted(creds)))
    if missing:
        print("   missing credential types: %s" % ", ".join(missing))
        print("   (create them in the n8n UI; re-run and every node is bound automatically)")

    staged, cred_hits = 0, 0
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith(".json"):
            continue
        text = open(os.path.join(src_dir, fn), encoding="utf-8").read()
        doc = json.loads(text)
        cred_hits += wire_credentials(doc, creds)
        with open(os.path.join(tmp, fn), "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        staged += 1
    print("-> staged %d workflows (%d credential refs bound)" % (staged, cred_hits))

    # 2. copy into the container and import (stable ids => updates in place, no duplicates)
    # Unique destination per run: docker cp writes as root while the container
    # runs as `node`, so cleaning a shared staging dir fails silently and the
    # import would keep reading whatever was there before.
    dest = "/tmp/" + os.path.basename(tmp)
    run(["docker", "cp", tmp, "%s:%s" % (a.container, dest)], quiet=True)
    listing = run(["docker", "exec", a.container, "sh", "-c", "ls %s/*.json | wc -l" % dest],
                  check=False, quiet=True)
    print("-> importing %s file(s) from %s" % (listing.stdout.strip() or "?", dest))
    run(["docker", "exec", a.container, "n8n", "import:workflow",
         "--separate", "--input=" + dest])
    run(["docker", "exec", "-u", "root", a.container, "rm", "-rf", dest], check=False, quiet=True)

    # 3. activate every workflow.
    #    On n8n 2.x a sub-workflow must ALSO be active or its caller fails with
    #    "Workflow is not active and cannot be executed" — so 00 Data IO and
    #    02 Service Gateway are activated too, not just the trigger workflows.
    # retire the other set first so its webhook paths stop competing
    for wid in stale_ids:
        run(["docker", "exec", a.container, "n8n", "update:workflow",
             "--id=" + wid, "--active=false"], check=False, quiet=True)
    if stale_ids:
        print("-> deactivated %d workflow(s) from the other set" % len(stale_ids))

    all_ids = want_ids
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

    if not a.no_seed:
        print("-> provisioning data tables (create + clear + seed)")
        try:
            req = urllib.request.Request(
                "http://localhost:%s/webhook/munjiz/reset" % port,
                data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=180) as r:
                print("   %s" % r.read(120).decode("utf-8", "replace").strip())
        except Exception as e:
            print("   !! seeding failed: %s (run it later from the portal's reset button)" % e)

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
            print("Add the Google Gemini credential in the n8n UI, then re-run.")
            print("See n8n -> Executions for the failing node.")
    except urllib.error.HTTPError as e:
        print("-> webhook responded HTTP %s (workflow reached, likely missing credentials)" % e.code)
        print("   add the Google Gemini credential in the n8n UI, then retry")
    except Exception as e:
        print("!! webhook not reachable: %s" % e)
        print("   check that workflow 05 shows as Active in the n8n UI")


if __name__ == "__main__":
    main()
