#!/usr/bin/env python3
"""
make_autoinstall_iso.py
---------------------------------
Creates a custom Ubuntu Server autoinstall ISO that automatically:
 - Configures DHCP on eth0
 - Injects a custom SSH public key
 - Sets a predefined or user-supplied password
 - Embeds a given autoinstall.yaml file
 - Works on Arch Linux or Ubuntu-based hosts

Usage example:
    sudo ./make_autoinstall_iso.py \
        ubuntu-22.04.5-live-server-amd64.iso \
        autoinstall.yaml \
        --ssh-key ~/.ssh/id_rsa.pub \
        --password 'MyPassword123' \
        my-autoinstall.iso
"""

import argparse
import crypt
import getpass
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

# -------------------------------------------------------------
# Helper function: execute shell commands safely and verbosely
# -------------------------------------------------------------


def run(cmd, cwd=None):
    """Run a command and stop if it fails."""
    print(f"[+] Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

# -------------------------------------------------------------
# Detect the correct syslinux bootloader binary (isohdpfx.bin)
# -------------------------------------------------------------


def detect_isohdpfx_path():
    """
    Try to locate the 'isohdpfx.bin' file.
    This file is required to make the new ISO bootable.
    """
    candidates = [
        "/usr/lib/ISOLINUX/isohdpfx.bin",          # Ubuntu/Debian
        "/usr/lib/syslinux/bios/isohdpfx.bin",     # Arch Linux
        "/usr/share/syslinux/isohdpfx.bin"         # Fallback
    ]
    for path in candidates:
        if Path(path).exists():
            print(f"[+] Using isohdpfx.bin from: {path}")
            return path
    raise FileNotFoundError(
        "Could not find 'isohdpfx.bin'. Install syslinux or check your distro path."
    )

# -------------------------------------------------------------
# Load the SSH public key for injection into the autoinstall file
# -------------------------------------------------------------


def load_ssh_key(ssh_key_file):
    """Read and return the contents of a .pub SSH key file."""
    key_path = Path(ssh_key_file)
    if not key_path.exists():
        raise FileNotFoundError(f"SSH key file not found: {ssh_key_file}")
    key_content = key_path.read_text().strip()
    print(f"[+] Loaded SSH key from {key_path}")
    return key_content

# -------------------------------------------------------------
# Securely hash a password using SHA-512 for Ubuntu autoinstall
# -------------------------------------------------------------


def get_password_hash(password=None):
    """
    Return a SHA-512 password hash.
    If no password is provided, prompt the user securely.
    """
    if not password:
        password = getpass.getpass("[?] Enter password for autoinstall user: ")
        confirm = getpass.getpass("[?] Confirm password: ")
        if password != confirm:
            raise ValueError("Passwords do not match.")
    hashed = crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))
    print("[+] Password hashed successfully")
    return hashed

# -------------------------------------------------------------
# Modify the autoinstall.yaml file:
#  - Inject SSH key
#  - Inject hashed password
#  - Force DHCP on eth0
# -------------------------------------------------------------


def inject_credentials_and_network(autoinstall_yaml, ssh_key, password_hash):
    """Patch autoinstall.yaml to include credentials and DHCP config."""
    with open(autoinstall_yaml, "r") as f:
        data = yaml.safe_load(f)

    ai = data.get("autoinstall", {})
    identity = ai.get("identity", {})
    username = identity.get("username", "ubuntu")
    hostname = identity.get("hostname", "autoinstall-node")

    # Insert username, hostname, and password
    ai["identity"] = {
        "hostname": hostname,
        "username": username,
        "password": password_hash
    }

    # Add SSH configuration
    ai["ssh"] = {
        "install-server": True,
        "authorized-keys": [ssh_key]
    }

    # Force Ethernet DHCP so the node auto-registers on LAN
    ai["network"] = {
        "network": {
            "version": 2,
            "ethernets": {
                "eth0": {
                    "dhcp4": True,
                    "dhcp6": False
                }
            }
        }
    }

    data["autoinstall"] = ai

    # Write the modified file to a temporary location
    temp_yaml = Path(tempfile.mktemp(prefix="user-data-", suffix=".yaml"))
    with open(temp_yaml, "w") as f:
        yaml.dump(data, f, sort_keys=False)

    print(f"[+] Credentials and DHCP config injected into: {temp_yaml}")
    return temp_yaml

