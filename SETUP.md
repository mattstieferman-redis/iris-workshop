# Setting up a workshop

These are the instructions for setting up this template on PS Portal.

## Initial setup

### 1. Clone the workshop template repo:

```bash
git clone https://github.com/redis-developer/workshop-docker-template.git my-workshop

cd my-workshop
```

### 2. Get your own repo:

Make a repo to hold your workshop on GitHub and update the remote to the repo:

```bash
git remote set-url origin https://github.com/redis-developer/my-workshop.git
```

> WARNING: Don't skip this step. If you do, you or some AI will do a git push and make a mess of the template. So do it now.

### 3. Acquire secret tokens:

You need two tokens:

- A GitHub Personal Access Token that you will create for your repo.
- A GitHub Personal Access Token from the PS Portal team to build the images.

To generate your token:

1. Go to **User** → **Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**
2. Click **"Generate new token"**
3. Set expiration as needed. I like one year.
4. Under **Repository access**, select **"Only select repositories"** and choose your workshop repo
5. Under **Permissions** → **Repository permissions**:
	- **Contents**: Read-only
	- **Metadata**: Read-only (usually auto-selected)
6. Click **"Generate token"**
7. Copy the token and save it somewhere as you'll never see it again

To generate the token from the PS Portal team:

1. Ask them for it in the ps-portal-public channel on Slack

### 4. Configure GitHub secrets:

You now need to set these tokens:

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
2. Set `SOURCE_REPO_READ_TOKEN` to the token you generated
3. Set `PS_IMAGE_BUILDER_TOKEN` to the token you were given from the PS Portal team

### 5. Ensure GitHub Actions is enabled:

1. Go to repo → **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **"Read and write permissions"**

You are now completely set up to deploy the image. But you probably don't want to do that yet.

## Building the workshop

### 1. Run it locally:

To run locally, just:

```bash
docker compose up
```

And then navigate to http://localhost to test it out.

### 2. Make changes:

Make changes. Add and remove panels. Add services. Restart Docker. Go to town until your happy. More details on this in [README.md](README.md).

## Deploying the workshop

### 1. Build the image:

1. Go to **GitHub Actions** for your repo at something like https://github.com/redis-developer/my-workshop/actions
2. Click **"Trigger Image Build"** in the left sidebar
3. Click **"Run workflow"** dropdown (right side)
4. Enter a version number (e.g., `0.1.7`) — **increment each time**
5. Click **"Run workflow"**

This will trigger another GitHub action from the PS Portal team at https://github.com/Redis-ProfessionalService/ps-portal-image-builder/actions/.

6. Wait for it to finish and when it does look in the "Get image information" step and grab the version. It should look like: `portal-images-<my-workshop>-<my version>`.

### 2. Deploy the image to PS Portal:

1. Got to PS Portal at https://portal.ps-redis.com/ and login if you need to.
2. Go to **Labs** if you want a single instance (for testing, or just to start with a single user)
3. Go to **Training Classes** if you are hosting a workshop
4. In either case, click **New**
5. Give it a **Name**—whatever you like
6. For **Type**, select "I've my own image"
7. Enter your version you grabbed earlier as the **Image location**. The one that looked like `portal-images-<my-workshop>-<my version>`.
8. Pick a **Machine size**. The template works fine on **Small**. You might need **Medium**. You probably won't need **Large**.
9. Leave the **Port** as 80.
10. Click **Create** and wait for the image to be created.

Any other fields should be self explanatory.

### 3. Start using the workshop:

You're done. Send links to whomever needs them. Use the PS Portal to host workshops or do labs yourself.