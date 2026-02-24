# Cert-manager + Cloudflare + Traefik
Automated TLS for Kubernetes IngressRoutes

This documentation describes how **cert-manager** is used to automatically issue and renew TLS certificates from **Let’s Encrypt** using **Cloudflare DNS-01 challenges**, and how those certificates are consumed by **Traefik IngressRoutes**.

---

## Prerequisites

* Kubernetes cluster
* cert-manager installed (`v1.11+` recommended)
```bash
helm install \
  cert-manager oci://quay.io/jetstack/charts/cert-manager \
  --version v1.19.2 \
  --namespace cert-manager \
  --create-namespace \
  --values certmanager-values.yaml \
  --set crds.enabled=true
```

* Traefik installed using CRDs
* Cloudflare-managed DNS zone
* Cloudflare **API Token** with permissions:

  * `Zone → DNS → Edit`
  * `Zone → Zone → Read`

## 1. Cloudflare API Token Secret
- Cert-manager needs credentials to create and delete DNS records during ACME validation.
- Log-in to Cloudflare > Profile > Api Tokens > Create Tokens
- Base64 Encode token
```bash
kubectl create secret generic cloudflare-api-token-secret --from-literal=api-token=**** --namespace=cert-manager --dry-run=client -o yaml > issuer-secret.yaml
```

```yaml
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: cloudflare-api-token-secret
  namespace: cert-manager
data:
  # Base64-encoded Cloudflare API token
  # Used by cert-manager to create DNS-01 challenge records
  api-token: ***
```

### Why this matters

* DNS-01 challenges **require programmatic DNS access**
* Token-based auth is safer than global API keys
* Stored securely in Kubernetes Secrets

---

## 2. ClusterIssuer (Let’s Encrypt + Cloudflare DNS-01)
A `ClusterIssuer` allows any namespace to request certificates.

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: cloudflare-dns-issuer
spec:
  acme:
    # Email used by Let's Encrypt for expiry & security notifications
    email: ***@domain.tld

    # Production Let's Encrypt endpoint
    server: https://acme-v02.api.letsencrypt.org/directory

    # Stores the ACME account private key
    privateKeySecretRef:
      name: cloudflare-dns-issuer-account-key

    # DNS-01 solver configuration
    solvers:
    - dns01:
        cloudflare:
          apiTokenSecretRef:
            # Reference to the secret created in Step 1
            name: cloudflare-api-token-secret
            key: api-token
```

### Why this matters

* **DNS-01** allows wildcard & internal domains
* No need for public HTTP ingress
* ClusterIssuer avoids duplication per namespace

---

## 3. Certificate Resource

The `Certificate` resource tells cert-manager **what domain you want** and **where to store the TLS material**.

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: traefik-ingressroute-certificate
  namespace: traefik
spec:
  # Kubernetes Secret where the TLS cert + key will be stored
  secretName: traefik-tls

  # Reference to the ClusterIssuer
  issuerRef:
    name: cloudflare-dns-issuer
    kind: ClusterIssuer

  # Domains to be included in the certificate
  dnsNames:
    - traefik.home.sparhomelab.dev
```

### Why this matters

* cert-manager watches this object
* It Automatically:
  * Creates ACME challenges
  * Issues certificates
  * Renews before expiry
* The resulting secret is `traefik-tls` in the `traefik` namespace

---

## 4. Traefik IngressRoute (TLS Enabled)

Traefik consumes the certificate by referencing the secret created above.

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: traefik-dashboard
  namespace: traefik
spec:
  entryPoints:
    # HTTPS entrypoint
    - websecure

  routes:
    - match: Host(`traefik.home.domain.tld`) &&
             (PathPrefix(`/dashboard`) || PathPrefix(`/api`))
      kind: Rule
      services:
        # Traefik's internal dashboard service
        - name: api@internal
          kind: TraefikService
          port: 80

  tls:
    # Must match Certificate.spec.secretName
    secretName: traefik-tls
```

### Why this matters

* Traefik **does not issue certificates**
* It only **consumes existing secrets**
* cert-manager and Traefik are cleanly decoupled
* TLS is automatically rotated without Traefik restarts

---

## Deployment Order

Apply manifests in this order:

```bash
kubectl apply -f cloudflare-secret.yaml
kubectl apply -f clusterissuer.yaml
kubectl apply -f certificate.yaml
kubectl apply -f ingressroute.yaml
```
---

## Validation & Troubleshooting

### Check Certificate Status

```bash
kubectl describe certificate traefik-ingressroute-certificate -n traefik
```
### Check the CertificateRequest resource status:
```bash
kubectl get certificaterequest -n traefik
kubectl describe certificaterequest <certificaterequest-name> -n traefik
```

The `CertificateRequest` status and events provide more granular details about the communication with the issuer (e.g., Let's Encrypt).

### Check the Order and Challenge resources (for ACME issuers):
```bash
kubectl get order -n traefik
kubectl describe order <order-name> -n traefik
kubectl get challenge -n traefik
kubectl describe challenge <challenge-name> -n traefik
```

The Challenge resource often reveals the most specific ACME-related errors, such as a firewall blocking port 80 or a DNS misconfiguration for http-01 or dns-01 challenges, respectively.

### Verify Secret Creation

```bash
kubectl get secret traefik-tls -n traefik
```

### cert-manager Logs

```bash
kubectl logs -n cert-manager deploy/cert-manager
```

---

## Common Issues & Fixes

| Issue                       | Likely Cause                      |
| --------------------------- | --------------------------------- |
| Certificate stuck `Pending` | DNS propagation delay             |
| `Unauthorized` errors       | Cloudflare token permissions      |
| Traefik HTTPS not working   | Secret name mismatch              |
| Works by IP, not DNS        | DNS not resolvable inside cluster |

---
