# One-command VPS installer

This public installer downloads deployment configuration only. It does not build images
or publish them to GitHub. After configuration, `deploy.sh` downloads both sources to a
temporary VPS build directory, builds local Docker images, deploys the stack, and removes
the temporary source directory.

```bash
read -rsp "GitHub token: " GITHUB_TOKEN
export GITHUB_TOKEN
curl -fsSL https://raw.githubusercontent.com/Gusma-crypto/Agent-fraudguard/main/deploy/vps/install.sh | bash
nano /opt/fraudguard/.env.production
/opt/fraudguard/deploy.sh
```

The token needs read-only Contents access to `Gusma-crypto/Fraudguard-core`. It is
not written to disk. Docker images are built locally on the VPS; no GHCR image is used.
The temporary source directory is removed after deployment. Run `deploy.sh` again for
updates; `update-restart.sh` is an alias for the same flow.
