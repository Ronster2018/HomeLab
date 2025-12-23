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