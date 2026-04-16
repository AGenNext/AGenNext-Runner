#!/usr/bin/env python3
"""
scripts/provision_vps.py
Automates OVH VPS provisioning after purchase:
  1. Generate SSH key pair (or use existing)
  2. Register public key to OVH account via API
  3. Reinstall VPS with that SSH key baked in (Ubuntu 24.04)
  4. Wait for VPS to become ready
  5. Print SSH connection string + next steps

Usage:
  pip install ovh
  export OVH_ENDPOINT=ovh-eu
  export OVH_APPLICATION_KEY=...
  export OVH_APPLICATION_SECRET=...
  export OVH_CONSUMER_KEY=...
  export OVH_VPS_NAME=vps-xxxxxxxx.vps.ovh.net   # from OVH control panel
  python3 scripts/provision_vps.py

OVH API credentials:
  Get them at: https://eu.api.ovh.com/createToken/
  Required rights:
    GET  /me/sshKey
    GET  /me/sshKey/*
    POST /me/sshKey
    GET  /vps
    GET  /vps/*
    POST /vps/*/reinstall

After this script:
  Add SSH_PRIVATE_KEY to GitHub Secrets, then push to main.
  CI handles everything from there.
"""

import os, sys, time, subprocess, json
from pathlib import Path

# ── Dependencies ──────────────────────────────────────────────────────────────
try:
    import ovh
except ImportError:
    print("Installing ovh SDK...")
    subprocess.run([sys.executable, "-m", "pip", "install", "ovh", "--quiet"], check=True)
    import ovh

# ── Config ────────────────────────────────────────────────────────────────────
ENDPOINT    = os.environ.get("OVH_ENDPOINT",           "ovh-eu")
APP_KEY     = os.environ.get("OVH_APPLICATION_KEY",    "")
APP_SECRET  = os.environ.get("OVH_APPLICATION_SECRET", "")
CONSUMER_KEY= os.environ.get("OVH_CONSUMER_KEY",       "")
VPS_NAME    = os.environ.get("OVH_VPS_NAME",           "")
KEY_NAME    = os.environ.get("OVH_SSH_KEY_NAME",       "autonomyx-ci")
KEY_PATH    = Path(os.environ.get("OVH_SSH_KEY_PATH",  str(Path.home() / ".ssh" / "autonomyx_ci")))

# Ubuntu 24.04 LTS image ID on OVH EU
# Find available images: GET /vps/{name}/images
UBUNTU_IMAGE = os.environ.get("OVH_IMAGE_ID", "")  # set after querying available images

POLL_INTERVAL = 15   # seconds between status checks
POLL_TIMEOUT  = 600  # 10 minutes max wait


def validate_env():
    missing = []
    for var in ["OVH_APPLICATION_KEY", "OVH_APPLICATION_SECRET", "OVH_CONSUMER_KEY", "OVH_VPS_NAME"]:
        if not os.environ.get(var):
            missing.append(var)
    if missing:
        print("❌ Missing environment variables:")
        for v in missing:
            print(f"   export {v}=...")
        print("\nGet OVH API credentials at:")
        print("  https://eu.api.ovh.com/createToken/")
        print("\nRequired rights:")
        print("  GET  /me/sshKey")
        print("  GET  /me/sshKey/*")
        print("  POST /me/sshKey")
        print("  GET  /vps")
        print("  GET  /vps/*")
        print("  POST /vps/*/reinstall")
        sys.exit(1)


def get_client():
    return ovh.Client(
        endpoint=ENDPOINT,
        application_key=APP_KEY,
        application_secret=APP_SECRET,
        consumer_key=CONSUMER_KEY,
    )


def ensure_ssh_key():
    """Generate SSH key pair if it doesn't exist. Returns public key string."""
    priv = KEY_PATH
    pub  = KEY_PATH.with_suffix(".pub")

    if not priv.exists():
        print(f"  Generating SSH key pair at {priv}...")
        priv.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            "ssh-keygen", "-t", "ed25519",
            "-C", f"{KEY_NAME}@openautonomyx.com",
            "-f", str(priv),
            "-N", ""   # no passphrase — CI needs unattended access
        ], check=True, capture_output=True)
        print(f"  ✅ Key pair generated")
    else:
        print(f"  ⏭  Key already exists at {priv}")

    return pub.read_text().strip()


def register_key_with_ovh(client, public_key: str) -> str:
    """Register public key to OVH account. Returns key name."""
    # Check if already registered
    try:
        existing_keys = client.get("/me/sshKey")
        if KEY_NAME in existing_keys:
            existing = client.get(f"/me/sshKey/{KEY_NAME}")
            if existing.get("key") == public_key:
                print(f"  ⏭  SSH key '{KEY_NAME}' already registered with OVH")
                return KEY_NAME
            else:
                print(f"  ⚠️  Key '{KEY_NAME}' exists but differs — deleting and re-registering")
                client.delete(f"/me/sshKey/{KEY_NAME}")
    except Exception as e:
        print(f"  Note: {e}")

    print(f"  Registering SSH key '{KEY_NAME}' with OVH account...")
    client.post("/me/sshKey", keyName=KEY_NAME, key=public_key)
    print(f"  ✅ SSH key registered")
    return KEY_NAME


