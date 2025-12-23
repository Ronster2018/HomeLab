# Install Traefik Resource Definitions:
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml

# Install RBAC for Traefik:
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-rbac.yml


# Traefik on Kubernetes with HTTPS and Pi-hole DNS

This documentation outlines the full setup of **Traefik v3** on a home Kubernetes cluster with:

- MetalLB for LoadBalancer IPs
- Self-signed TLS certificates for HTTPS
- Pi-hole as DNS server for local domain resolution
- Guidance for exposing new services via DNS

---
## 0. Installation
- Create Namespace
```bash
kubectl apply -f traefik/traefik-ns.yml
```

-  Install Traefik Resource Definitions:

```bash
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-definition-v1.yml
```

Install RBAC for Traefik:
```bash
kubectl apply -f https://raw.githubusercontent.com/traefik/traefik/v3.6/docs/content/reference/dynamic-configuration/kubernetes-crd-rbac.yml
```

Apply manifests
```bash
kubectl apply -f traefik/
```

## 1. Traefik Deployment Overview

Traefik is deployed as a **LoadBalancer service** and exposes **web (HTTP) and websecure (HTTPS)** entrypoints. It handles routing of IngressRoutes defined in Kubernetes and serves self-signed certificates for local domains.

---

### 1.1 Traefik Deployment YAML
**Key components:**

* `--api.dashboard=true`: Enables the dashboard on Traefik.
* `--providers.kubernetescrd`: Allows Traefik to read CRD IngressRoutes.
* `--entrypoints.web`: HTTP traffic.
* `--entrypoints.websecure`: HTTPS traffic.
* `--entrypoints.web.http.redirections.entryPoint.to=websecure`: Automatically redirects HTTP → HTTPS.
* `--certificatesresolvers.default.acme.tlschallenge=true`: Auto-generates self-signed certificates.
* `--certificatesresolvers.default.acme.storage=/data/acme.json`: Storage location for generated certificates.
* `volumeMounts` + `volumes`: Required for Traefik to persist certificate storage (can later use a PVC for persistence).

---

### 1.2 Traefik Service YAML
* `type: LoadBalancer`: Exposes Traefik on an IP assigned by MetalLB.
* `selector: app: traefik`: Connects Service to Traefik pods.
* `ports`: Exposes HTTP and HTTPS.

---

### 1.3 MetalLB Configuration

* `IPAddressPool`: Range of IPs MetalLB can assign to LoadBalancer services.
* `L2Advertisement`: Broadcasts ARP so local devices can reach LoadBalancer IPs.

---

### 1.4 IngressRoute Example for Pi-hole

* `entryPoints: websecure`: Serves HTTPS traffic.
* `Host('pihole.home.arpa')`: DNS hostname for Pi-hole.
* `services.name/port`: Routes traffic to Pi-hole service in Kubernetes.
* `tls.certResolver`: Uses self-signed TLS from Traefik.

---

### 1.5 IngressRoute Example for Traefik Dashboard

* `api@internal`: Internal Traefik dashboard service.
* Enables HTTPS access to the dashboard.

---

## 2. Exposing New Services via Traefik + DNS

1. **Deploy your application** as a Kubernetes Deployment + Service.
2. **Create an IngressRoute** in the same namespace:

3. **Add a DNS entry in Pi-hole**:

* Domain: `myapp.home.arpa`
* IP: The MetalLB LoadBalancer IP assigned to Traefik (e.g., 192.168.4.201)

4. **Verify access over HTTPS**:

```
https://myapp.home.arpa
```

> All services now share a single Traefik LoadBalancer, which terminates TLS and routes requests internally via Kubernetes Service names.

---

## 3. Notes / Best Practices

* Use **consistent labeling** on all pods to match Service selectors.
* Keep **MetalLB IPs within your LAN subnet** to avoid ARP issues.
* For production or multiple apps, consider **dedicated Persistent Volumes** for ACME storage to persist certificates across restarts.
* Update Pi-hole **local DNS entries** for each new service using the `.home.arpa` domain.
* Always test connectivity **inside the cluster** first:

```bash
kubectl run tmp --rm -it --image=busybox sh
wget -O- http://myapp-service.my-namespace.svc.cluster.local
```

* Self-signed certificates will trigger browser warnings — you can add them to trusted cert store for convenience.

---

## 4. References

* [Traefik Official Documentation v3](https://doc.traefik.io/traefik/)
* [MetalLB Documentation](https://metallb.universe.tf/)
* [Pi-hole DNS Configuration](https://docs.pi-hole.net/)
* [Kubernetes IngressRoute CRD](https://doc.traefik.io/traefik/routing/providers/kubernetes-crd/)
