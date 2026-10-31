# Task 2: Secret

The **memory-app-credentials** Secret contains APP_TOKEN.
All three Deployments inject it into the initContainer and app using secretKeyRef.
The initContainer checks that it is nonempty without printing it.

The application does not read the token. This demonstrates Secret injection;
it does not implement application authentication.

## Create before merging the Deployment changes

Run once on the EC2 control-plane node:

~~~bash
python3 -c 'import secrets; print("APP_TOKEN=" + secrets.token_hex(32))' \
  | kubectl -n memory-app create secret generic memory-app-credentials \
      --from-env-file=/dev/stdin

kubectl -n memory-app get secret memory-app-credentials
~~~

The generated value goes directly to kubectl, without being displayed, saved to
a local file or committed. An existing Secret is not overwritten.

Then merge the Deployment references through a PR and let Argo CD sync.

The Secret is managed separately from Git. Argo CD manages only its references,
so the AppProject needs no Secret whitelist change. Recreate the Secret if the
namespace is rebuilt.

## Verify

~~~bash
kubectl -n memory-app logs deployment/memory-app-py312 -c validate-runtime
kubectl -n memory-app exec deployment/memory-app-py312 -c memory-app -- python -c 'import os; assert os.environ.get("APP_TOKEN"); print("APP_TOKEN is present")'
~~~

Expect **Runtime configuration and Secret validated** and **APP_TOKEN is present**.
Repeat for py313 and py314. Retry exec if an expected OOM restart interrupts it.

A missing Secret/key prevents container startup. An empty token fails init
validation. After rotating the Secret, replace Pods through a Pod-template
change in Git to refresh all containers.

Secret injection needs no extra app ServiceAccount permissions. Base64 is not
encryption; encryption at rest must be configured separately by the cluster
administrator. Do not commit real Secret values.
