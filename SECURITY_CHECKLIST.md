# Security Checklist for GitHub Upload

## ✅ Completed Actions

### 1. Created .gitignore
A comprehensive `.gitignore` file has been created to prevent committing:
- Cache folders (`cache/`)
- Log files (`logs/`)
- Python bytecode and virtual environments
- IDE configuration files
- OS-specific files

### 2. Identified Hardcoded Credentials

The following files contain hardcoded API keys that need to be replaced with environment variables:

#### amazon_api.py (Lines 12-19)
```python
AMAZON_AFFILIATE_TAG = 'oniricapps-21'  # ⚠️ Public, but should be configurable
API_TOKEN = 'YOUR_APIFY_API_TOKEN_HERE'  # ✅ Placeholder (safe)
ACCESS_KEY = 'YOUR_ACCESS_KEY_HERE'      # ✅ Placeholder (safe)
SECRET_KEY = 'YOUR_SECRET_KEY_HERE'      # ✅ Placeholder (safe)
```

#### chat.py (Line 18)
```python
GEMINI_API_KEY = 'YOUR_GEMINI_API_KEY_HERE'  # ✅ Placeholder (safe)
```

#### app.py (Line 15)
```python
app.secret_key = 'AISHA_ONIRICAPPS_0723'  # ⚠️ Should be changed for production
```

## ⚠️ Actions Required Before GitHub Upload

### 1. Replace Hardcoded Keys with Environment Variables

**Option A: Using environment variables**

Create a `.env` file (already in .gitignore):
```bash
AMAZON_AFFILIATE_TAG=your-tag
APIFY_API_TOKEN=your-token
AMAZON_ACCESS_KEY=your-key
AMAZON_SECRET_KEY=your-secret
GEMINI_API_KEY=your-key
FLASK_SECRET_KEY=your-secret
```

**Option B: Using a secrets.py file**

Create `secrets.py` (already in .gitignore):
```python
AMAZON_AFFILIATE_TAG = 'your-tag'
APIFY_API_TOKEN = 'your-token'
AMAZON_ACCESS_KEY = 'your-key'
AMAZON_SECRET_KEY = 'your-secret'
GEMINI_API_KEY = 'your-key'
FLASK_SECRET_KEY = 'your-secret'
```

### 2. Update Code Files

You need to modify these files to load from environment/secrets:

**amazon_api.py:**
```python
import os
# Option A: Environment variables
AMAZON_AFFILIATE_TAG = os.getenv('AMAZON_AFFILIATE_TAG', 'your-affiliate-tag')
API_TOKEN = os.getenv('APIFY_API_TOKEN')
ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY')
SECRET_KEY = os.getenv('AMAZON_SECRET_KEY')

# Option B: Import from secrets.py
# from secrets import AMAZON_AFFILIATE_TAG, API_TOKEN, ACCESS_KEY, SECRET_KEY
```

**chat.py:**
```python
import os
# Option A: Environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Option B: Import from secrets.py
# from secrets import GEMINI_API_KEY
```

**app.py:**
```python
import os
# Option A: Environment variables
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-dev-key')

# Option B: Import from secrets.py
# from secrets import FLASK_SECRET_KEY
# app.secret_key = FLASK_SECRET_KEY
```

### 3. Review Cache and Logs Content

The following directories are excluded from git but may contain sensitive data:
- `cache/` - Contains cached API responses (safe to exclude)
- `logs/` - Contains request logs with IPs and URLs (safe to exclude)

**Note**: If you have actual API keys in any cached files, ensure these folders are never committed.

### 4. Clean Git History (if keys were previously committed)

If you've previously committed real API keys:
```bash
# Use BFG Repo-Cleaner or git-filter-repo to remove sensitive data
# This is CRITICAL if real keys were committed before
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch secrets.py" \
  --prune-empty --tag-name-filter cat -- --all
```

### 5. Verify Before Push

Before pushing to GitHub:
```bash
# Check what will be committed
git status

# Review .gitignore is working
git check-ignore -v cache/ logs/ secrets.py .env

# Verify no secrets in tracked files
grep -r "api_key\|secret_key\|token" --include="*.py" .

# Do a dry run
git add -A --dry-run
```

## ✅ Safe to Commit

The following placeholders are safe (they're obviously fake):
- `'YOUR_APIFY_API_TOKEN_HERE'`
- `'YOUR_ACCESS_KEY_HERE'`
- `'YOUR_SECRET_KEY_HERE'`
- `'YOUR_GEMINI_API_KEY_HERE'`

The affiliate tag `'oniricapps-21'` is public information (visible in URLs), but should still be configurable.

## 📋 Final Checklist

- [ ] Update amazon_api.py to use environment variables or secrets.py
- [ ] Update chat.py to use environment variables or secrets.py
- [ ] Update app.py to use environment variables or secrets.py
- [ ] Create .env or secrets.py with your actual keys (DON'T commit this)
- [ ] Test that application works with new configuration
- [ ] Verify .gitignore is working
- [ ] Review git status before commit
- [ ] If keys were previously committed, clean git history
- [ ] Add a .env.example or secrets.py.example with placeholders

## 📝 Recommended: Create Example Files

Create `.env.example`:
```bash
AMAZON_AFFILIATE_TAG=your-affiliate-tag-here
APIFY_API_TOKEN=your-apify-token-here
AMAZON_ACCESS_KEY=your-amazon-access-key-here
AMAZON_SECRET_KEY=your-amazon-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here
FLASK_SECRET_KEY=your-secure-random-key-here
```

This file can be committed to guide other developers.

## 🔐 Additional Security Recommendations

1. **Generate Strong Flask Secret Key**:
   ```python
   import secrets
   print(secrets.token_hex(32))
   ```

2. **Rotate API Keys**: After uploading to GitHub, rotate all API keys as a precaution

3. **GitHub Repository Settings**:
   - Use GitHub Secrets for CI/CD
   - Enable security scanning
   - Set repository to private initially

4. **Add Security Documentation**: Document in README.md how to set up secrets

---

**Status**: Ready for GitHub upload after implementing environment variable changes.
