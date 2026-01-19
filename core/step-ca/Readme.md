# Home Lab Setup
- We will not be using a certificate like Letsencrypt or Cloudflare to provide certificates. This home lab will be self contained

## Overview of Steps Taken
1. Generate our private keys and root certificate
2. Generate Intermediate Certificate
3. Give that certificate to our CA so it can generate and sign certificates (Step CA)

### 1. Generate PK & Root Certificate (OpenSSL)
1. Update `/ca/root.conf` file and move it into
2. Create the following directories
```bash
mkdir -p ./ca ./ca/certs ./ca/crl ./ca/newcerts ./ca/private
touch ./ca/index.txt
# Serial is a unique serial number for the self signed root cert
echo 1111 > ./ca/serial
```

3. Generate and sign Root certificate
```bash
# Generate a private key (needs a passphrase, don't forget the passphrase)
openssl genrsa -aes256 -out ./ca/root_ca_key 4096

# Sign a 100 year certificate, to be used by clients mostly
openssl req -config ./ca/root.conf -key ./ca/root_ca_key -days 36525 -new -x509 -sha256 -extensions v3_ca -out ./ca/root_ca.crt
```
> Note: To examine the key, use the following command
```bash
openssl x509 -noout -text -in ./ca/root_ca.crt
```

### 2. Generate Intermediate Cert
```bash
# Generate a private key (needs a passphrase)
openssl genrsa -aes256 -out ./ca/intermediate_ca_key 4096
# Generate a certificate-signing-request (CSR) for the intermediate CA key
openssl req -config ./ca/root.conf -new -sha256 -key ./ca/intermediate_ca_key -out ./ca/intermediate_ca.csr.pem
# Sign the CSR with the root key
openssl ca -config ./ca/root.conf -keyfile ./ca/root_ca_key -cert ./ca/root_ca.crt -extensions v3_intermediate_ca -days 3650 -notext -md sha256 -in ./ca/intermediate_ca.csr.pem -out ./ca/intermediate_ca.crt
```

- To view and validate the cert, run the following command
```bash
openssl x509 -noout -text -in ./ca/intermediate_ca.crt
```

### 3. Deploy and Configure Step CA and Autocert (In cluster service to service mTLS security) add-on
#### 1. Create the following secrets for cert and key files

step-certificates-secrets
- `intermediate_ca_key`
      The encrypted X.509 intermediate certificate private key.
- `root_ca_key` (optional)
      The encrypted X.509 root certificate private key.
```bash
kubectl create secret generic step-certificates-secrets --from-file=./ca/intermediate_ca_key --from-file=./ca/root_ca_key --namespace=step-ca --dry-run=client -o yaml  > step-certificates-secrets.yml
```

step-certificates-certs
- `root_ca.crt`
      The root CA certificate.
- `intermediate_ca.crt`
      The intermediate CA certificate (optional).
```bash
kubectl create secret generic step-certificates-certs --from-file=./ca/root_ca.crt --from-file=./ca/intermediate_ca.crt --namespace=step-ca --dry-run=client -o yaml > step-certificates-certs.yml
```
step-certificates-ca-password
- `password`
      The password used to decrypt the X.509 intermediate certificate private key.
      type: smallstep.com/ca-password (manually added type)
```bash
kubectl create secret generic step-certificates-ca-password --from-literal=password='Gab Canteen Gummy3' --namespace=step-ca --dry-run=client -o yaml > step-ca-cert-secret.yml
```
step-ca-step-certificates-config (Currently leaving this field in `step-ca-values` as `false`)
- `ca.json`
      The configuration file used by step-ca.
```bash
kubectl create configmap step-certificates-config --from-file=ca.json --dry-run=client -o yaml --namespace=step-ca > step-certificates-config.yaml
```

- `default.json`
      The configuration file used by step with the default flags.

When existingSecrets.issuer is true secret name: {{ include "step-certificates.fullname" . }}-certificate-issuer-password secret type: smallstep.com/certificate-issuer-password which contains the following data:

    password
        The password used to decrypt the private key used to sign RA tokens.
