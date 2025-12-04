# CI/CD Pipeline Guide

GitHub Actions workflows for automated testing, building, and deployment of the Email Campaign Management Platform.

## 📋 Overview

Two GitHub Actions workflows automate the entire development and deployment pipeline:

1. **tests.yml** - Run on every push/PR to main branches
2. **deploy.yml** - Run on production branch pushes and version tags

## 🧪 Tests Workflow (tests.yml)

Runs on every push to any branch and on all pull requests.

### Jobs

#### 1. Backend Tests
- **Runs on:** Ubuntu Latest
- **Python versions:** 3.12, 3.13 (matrix)
- **Database:** PostgreSQL 16 (service container)
- **Cache:** Redis 7 (service container)

**Steps:**
1. Checkout code
2. Setup Python (with pip caching)
3. Install dependencies (base + dev)
4. Run migrations
5. Run Django tests with parallel execution
6. Generate coverage report
7. Upload to Codecov

**Environment Variables:**
```
DEBUG=False
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=test-secret-key-for-ci
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 2. Code Quality
- **Runs on:** Ubuntu Latest

**Tools:**
- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Linting
- **Bandit** - Security scanning

**Steps:**
```bash
# Check code formatting
black --check apps/ project_config/

# Check import sorting
isort --check-only apps/ project_config/

# Run linter
flake8 apps/ project_config/

# Security scan
bandit -r apps/
```

#### 3. Django Checks
- **Runs on:** Ubuntu Latest

**Steps:**
1. Setup Python
2. Install base dependencies
3. Run `python manage.py check`
4. Run `python manage.py makemigrations --dry-run --check`

**Purpose:** Ensure Django system is configured correctly and migrations are up-to-date

#### 4. Frontend Tests
- **Runs on:** Ubuntu Latest
- **Node version:** 18

**Steps:**
1. Checkout code
2. Setup Node.js (with npm caching)
3. Install npm dependencies
4. Run tests with coverage
5. Run linting
6. Build for production

#### 5. Docker Build Test
- **Runs on:** Ubuntu Latest

**Steps:**
1. Setup Docker Buildx
2. Build development image (test)
3. Build production image (test)

**Purpose:** Ensure Dockerfile builds without errors

#### 6. Summary
- **Runs on:** Ubuntu Latest
- **Depends on:** All previous jobs

**Steps:**
1. Display test results
2. Add comment to PR (if PR)
3. Fail workflow if any critical test fails

### Artifacts & Reports

- **Coverage Reports** - Uploaded to Codecov
- **Test Results** - Visible in GitHub Actions tab
- **PR Comments** - Auto-commented on PRs with test status

---

## 🚀 Deploy Workflow (deploy.yml)

Runs on:
- Push to `production` branch
- Git version tags (v*.*)
- Manual workflow dispatch

### Jobs

#### 1. Test (Prerequisite)
Same as tests.yml backend tests job
- Runs PostgreSQL and Redis services
- Executes Django test suite
- Generates coverage reports

#### 2. Security Scan
- Runs Bandit security scanner
- Runs Safety dependency check
- Continues on error (warnings don't block deployment)

#### 3. Build Docker Image
- **Requires:** test and security jobs passed
- **Registry:** Docker Hub
- **Image Name:** `{username}/email-platform:{tag}`

**Steps:**
1. Checkout code
2. Setup Docker Buildx
3. Login to Docker Hub
4. Extract metadata for tags
5. Build and push Docker image
6. Use Docker registry cache for faster builds

**Tags Generated:**
- `latest` - For main branch
- `{version}` - Semver tags (v1.2.0)
- `sha-{short-hash}` - Git SHA
- `branch-name` - For feature branches

**Docker Hub Credentials Required:**
```
secrets.DOCKER_USERNAME
secrets.DOCKER_PASSWORD
```

#### 4. Deploy to Production
- **Requires:** build job passed
- **Runs on:** production branch or version tags
- **Environment:** Production (protected)

**Steps:**
1. Checkout code
2. Configure AWS credentials
3. Setup SSH for server access
4. Execute deploy script on production server
5. Verify deployment (health check)
6. Notify Slack on success/failure
7. Create GitHub Release (for version tags)

**Required Secrets:**
```
secrets.DEPLOY_KEY          # SSH private key
secrets.DEPLOY_HOST         # Production server IP/hostname
secrets.DEPLOY_USER         # SSH username
secrets.AWS_ACCESS_KEY_ID   # AWS credentials
secrets.AWS_SECRET_ACCESS_KEY
secrets.AWS_REGION
secrets.SLACK_WEBHOOK_URL   # Slack notification
secrets.DOCKER_USERNAME     # Docker registry
secrets.DOCKER_PASSWORD
```

**What Happens:**
1. Connects to production server via SSH
2. Runs `/opt/email-platform/backend/deploy.sh --force`
3. Waits 30 seconds for deployment
4. Tests health endpoint
5. Sends Slack notification

---

## 🔐 GitHub Secrets Setup

### Required Secrets

#### Docker Registry
```
DOCKER_USERNAME: your-docker-hub-username
DOCKER_PASSWORD: your-docker-hub-access-token
```

#### Production Deployment
```
DEPLOY_KEY: |
  -----BEGIN OPENSSH PRIVATE KEY-----
  ... SSH private key content ...
  -----END OPENSSH PRIVATE KEY-----

DEPLOY_HOST: api.example.com
DEPLOY_USER: deploy-user
```

#### AWS (For production resources)
```
AWS_ACCESS_KEY_ID: AKIA...
AWS_SECRET_ACCESS_KEY: wJal...
AWS_REGION: us-east-1
```

#### Slack Notifications
```
SLACK_WEBHOOK_URL: https://hooks.slack.com/services/T.../B.../X...
```

### How to Add Secrets

1. Go to: GitHub → Repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value
4. Repeat for all required secrets

### Generate Deploy Key

```bash
# Generate SSH key pair
ssh-keygen -t ed25519 -f deploy_key -N ""

