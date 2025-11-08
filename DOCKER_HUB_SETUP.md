# Docker Hub Setup Instructions

This guide will help you set up automatic Docker image builds and pushes to Docker Hub using GitHub Actions.

## Prerequisites

1. **Docker Hub Account**: Create one at https://hub.docker.com/
2. **GitHub Repository**: Your code is already on GitHub

## Setup Steps

### 1. Create Docker Hub Access Token

1. Go to https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Give it a name (e.g., "github-actions")
4. Set permissions to **Read & Write**
5. Copy the token (you won't see it again!)

### 2. Add GitHub Secrets

1. Go to your GitHub repository: https://github.com/Emmanuelasika/SoraWatermarkCleaner
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1:**
   - Name: `DOCKER_HUB_USERNAME`
   - Value: Your Docker Hub username

   **Secret 2:**
   - Name: `DOCKER_HUB_TOKEN`
   - Value: The access token you created in step 1

### 3. Trigger the Workflow

The workflow will automatically run when you:
- Push to the `main` branch
- Create a git tag (e.g., `v1.0.0`)
- Manually trigger it from the Actions tab

### 4. Use the Pre-built Image in RunPod

Once the image is built and pushed, you can use it in RunPod:

**Docker Image Name:**
```
YOUR_DOCKER_HUB_USERNAME/sorawatermarkcleaner:latest
```

**In RunPod:**
1. Go to your endpoint settings
2. Instead of building from Dockerfile, use the pre-built image
3. Enter: `YOUR_DOCKER_HUB_USERNAME/sorawatermarkcleaner:latest`

## Benefits

✅ **No more 7.77 GB downloads** - Image is pre-built and cached  
✅ **Faster deployments** - Just pull the image, don't build it  
✅ **Automatic updates** - Image rebuilds automatically on code changes  
✅ **Better caching** - Docker Hub caches layers efficiently  

## Image Tags

The workflow creates multiple tags:
- `latest` - Latest main branch build
- `main` - Main branch build
- `main-<sha>` - Specific commit SHA
- `v1.0.0` - Semantic version tags (if you tag releases)

## Troubleshooting

### Workflow Fails to Push

**Check:**
1. Docker Hub username is correct
2. Access token has Read & Write permissions
3. Secrets are named exactly: `DOCKER_HUB_USERNAME` and `DOCKER_HUB_TOKEN`

### Image Not Found in RunPod

**Check:**
1. Image was successfully pushed (check Docker Hub)
2. Using correct image name: `YOUR_USERNAME/sorawatermarkcleaner:latest`
3. Image is public or you're logged into Docker Hub in RunPod

## Next Steps

1. **Set up secrets** (steps 1-2 above)
2. **Push to main branch** - This will trigger the build
3. **Wait for workflow to complete** (check Actions tab)
4. **Update RunPod** to use the pre-built image

That's it! No more waiting for 7.77 GB downloads! 🎉