```bash
kubectl create secret generic step-certificates-certificate-issuer-password --from-literal=password='Hamlet Duo Naturist7' --namespace=step-ca --dry-run=client -o yaml > step-certificate-issuer-secret.yaml
```

#### 2. Modify values in `step-ca-values.yaml`

#### 3.. Install Helm on the system
- The plan here is to extract the template and add our own certificates to the secrets.

```bash
helm repo add smallstep https://smallstep.github.io/helm-charts/
helm install step-certificates smallstep/step-certificates -f step-ca-values.yml --namespace step-ca --create-namespace

# update
helm upgrade --install step-certificates smallstep/step-certificates -f step-ca-values.yml --namespace step-ca
```

> Note: Uninstall: `helm uninstall step-certificates -n step-ca`

# Why do we need Certs and a Certificate Authority??
## M.I.T.M Attacks
- A man in the middle attack is where an attacker attempts to intercept a web request, examine or modify it, and send it off to where the web request was headed. This tricks both parties on either into thinking that they're talking directly to each other.
- As an act of prevention, we can now introduce a trusted 3rd party with signed certificates that ensures the two end parties are talking to each other confidently. That third party is the Certificate Authority. They all have trusted certificates from websites. Before websites can communicate securely on port `443` with TLS, the server must present a valid and signed certificate to a CA. The server will of course, start, but the certificates will be invalid.
- Now that the web server has provided information to the Certificate Authority, the client has to verify/validate the certificate. Now the client takes the Public Key from the C.A, uses that to encrypt the cert info, and compare it with the cert from the C.A. If those two pieces match, then it is trusted.


## SSL/TLS Handshake Overview (Good to know)

Client                                             Server
  |                                                   |
  | (1) ClientHello                                   |
  |----------------------------------------------->   |
  |                                                   |
  | (2) ServerHello                                   |
  |<-----------------------------------------------   |
  |                                                   |
  | (3) Server Certificate                            |
  |<-----------------------------------------------   |
  |                                                   |
  | (4) Server Key Exchange*                          |
  |<-----------------------------------------------   |
  |                                                   |
  | (5) ServerHelloDone*                              |
  |<-----------------------------------------------   |
  |                                                   |
  | (6) Client Key Exchange                           |
  |----------------------------------------------->   |
  |                                                   |
  | (7) ChangeCipherSpec                              |
  |----------------------------------------------->   |
  |                                                   |
  | (8) Finished                                      |
  |----------------------------------------------->   |
  |                                                   |
  | (9) ChangeCipherSpec                              |
  |<-----------------------------------------------   |
  |                                                   |
  | (10) Finished                                     |
  |<-----------------------------------------------   |
  |                                                   |
  | (11) Encrypted Application Data                   |
  |<===============================================>  |

1. ClientHello:
- Client initiates the handshake.
- Sends supported TLS versions, cipher suites, random value, and extensions (SNI, ALPN).

2. ServerHello:
- Server selects the TLS version and cipher suite.
- Sends its own random value.

3. Server Certificate:
- Server sends its public certificate.
- Allows the client to verify the server’s identity using a trusted CA.

4. Server Key Exchange (TLS 1.2, optional):
- Server provides key exchange parameters (e.g., ECDHE).
- Used to securely establish shared secrets.

5. ServerHelloDone (TLS 1.2 only):
- Indicates the server has finished its initial handshake messages.

6. Client Key Exchange:
- Client sends key exchange data.
- Both sides now independently compute the same shared session keys.

7. ChangeCipherSpec (Client):
- Client signals it will start using encrypted communication.
- Switches to negotiated cipher suite.

8. Finished (Client):
- First encrypted message from the client.
- Confirms handshake integrity.

9. ChangeCipherSpec (Server):
- Server switches to encrypted communication.

10. Finished (Server):
- Server confirms successful handshake and key agreement.

11. Encrypted Application Data:
- Secure bidirectional communication begins.
-mAll data is encrypted and integrity-protected.