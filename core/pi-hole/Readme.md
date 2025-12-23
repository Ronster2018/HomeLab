# Pi-hole Home Server Project

A simple reference guide on how I deployed **Pi-hole** as my DNS server on a home Kubernetes cluster, using **MetalLB** as the load balancer and an **Eero** router in bridged mode.

---

## Overview

This project deploys:

* **Pi-hole** as a DNS server running in Kubernetes
* **MetalLB** to provide a LoadBalancer IP on a bare‑metal/home network
* A home router (**Eero**) configured in **Bridged Mode** with DNS pointed at Pi-hole’s load balancer IP

Your cluster network is configured with a dedicated MetalLB IP pool:

```
192.168.4.200–250
```

---

## 🧰 Requirements

* A functioning Kubernetes cluster (home lab)
* MetalLB installed
* Pi-hole Deployment, Service, and PVC manifests applied
* Router set to Bridged mode
* Router DNS pointed to the Pi-hole LoadBalancer IP

---

## 📡 Install MetalLB

MetalLB provides a **LoadBalancer** IP on a home network.

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.3/config/manifests/metallb-native.yaml
```

After installation, configure an `IPAddressPool` using your chosen range:

```
192.168.4.200–250
```

---

## 🧩 Deploy Pi-hole

Apply all of the manifest files with the following command:
```bash
kubectl apply -f pi-hole/
```

Once the manifests are applied (Deployment, Service, PVC, ConfigMap, etc.):

```bash
kubectl -n pi-hole get pods,svc,pvc
```

There will be two services. One service of type `ClusterIP` that exposes ports `80` and `443` for web traffic, and the other for DNS lookup traffic via port `53`. This second service is of type `LoadBalancer`. This is given a static IP address on the local network for local DNS resolution.

Point your router DNS settings to that LoadBalancer IP.

---

## 🌐 Home Network Configuration

🏠 Local Domain Configuration (home.arpa) for Pi-hole + Eero

This section covers a crucial network configuration step required to ensure reliable local DNS resolution when using Pi-hole as the LAN DNS server while Eero remains in Router Mode.

Without this change, Pi-hole may be unable to resolve local hostnames (e.g., http://pi-hole/) and gravity updates may fail due to DNS resolution issues.

### Why You Must Use home.arpa

Multicast .local is reserved for mDNS and should not be used as an authoritative DNS domain on your LAN.
Instead, the IETF reserved home.arpa specifically for private home networks.

Using home.arpa avoids:
- Conflicts with mDNS
- Conflicts with VPNs and corporate DNS
- Broken local DNS lookups
- Pi-hole gravity update failures

> Note: This applications web traffic relies on a `Traefik` IngressRoute to be installed and configured. Whereas the DNS portion relies on `MetalLB` to be installed and configured.
---

# Configure Pi-hole with `home.arpa`

### **1. Log into Pi-hole Admin**

Open Pi-hole web UI:
```
http://<pi-hole-ip>/admin
```

### **2. Go to DNS Settings**

Navigate to:
**Settings All → DNS**

May have to toggle the BASIC settings switch to view hidden settings.

Find the field labeled **“DNS Domain Name”** (sometimes shown as `dns.domain.name`).

### **3. Set Local Domain fron `lan` to `home.arpa`**

Change the domain name to:
```
home.arpa
```

Save the settings.

### **4. Add a Local DNS Record for Pi-hole**

Still in the Pi-hole UI:

**Local DNS → DNS Records → Add New Record**

| Field      | Value                           |
| ---------- | ------------------------------- |
| Domain     | `pihole.home.arpa`             |
| IP Address | `192.168.x.x` (Your Traefik LoadBalancedIP) |

Example:

```
pi-hole.home.arpa -> 192.168.4.202
```

Click **Add**.

### Verification

#### **1. Test DNS resolution from any device**

Open a terminal:
```bash
nslookup pihole.home.arpa
```

Expected:
```
Name:    pihole.home.arpa
Address:  192.168.4.202
```

#### **2. Access the Pi-hole UI**
Navigate to:
```
http://pihole.home.arpa/admin
```
#### **3. Check Pi-hole Gravity Update**

On the Pi-hole device:
```bash
pihole -g
```

The update should run without the error `DNS resolution is currently unavailable`. This ensures all local devices use Pi-hole for DNS filtering.

## Troubleshooting
While setting up the deployment, **and rolling out changes**, I came across an error in the logs
```bash
ERROR: Cannot read gravity database at /etc/pihole/gravity.db - file does not exist or is not readable
```

This seems to be an issue when`gravity.db` is missing. This happened due to using `emptyDir` as my storage option. My changes were wiped out since the pod was removed. I decided to set up a PV and a PVC with the intention of updating it to use TrueNas as the persistent storage NFS solution.

Steps taken were as follows:
- Connect to the pod and check the mounted directory for `gravity.db`
```bash
kubectl -n pi-hole exec -it pi-hole-XXXXXX -- bash
ls -l /etc/pi-hole
```

- After reviewing the filesystem, I noticed that `gravity.db` was not present. I modified the `yaml` and added a PV and a PVC that will use the `volumeMode: Filesystem` parameter and also inclided `hostPath` to mount at `/mnt/data/pihole` to use this directory on the node as a temporary solution.

- To fix the issue of the missing `gravity.db` file
```bash
kubectl -n pi-hole exec -it pi-hole-XXXX -- pihole -g

# Error with DNS?
pihole refreshdns

# Error with DNS resolution/
sudo vi /etc/resolv.conf
# view where the nameserver is pointing and edit as needed. I added the following
#nameserver 10.96.0.10
#nameserver 192.168.4.201
#nameserver 8.8.8.8
```




## Next steps
- Add a separate admin UI LoadBalancer IP
- Add health checks
- Add automatic backup scripts (to NAS or Git)
- External Secrets Provider