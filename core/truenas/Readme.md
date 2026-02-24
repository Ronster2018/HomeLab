# Setting up TrueNas storage class components

## Prepare underlying nodes(?... Skipping initially to test and see)
```bash
# Ubuntu, Debian, etc
sudo apt install libnfs-utils
sudo apt-get install -y open-iscsi lsscsi sg3-utils multipath-tools scsitools

sudo tee /etc/multipath.conf <<-'EOF'
defaults {
    user_friendly_names yes
    find_multipaths yes
}
EOF

sudo systemctl enable multipath-tools.service
sudo service multipath-tools restart
sudo systemctl enable open-iscsi.service
sudo service open-iscsi start

```

```bash
helm repo add democratic-csi https://democratic-csi.github.io/charts/
helm repo update

# helm v3
helm search repo democratic-csi/

# copy proper values file from https://github.com/democratic-csi/charts/tree/master/stable/democratic-csi/examples
# edit as appropriate
# examples are from helm v2, alter as appropriate for v3

# add --create-namespace for helm v3
helm upgrade \
--install \
--values iscsi.yaml \
--namespace truenas \
--create-namespace \
zfs-iscsi democratic-csi/democratic-csi

helm upgrade \
--install \
--values nfs.yaml \
--namespace truenas \
--create-namespace \
zfs-nfs democratic-csi/democratic-csi
```

# Validations
```bash
kubectl get pods -n democratic-csi -o wide

curl -k -H "Authorization: Bearer API_KEY_********************************"   http://192.168.4.50/api/v2.0/system/version

```

# uninstall
```bash
helm uninstall zfs-nfs --namespace truenas
helm uninstall zfs-iscsi --namespace truenas
```