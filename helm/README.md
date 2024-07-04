# An Otter Wiki

An Otter Wiki is a minimalistic wiki powered by python, markdown and git.

## Introduction

This chart bootstraps An [OtterWiki](https://github.com/redimp/otterwiki) deployment
on a [Kubernetes](https://kubernetes.io) cluster using the [Helm](https://helm.sh)
package manager.

If you run into any issues, please report them via [github](https://github.com/redimp/otterwiki/issues).

## Prerequisites

- Kubernetes 1.23+
- Helm 3.8.0+
- PV provisioner support in the underlying infrastructure

## Installing the Chart

To install the chart with the release name `my-otterwiki` run:

```bash
helm install my-otterwiki --version 0.1.0 oci://registry-1.docker.io/redimp/otterwiki
```

The command deploys An Otter Wiki on the kubernetes cluster in the default namespace
with the default configuration. See the [Parameters](#parameters) section for anything
that can be configured during installation.

## Parameters

| Name                              | Description                                          | Value                                       |
| --------------------------------- | ---------------------------------------------------- | ------------------------------------------- |
| `config`                          | configure Otter Wiki environment variables           | `{}`                                        |
| `image.repository`                | Otter Wiki image repository                          | `redimp/otterwiki`                          |
| `image.pullPolicy`                | Image pull policy                                    | `Always`                                    |
| `image.tag`                       | Otter Wiki image tag, overrides the charts appVersion | `""`                                       |
| `service.type`                    | Kubernetes Service type                              | `ClusterIP`                                 |
| `service.port`                    | Service HTTP port                                    | `80`                                        |
| `ingress.enabled`                 | Enable ingress controller resource                   | `false`                                     |
| `ingress.hosts[0].host`           | Hostname to your OtterWiki installation              | `otterwiki.local`                           |
| `ingress.hosts[0].paths.path`     | Path within the url structure                        | `/`                                         |
| `ingress.hosts[0].paths.pathType` | Path matching rule                                   | `ImplementationSpecific`                    |
| `ingress.hosts[0].tls[0].hosts[0]`  |  Hostname for which TLS will be configured         | `otterwiki.local`                           |
| `ingress.hosts[0].tls[0].secretName` | TLS Secret (certificates)                         | `otterwiki-local-tls`                       |
| `persistence.enabled`             | Enable persistence using PVC                         | `true`                                      |
| `persistence.storageClass`        | PVC Storage Class for OtterWiki volume               | `nil` (uses alpha storage class annotation) |
| `persistence.accessMode`          | PVC Access Mode for OtterWiki volume                 | `ReadWriteOnce`                             |
| `persistence.size`                | PVC Storage Request for OtterWiki volume             | `512Mi`                                     |
| `resources`                       | CPU/Memory resource requests/limits                  | `{}`                                        |
| `nodeSelector`                    | Node labels for pod assignment                       | `{}`                                        |
| `affinity`                        | Affinity settings for pod assignment                 | `{}`                                        |
| `tolerations`                     | Toleration labels for pod assignment                 | `[]`                                        |
| `podAnnotations`                  | Pod annotations                                      | `{}`                                        |


The parameters can be specified using `--set key=value[,key=value]` as argument to `helm install`, e.g.

```bash
helm install my-otterwiki \
  --set config.SITE_DESCRIPTION="An Otter Wiki deployed with Helm" \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host="helm.otterwiki.com" \
  --version 0.1.0 \
  oci://registry-1.docker.io/redimp/otterwiki
```

Alternatively, you can use a yaml-file to set the parameters, for example when creating a `values.yaml` with

```yaml
config:
  SITE_DESCRIPTION: "An Otter Wiki deployed with Helm"
ingress:
  enabled: true
  hosts:
  - helm.otterwiki.com
```

and deploy it with

```bash
helm install my-otterwiki \
  --values values.yaml \
  --version 0.1.0 \
  oci://registry-1.docker.io/redimp/otterwiki
```

The most recent default `values.yaml` can be fetched using

```bash
helm show values --version 0.1.0 oci://registry-1.docker.io/redimp/otterwiki > values.yaml
```

### Application configuration

The app is configured via the `config` mapping, with the keys being the variable names
used in the `settings.cfg`, see [Configuration](https://otterwiki.com/Configuration). The configuration
will be stored in a configMap or those variables considered as a secret in a Secret.

### Persistence

The [redimp/otterwiki](https://hub.docker.com/r/redimp/otterwiki) image stores the wikis
data at the `/app-data` path of the container. Persistent Volume Claims are used to keep the
data across deployments.
