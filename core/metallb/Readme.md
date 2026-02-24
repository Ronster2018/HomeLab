kubectl get ipaddresspools -A
kubectl get l2advertisements -A
kubectl get pods -n metallb-system -o wide
kubectl logs -n metallb-system deployment/controller --tail=50