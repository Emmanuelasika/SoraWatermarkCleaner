# GitHub Secrets Setup - Quick Guide

## Step 1: Go to GitHub Secrets Page

Open this URL in your browser:
```
https://github.com/Emmanuelasika/SoraWatermarkCleaner/settings/secrets/actions
```

## Step 2: Add Docker Hub Username

1. Click **"New repository secret"**
2. Name: `DOCKER_HUB_USERNAME`
3. Value: `efethesage`
4. Click **"Add secret"**

## Step 3: Add Docker Hub Token

1. Click **"New repository secret"** again
2. Name: `DOCKER_HUB_TOKEN`
3. Value: `YOUR_DOCKER_HUB_TOKEN_HERE` (paste the token you copied from Docker Hub)
4. Click **"Add secret"**

## Step 4: Verify Secrets

You should now see two secrets:
- ✅ `DOCKER_HUB_USERNAME`
- ✅ `DOCKER_HUB_TOKEN`

## Step 5: Push Changes to Trigger Build

Once secrets are set, push the workflow files:

```bash
git add .github/workflows/docker-build-push.yml Dockerfile DOCKER_HUB_SETUP.md GITHUB_SECRETS_SETUP.md
git commit -m "Add Docker Hub auto-build workflow"
git push
```

## Step 6: Monitor the Build

1. Go to: https://github.com/Emmanuelasika/SoraWatermarkCleaner/actions
2. Watch the "Build and Push Docker Image" workflow run
3. Wait for it to complete (first build takes ~10-15 minutes)

## Step 7: Use the Image in RunPod

Once the build completes, your Docker image will be available at:
```
efethesage/sorawatermarkcleaner:latest
```

In RunPod, use this image instead of building from Dockerfile:
- Image name: `efethesage/sorawatermarkcleaner:latest`

## That's It! 🎉

No more 7.77 GB downloads - just pull the pre-built image!