# -------------------------------------------------------------
# Main logic: ISO extraction, injection, and rebuild
# -------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Create a custom Ubuntu Server autoinstall ISO with DHCP, SSH key, and password."
    )
    parser.add_argument(
        "source_iso", help="Path to the source Ubuntu Server ISO")
    parser.add_argument("autoinstall_yaml",
                        help="Path to the base autoinstall.yaml file")
    parser.add_argument("--ssh-key", required=True,
                        help="Path to SSH public key (.pub)")
    parser.add_argument(
        "--password", help="Password for autoinstall user (optional)")
    parser.add_argument(
        "output_iso",
        nargs="?",
        default="autoinstall-server.iso",
        help="Output ISO filename (default: autoinstall-server.iso)"
    )
    args = parser.parse_args()

    # Resolve file paths
    source_iso = Path(args.source_iso).resolve()
    autoinstall_yaml = Path(args.autoinstall_yaml).resolve()
    ssh_key_file = Path(args.ssh_key).resolve()
    output_iso = Path(args.output_iso).resolve()

    # Sanity checks
    if not source_iso.exists():
        raise FileNotFoundError(f"Source ISO not found: {source_iso}")
    if not autoinstall_yaml.exists():
        raise FileNotFoundError(
            f"Autoinstall YAML not found: {autoinstall_yaml}")
    if not ssh_key_file.exists():
        raise FileNotFoundError(f"SSH key file not found: {ssh_key_file}")

    # Load configuration components
    ssh_key = load_ssh_key(ssh_key_file)
    password_hash = get_password_hash(args.password)
    new_yaml = inject_credentials_and_network(
        autoinstall_yaml, ssh_key, password_hash)
    isohdpfx_path = detect_isohdpfx_path()

    # Create temporary working directories
    work_dir = Path(tempfile.mkdtemp(prefix="autoinstall_build_"))
    iso_mount = work_dir / "iso_mount"
    iso_extract = work_dir / "iso_extract"

    try:
        iso_mount.mkdir()
        iso_extract.mkdir()

        # Mount the source ISO
        run(["sudo", "mount", "-o", "loop", str(source_iso), str(iso_mount)])

        # Copy its contents to a writable directory
        run(["rsync", "-a", str(iso_mount) + "/", str(iso_extract) + "/"])

        # Unmount the ISO after copying
        run(["sudo", "umount", str(iso_mount)])

        # Create the autoinstall directory and copy config
        autoinstall_dir = iso_extract / "autoinstall"
        autoinstall_dir.mkdir(exist_ok=True)
        shutil.copy(new_yaml, autoinstall_dir / "user-data")

        # Meta-data file required for NoCloud datasource
        with open(autoinstall_dir / "meta-data", "w") as f:
            f.write("instance-id: autoinstall\nlocal-hostname: autoinstall\n")

        # Modify boot configs to trigger autoinstall automatically
        for cfg_path in [
            iso_extract / "boot/grub/grub.cfg",
            iso_extract / "isolinux/txt.cfg"
        ]:
            if cfg_path.exists():
                text = cfg_path.read_text()
                new_text = text.replace(
                    "quiet ---",
                    "autoinstall ds=nocloud\\;s=/cdrom/autoinstall/ quiet ---"
                )
                cfg_path.write_text(new_text)
                print(f"[+] Modified {cfg_path}")

        # Finally, rebuild the ISO with xorriso
        print("[+] Creating new ISO...")
        run([
            "xorriso",
            "-as", "mkisofs",
            "-r",
            "-V", "Ubuntu-Autoinstall",
            "-o", str(output_iso),
            "-J",
            "-l",
            "-cache-inodes",
            "-isohybrid-mbr", isohdpfx_path,
            "-b", "isolinux/isolinux.bin",
            "-c", "isolinux/boot.cat",
            "-no-emul-boot",
            "-boot-load-size", "4",
            "-boot-info-table",
            "--eltorito-alt-boot",
            "-e", "boot/grub/efi.img",
            "-no-emul-boot",
            str(iso_extract)
        ])

        print(f"\n✅ ISO created successfully: {output_iso}\n")

    finally:
        # Always clean up the temporary directories, even on failure
        shutil.rmtree(work_dir, ignore_errors=True)


# -------------------------------------------------------------
# Entrypoint
# -------------------------------------------------------------
if __name__ == "__main__":
    main()