# Content of deploy_key is the DEPLOY_KEY secret
cat deploy_key

# Copy public key to server
cat deploy_key.pub | ssh user@production-server "cat >> ~/.ssh/authorized_keys"
```

---

## 📊 Workflow Runs

### View Workflow Status

1. Go to: GitHub → Repository → Actions
2. Select workflow (Tests or Deploy)
3. View runs, logs, and status

### Common Workflow Scenarios

#### Scenario 1: Push to Feature Branch
```
Triggers: tests.yml
- Backend tests
- Code quality checks
- Django checks
- Frontend tests
- Docker build test
Result: ✅ All green = ready for PR
```

#### Scenario 2: Create Pull Request
```
Triggers: tests.yml
- Same as above
- Auto-comment with test results
- Show coverage changes
```

#### Scenario 3: Merge to Production
```
Triggers: deploy.yml
1. Run all tests ✅
2. Security scan ✅
3. Build Docker image
4. Deploy to production
5. Health check
6. Slack notification
Result: App live in production
```

#### Scenario 4: Create Version Tag
```
Command: git tag v1.2.0 && git push origin v1.2.0

Triggers: deploy.yml
1. Test ✅
2. Build image → docker.io/user/email-platform:1.2.0
3. Deploy
4. Create GitHub Release with artifacts
```

---

## 📝 Configuration

### Modify Test Command

Edit `.github/workflows/tests.yml`:

```yaml
- name: Run Django tests
  run: |
    python manage.py test apps/ --verbosity=2 --parallel
    # Change --parallel to --sequential for debugging
    # Add --keepdb to speed up repeated runs
```

### Modify Deploy Target

Edit `.github/workflows/deploy.yml`:

```yaml
deploy:
  if: github.ref == 'refs/heads/production' || startsWith(github.ref, 'refs/tags/v')
  # Change 'production' to 'main' to deploy from main
  # Add '|| github.ref == 'refs/heads/staging'' for staging
```

### Add New Test Suite

Add to `.github/workflows/tests.yml`:

```yaml
  my-new-test:
    runs-on: ubuntu-latest
    name: My New Test
    steps:
      - uses: actions/checkout@v4
      # Add your test steps
```

---

## 🔍 Troubleshooting

### Tests Failing Locally but Passing in CI

**Cause:** Environment differences
**Solution:**
```bash
# Run with CI environment variables
export DEBUG=False
export DATABASE_URL=postgresql://...
export SECRET_KEY=test-key
python manage.py test
```

### Docker Push Failing

**Cause:** Docker Hub credentials invalid
**Solution:**
1. Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
2. Check Docker Hub access token (not password)
3. Ensure token has push permissions

### Deployment Not Running

**Cause:** Secrets not configured
**Solution:**
1. Check GitHub Secrets page: Settings → Secrets
2. Verify all required secrets exist
3. Check secret values for trailing spaces

### Slack Notifications Not Working

**Cause:** Webhook URL invalid or expired
**Solution:**
1. Generate new webhook in Slack
2. Update `SLACK_WEBHOOK_URL` secret
3. Check workflow logs for errors

---

## 📈 Monitoring

### Check Workflow Health

```bash
# View recent workflow runs
gh run list --repo yourorg/email-platform --workflow deploy.yml --limit 10

# View specific run details
gh run view <run-id> --log

# Cancel running workflow
gh run cancel <run-id>
```

### Workflow Status Badge

Add to README.md:

```markdown
[![Tests](https://github.com/yourorg/email-platform/workflows/Tests%20&%20Code%20Quality/badge.svg)](https://github.com/yourorg/email-platform/actions/workflows/tests.yml)

[![Deploy](https://github.com/yourorg/email-platform/workflows/Deploy%20to%20Production/badge.svg)](https://github.com/yourorg/email-platform/actions/workflows/deploy.yml)

[![codecov](https://codecov.io/gh/yourorg/email-platform/branch/main/graph/badge.svg)](https://codecov.io/gh/yourorg/email-platform)
```

---

## 🎯 Best Practices

1. **Keep Tests Fast**
   - Use `--parallel` flag
   - Mock external services
   - Use SQLite for tests (when possible)

2. **Secure Secrets**
   - Never commit `.env` files
   - Rotate keys regularly
   - Use least privilege for AWS keys

3. **Clear Logging**
   - Add context to test failures
   - Use descriptive job names
   - Log important environment variables (safely)

4. **Efficient Caching**
   - Cache pip and npm dependencies
   - Use Docker layer caching
   - Clean up old images

5. **Deployment Safety**
   - Always backup database before deployment
   - Use health checks
   - Have rollback procedure
   - Gradual rollout to canary environment first

6. **Monitoring & Alerts**
   - Slack notifications for deploys
   - Email alerts for test failures
   - GitHub branch protection rules
   - Required status checks

---

## 🔗 Related Documentation

- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
- [DOCKER_SETUP.md](./DOCKER_SETUP.md)
- [deploy.sh](./deploy.sh)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Create deploy key
ssh-keygen -t ed25519 -f deploy_key -N ""

# 2. Add to server
cat deploy_key.pub | ssh user@server "cat >> ~/.ssh/authorized_keys"

# 3. Add secrets to GitHub
# Go to Settings → Secrets → New repository secret

# 4. Test workflow
git push origin main
# Watch: GitHub → Actions → Tests workflow

# 5. Deploy to production
git tag v1.0.0
git push origin v1.0.0
# Watch: GitHub → Actions → Deploy workflow
```

---

Last Updated: 2024
Version: 1.0