def get_ubuntu_image(client) -> str:
    """Find Ubuntu 24.04 image ID for this VPS."""
    if UBUNTU_IMAGE:
        return UBUNTU_IMAGE

    print("  Fetching available images...")
    images = client.get(f"/vps/{VPS_NAME}/images")

    ubuntu_24 = None
    for img_id in images:
        try:
            img = client.get(f"/vps/{VPS_NAME}/images/{img_id}")
            name = img.get("name", "").lower()
            if "ubuntu" in name and "24" in name:
                ubuntu_24 = img_id
                print(f"  Found: {img.get('name')} → {img_id}")
                break
        except Exception:
            continue

    if not ubuntu_24:
        print("  Available images:")
        for img_id in images[:10]:
            try:
                img = client.get(f"/vps/{VPS_NAME}/images/{img_id}")
                print(f"    {img_id}: {img.get('name', '?')}")
            except Exception:
                pass
        print("\n  Set OVH_IMAGE_ID to one of the above and re-run")
        sys.exit(1)

    return ubuntu_24


def reinstall_vps(client, image_id: str, ssh_key_name: str):
    """Reinstall VPS with Ubuntu 24.04 and SSH key."""
    print(f"  Reinstalling VPS {VPS_NAME}...")
    print(f"  Image: {image_id}")
    print(f"  SSH key: {ssh_key_name}")
    print(f"  ⚠️  This will WIPE the VPS — all existing data will be lost")

    confirm = input("  Type 'yes' to confirm reinstall: ").strip().lower()
    if confirm != "yes":
        print("  Cancelled.")
        sys.exit(0)

    result = client.post(
        f"/vps/{VPS_NAME}/reinstall",
        imageId=image_id,
        sshKey=[ssh_key_name],
        language="en",
    )
    print(f"  ✅ Reinstall started: {result}")


def wait_for_ready(client) -> str:
    """Poll VPS status until running. Returns VPS IP."""
    print(f"\n  Waiting for VPS to become ready (up to {POLL_TIMEOUT//60} minutes)...")
    start = time.time()
    last_status = None

    while time.time() - start < POLL_TIMEOUT:
        try:
            vps = client.get(f"/vps/{VPS_NAME}")
            status = vps.get("state", "unknown")
            ip     = vps.get("netbootMode", "")

            # Get IP from VPS info
            try:
                ips = client.get(f"/vps/{VPS_NAME}/ips")
                ipv4 = [ip for ip in ips if "." in str(ip)]
                vps_ip = ipv4[0] if ipv4 else "unknown"
            except Exception:
                vps_ip = "unknown"

            if status != last_status:
                elapsed = int(time.time() - start)
                print(f"  [{elapsed:3d}s] Status: {status}")
                last_status = status

            if status == "running":
                print(f"  ✅ VPS is ready")
                return vps_ip

        except Exception as e:
            print(f"  API error: {e}")

        time.sleep(POLL_INTERVAL)

    print(f"  ❌ Timeout waiting for VPS after {POLL_TIMEOUT//60} minutes")
    sys.exit(1)


def print_next_steps(vps_ip: str):
    private_key = str(KEY_PATH)
    pub_key_content = KEY_PATH.with_suffix(".pub").read_text().strip()

    print("""
══════════════════════════════════════════════════════════
  VPS provisioned and ready
══════════════════════════════════════════════════════════
""")
    print(f"  IP:       {vps_ip}")
    print(f"  SSH:      ssh -i {private_key} root@{vps_ip}")
    print(f"  Key:      {private_key}")
    print("""
  Next steps:
  1. Add SSH_PRIVATE_KEY to GitHub Secrets:
     gh secret set SSH_PRIVATE_KEY \\
       --repo OpenAutonomyx/autonomyx-model-gateway \\
       < """ + private_key + """

  2. Add all API key secrets (see docs/github-secrets.md)

  3. Push to main — CI bootstraps + deploys everything:
     git commit --allow-empty -m "trigger: initial deploy"
     git push origin main

  4. Monitor at:
     https://github.com/OpenAutonomyx/autonomyx-model-gateway/actions
══════════════════════════════════════════════════════════
""")
    print(f"  Public key (for reference):\n  {pub_key_content}\n")


def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     Autonomyx — OVH VPS Provisioning                    ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    validate_env()

    client = get_client()

    # Verify credentials
    try:
        me = client.get("/me")
        print(f"✅ OVH API authenticated as: {me.get('nichandle')} ({me.get('email')})\n")
    except Exception as e:
        print(f"❌ OVH API authentication failed: {e}")
        sys.exit(1)

    print("── Step 1/4: SSH key ────────────────────────────────────")
    public_key = ensure_ssh_key()
    register_key_with_ovh(client, public_key)
    print()

    print("── Step 2/4: Ubuntu 24.04 image ─────────────────────────")
    image_id = get_ubuntu_image(client)
    print()

    print("── Step 3/4: Reinstall VPS ──────────────────────────────")
    reinstall_vps(client, image_id, KEY_NAME)
    print()

    print("── Step 4/4: Wait for ready ─────────────────────────────")
    vps_ip = wait_for_ready(client)
    print()

    print_next_steps(vps_ip)


if __name__ == "__main__":
    main()
