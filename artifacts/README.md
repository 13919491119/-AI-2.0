Artifacts directory for canary deploy.

- manifests/: Kubernetes manifests including `canary-deployment.yaml`.

To use: place built image in registry and update `manifests/canary-deployment.yaml` image field. Then run deploy script:

```bash
./tools/deploy_canary.sh --artifact artifacts --namespace canary --dry-run=true
```
