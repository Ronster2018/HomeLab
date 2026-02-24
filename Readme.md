Note: Get all resources

```bash
# Source - https://stackoverflow.com/a
# Posted by rcorre, modified by community. See post 'Timeline' for change history
# Retrieved 2025-11-21, License - CC BY-SA 4.0

kubectl api-resources --verbs=list --namespaced -o name \
  | xargs -n 1 kubectl get --show-kind --ignore-not-found -l <label>=<value> -n <namespace>
```

Items installed
Metric Server
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

# Base Applications
- ✅ MetalLB
- ✅ Traefik
  - ✅ Pi-Hole for DNS (relies on Traefik)
- 🚧 Step CA (Holds Intermediate CA private key)
- 🚧 Cert Manager(?)
- 🚧 Metric Server

# Base Configurations
- Core DNS
- Calico (CNI)


---
# Setting up stroage
Below is a **clear, click-by-click TrueNAS SCALE guide** for creating a **Zvol** and exposing it via **iSCSI** for Kubernetes (PostgreSQL / Paperless use case).

> Assumes **TrueNAS SCALE** (not CORE) and a **single-node or small K8s cluster**

---

# ✅ Part 1: Create the Zvol (Block Device)

## Step 1️⃣ Open Datasets

1. Log into **TrueNAS Web UI**
2. Go to **Storage → Datasets**
3. Expand your pool (example: `TrueNAS`)

---

## Step 2️⃣ Create Zvol

1. Click **Add Zvol**
2. Fill in:

| Field           | Value                     |
| --------------- | ------------------------- |
| **Zvol Name**   | `postgres-paperless`      |
| **Size**        | `10 GiB` (or more)        |
| **Block Size**  | `16K` ✅                   |
| **Sparse**      | Optional (ON saves space) |
| **Compression** | LZ4 (default)             |
| **Sync**        | STANDARD                  |
| **Read-only**   | OFF                       |

3. Click **Save**

📍 Resulting path:

```
/dev/zvol/TrueNAS/postgres-paperless
```

---

# ✅ Part 2: Enable iSCSI Service

## Step 3️⃣ Enable iSCSI

1. Go to **System Settings → Services**
2. Toggle **iSCSI → ON**
3. Set **Start Automatically**

---

# ✅ Part 3: Create iSCSI Resources

You must create **5 objects**:

1. Portal
2. Initiator Group
3. Target
4. Extent
5. Association

---

## Step 4️⃣ Create Portal

1. Go to **Sharing → iSCSI → Portals**
2. Click **Add**

| Field           | Value        |
| --------------- | ------------ |
| **Description** | `k8s-portal` |
| **IP Address**  | `0.0.0.0`    |
| **Port**        | `3260`       |

3. Save

✅ Allows all interfaces to serve iSCSI

---

## Step 5️⃣ Create Initiator Group

1. Go to **Initiators**
2. Click **Add**

| Field                   | Value                       |
| ----------------------- | --------------------------- |
| **Description**         | `k8s-nodes`                 |
| **Initiators**          | `ALL`                       |
| **Authorized Networks** | `192.168.4.0/24` (your LAN) |

3. Save

🔐 Locks access to your network

---

## Step 6️⃣ Create Target

1. Go to **Targets**
2. Click **Add**

| Field                     | Value                |
| ------------------------- | -------------------- |
| **Target Name**           | `postgres-paperless` |
| **Portal Group**          | `k8s-portal`         |
| **Initiator Group**       | `k8s-nodes`          |
| **Authentication Method** | NONE                 |
| **Authentication Group**  | NONE                 |

3. Save

📌 Target IQN will look like:

```
iqn.2005-10.org.freenas.ctl:postgres-paperless
```

---

## Step 7️⃣ Create Extent

1. Go to **Extents**
2. Click **Add**

| Field                                     | Value                                  |
| ----------------------------------------- | -------------------------------------- |
| **Name**                                  | `postgres-paperless-extent`            |
| **Extent Type**                           | Device                                 |
| **Device**                                | `/dev/zvol/TrueNAS/postgres-paperless` |
| **Logical Block Size**                    | 512                                    |
| **Disable Physical Block Size Reporting** | OFF                                    |

3. Save

---

## Step 8️⃣ Associate Target & Extent

1. Go to **Associated Targets**
2. Click **Add**

| Field      | Value                       |
| ---------- | --------------------------- |
| **Target** | `postgres-paperless`        |
| **Extent** | `postgres-paperless-extent` |
| **LUN ID** | `0`                         |

3. Save

---

# ✅ Part 4: Verify iSCSI Is Working

## Step 9️⃣ Confirm Target Exists

On a Kubernetes node:

```bash
sudo iscsiadm -m discovery -t sendtargets -p 192.168.4.50
```

Expected output:

```
192.168.4.50:3260,1 iqn.2005-10.org.freenas.ctl:postgres-paperless
```

---

## Step 🔟 Confirm Kubernetes Can Mount

```bash
kubectl get pv
kubectl get pvc -n paperless
```

PVC should be **Bound**

---

# ✅ Part 5: Best Practices (Important)

| Setting        | Recommendation   |
| -------------- | ---------------- |
| Databases      | iSCSI (Zvol)     |
| Media / Files  | NFS              |
| Snapshots      | Enabled on Zvol  |
| Reclaim Policy | Retain           |
| Multi-node DB  | ❌ Not with iSCSI |
