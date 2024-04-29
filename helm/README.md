
# An Otter Wiki Helm Chart

This Helm chart simplifies the deployment of An Otter Wiki on Kubernetes. Tested on k3s. 

## Installing the Chart

To install the chart with the release name `my-otterwiki`:

```shell
helm install my-otterwiki ./path/to/otterwiki/chart
```

For example:
```shell
[~/otterwiki] $ helm install my-otterwiki ./helm/
NAME: my-otterwiki
LAST DEPLOYED: Fri Apr 12 09:43:54 2024
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  http://otterwiki.local
```

This command deploys An Otter Wiki on the Kubernetes cluster with the default configuration. 

## Uninstalling the Chart

To uninstall/delete the `my-otterwiki` deployment:

```shell
helm delete my-otterwiki
```

This command removes all the Kubernetes components associated with the chart and deletes the release.

## Service Types

OtterWiki can be exposed externally using different types of services. Here’s how to configure the service type:

### Ingress

The most likely service to use and enabled by default. Requires the Kubernetes cluster to have an Ingress controller configured. 

```shell
$ helm install my-otterwiki ./helm/ --set ingress.enabled=true
```

If .local domains are setup and working, you can then connect using ```http://otterwiki.local```

```shell
 $ curl http://otterwiki.local
<!DOCTYPE html><html lang="en"> <head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"><meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport"><meta name="viewport" content="width=device-width"><meta property="og:title" content="Home - An Otter Wiki">
```

#### Ingress with specified hostname
To use your own hostname 

```shell
helm install my-otterwiki ./helm/ --set ingress.hostname=otterwiki.example.com
```

Example output:

```shell
$ helm install my-otterwiki ./helm/ --set ingress.hostname=otterwiki.example.com
NAME: my-otterwiki
LAST DEPLOYED: Fri Apr 12 10:08:23 2024
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  http://otterwiki.example.com
$ curl http://otterwiki.example.com
<!DOCTYPE html><html lang="en"> <head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"><meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport"><meta name="viewport" content="width=device-width"><meta property="og:title" content="Home - An Otter Wiki">
...
```

### NodePort

To use a NodePort service:

```shell
helm install my-otterwiki ./helm/ --set service.type=NodePort
```

NodePort exposes OtterWiki on each node’s IP at a static port. You can access the service from outside the cluster by requesting `<NodeIP>:<NodePort>`.

For example, where one of the Kubernetes nodes is 192.168.200.22 and NodePort is 30353 : 
```shell
$ kubectl get service | grep my-otterwiki-helm
my-otterwiki-helm   NodePort       10.43.148.5    <none>           80:30353/TCP     5m28s
$ curl  192.168.200.22:30353
<!DOCTYPE html><html lang="en"> <head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"><meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport"><meta name="viewport" content="width=device-width"><meta property="og:title" content="Home - An Otter Wiki"><meta property="og:type" content="website"><meta property="og:url" content="http://192.168.200.22:30353/Home"><meta property="og:description" content="A minimalistic wiki powered by python, markdown and git.">
..
```

### ClusterIP

For internal access only, you can use ClusterIP:

```shell
helm install my-otterwiki ./helm/ --set service.type=ClusterIP
```

ClusterIP exposes OtterWiki internally within the cluster, making it accessible only from within.
To connect to ClusterIP

```shell
$ export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=helm,app.kubernetes.io/instance=my-otterwiki" -o jsonpath="{.items[0].metadata.name}")
$ export CONTAINER_PORT=$(kubectl get pod --namespace default $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
kubectl --namespace default port-forward $POD_NAME 8080:$CONTAINER_PORT
```
Then connect to localhost 8080
```shell
$ curl localhost:8080
<!DOCTYPE html><html lang="en"> <head><meta charset="utf-8"><meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"><meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" name="viewport"><meta name="viewport" content="width=device-width"><meta property="og:title" content="Home - An Otter Wiki">
...
```

## Customizing the Chart Before Installing

To edit or customize the default configuration, you can use the `helm show values` command to generate a `values.yaml` file:

```shell
helm show values ./helm/ > myvalues.yaml
```

Edit `myvalues.yaml` as needed, then install the chart with the updated values:

```shell
helm install my-otterwiki ./helm/ -f myvalues.yaml 
```

