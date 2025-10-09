Perfect 👍 — here’s a clear and professional `README.md` you can include alongside your script.
It documents **installation**, **usage**, **example commands**, and **troubleshooting tips**, all tailored for your Arch Linux setup.

---

## 🧾 `README.md`

# Ubuntu Server Autoinstall ISO Builder

This tool creates a **custom Ubuntu Server autoinstall ISO** that can automatically install and configure Ubuntu with minimal user interaction.

It allows you to:

* Automatically configure **networking via DHCP**
* Inject your **SSH public key** for secure login
* Set a **custom password** for the default user
* Embed a custom `autoinstall.yaml` into the ISO
* Build on **Arch Linux** or **Ubuntu/Debian**

---

## ⚙️ Features

* ✅ Automatically detects the correct `isohdpfx.bin` path (Arch or Ubuntu)
* ✅ Configures DHCP on `eth0` automatically
* ✅ Injects a provided SSH key and password hash
* ✅ Includes all base Kubernetes and Docker dependencies in your autoinstall file
* ✅ Produces a **bootable hybrid ISO** ready for USB or PXE installation

---

## 🧩 Requirements

### On **Arch Linux**:

```bash
sudo pacman -S --needed xorriso syslinux rsync python-yaml
```

### On **Ubuntu/Debian**:

```bash
sudo apt update
sudo apt install xorriso syslinux rsync python3-yaml
```

---

## 🧰 Usage

### Basic Command

```bash
sudo ./make_autoinstall_iso.py \
    /path/to/ubuntu-22.04.5-live-server-amd64.iso \
    /path/to/autoinstall.yaml \
    --ssh-key ~/.ssh/id_rsa.pub
```

### With a Custom Password and Output Name

```bash
sudo ./make_autoinstall_iso.py \
    ubuntu-22.04.5-live-server-amd64.iso \
    autoinstall.yaml \
    --ssh-key ~/.ssh/id_ed25519.pub \
    --password 'MySecurePass123' \
    my-autoinstall.iso
```

### Parameters

| Flag               | Description                                                                | Required |
| ------------------ | -------------------------------------------------------------------------- | -------- |
| `source_iso`       | Path to the official Ubuntu Server ISO to modify                           | ✅        |
| `autoinstall_yaml` | Base YAML configuration file to use                                        | ✅        |
| `--ssh-key`        | Path to your public SSH key (`.pub` file)                                  | ✅        |
| `--password`       | Optional password for the default user (if omitted, prompts interactively) | ❌        |
| `output_iso`       | Name of the resulting ISO (default: `autoinstall-server.iso`)              | ❌        |

---

## 🗂️ Example `autoinstall.yaml`

This is the **base YAML** that the script modifies automatically
(so you don’t need to manually edit passwords, SSH keys, or network settings).

```yaml
#cloud-config
autoinstall:
  version: 1
  identity:
    hostname: kube-node
    username: ubuntu
  keyboard:
    layout: us
  locale: en_US.UTF-8
  storage:
    layout:
      name: lvm
  packages:
    - vim
    - htop
    - curl
    - docker.io
    - kubelet
    - kubeadm
    - kubectl
  late-commands:
    - curtin in-target --target=/target -- systemctl enable docker
    - curtin in-target --target=/target -- systemctl start docker
    - curtin in-target --target=/target -- apt-mark hold kubelet kubeadm kubectl
```

🧠 The script will automatically:

* Inject your **SSH public key**
* Add your **password hash**
* Replace the network section with a **DHCP configuration**

---

## 💽 Output

When the build completes, you’ll see:

```
✅ ISO created successfully: /path/to/autoinstall-server.iso
```

You can then flash it to a USB drive using:

```bash
sudo dd if=autoinstall-server.iso of=/dev/sdX bs=4M status=progress
```

Or mount it in your virtualization software (e.g., Proxmox, VirtualBox, or VMware).

---

## 🧑‍💻 Tips for Use in a Lab or Cluster

* You can reuse the same ISO for all servers — each one will request an IP via DHCP.
* To identify machines easily, rename hostnames post-install (or dynamically during install using cloud-init templating if desired).
* The servers will come up with:

  * SSH enabled
  * Your key preinstalled
  * Docker + Kubernetes tools ready to go

---

## 🧯 Troubleshooting

| Issue                                       | Cause / Fix                                                                                         |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `isohdpfx.bin not found`                    | Install `syslinux` and ensure the file exists in `/usr/lib/syslinux/bios/`                          |
| `Permission denied while mounting ISO`      | Run the script with `sudo`                                                                          |
| `ModuleNotFoundError: No module named yaml` | Install `python-yaml` (Arch) or `python3-yaml` (Debian/Ubuntu)                                      |
| `boot menu doesn’t auto-install`            | Ensure `autoinstall` and `ds=nocloud` strings were correctly injected into `grub.cfg` and `txt.cfg` |

---

## 🧰 Project Structure

```
autoinstall-builder/
├── make_autoinstall_iso.py
├── README.md
├── autoinstall.yaml
└── id_rsa.pub
```

---

## 🏁 License

MIT License — you are free to modify and redistribute this script.
