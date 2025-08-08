# Environment Variable Usage Audit

## Summary
This audit documents all references to `API_KEY`, `OPENAI_API_KEY`, `DB_TOKEN`, and `X_API_KEY` in the codebase to identify exactly what needs to change for the environment variable migration.

## Executive Summary

The codebase currently uses multiple environment variables for authentication:
- **`X_API_KEY`** - Primary API key variable (preferred)
- **`API_KEY`** - Secondary/fallback API key variable
- **`DB_TOKEN`** - Used by newer security modules for authentication
- **`OPENAI_API_KEY`** - Referenced in security utilities but not actively used in auth flow

## Key Findings

### 1. Current Authentication Flow
The main authentication logic has **inconsistent variable naming** across different modules:

#### A. Legacy Authentication (routes/authenticate.py, routes/v1/toolkit/authenticate.py)
```python
API_KEY = os.environ.get('API_KEY')  # Uses API_KEY only
```

#### B. Main Config (config.py)
```python
API_KEY = os.environ.get('X_API_KEY') or os.environ.get('API_KEY')  # Tries X_API_KEY first, falls back to API_KEY
```

#### C. Services (services/authentication.py)
```python
from config import API_KEY  # Inherits config.py logic
```

#### D. New Security Module (server/security.py)
```python
token = os.getenv('DB_TOKEN')  # Uses DB_TOKEN exclusively
```

### 2. Critical Files Requiring Updates

#### **IMMEDIATE CHANGES REQUIRED:**

##### Primary Authentication Files:
1. **`config.py` (Lines 23-25)**
   - Currently: `API_KEY = os.environ.get('X_API_KEY') or os.environ.get('API_KEY')`
   - Status: ✅ Already supports X_API_KEY as primary

2. **`routes/authenticate.py` (Line 26)**
   - Currently: `API_KEY = os.environ.get('API_KEY')`
   - Status: ❌ **NEEDS UPDATE** to use X_API_KEY

3. **`routes/v1/toolkit/authenticate.py` (Line 26)**
   - Currently: `API_KEY = os.environ.get('API_KEY')`
   - Status: ❌ **NEEDS UPDATE** to use X_API_KEY

4. **`services/authentication.py` (Lines 21, 28)**
   - Currently: Imports `API_KEY` from config.py
   - Status: ✅ Will work after config.py (already supports X_API_KEY)

##### Security Module Files:
5. **`server/security.py` (Lines 67-70)**
   - Currently: Uses `DB_TOKEN` exclusively
   - Status: ❌ **NEEDS DECISION** - Standardize on X_API_KEY or keep DB_TOKEN?

6. **`security_utils.py` (Lines 43-44, 96)**
   - Currently: Uses `OPENAI_API_KEY` and `DB_TOKEN` 
   - Status: ❌ **NEEDS DECISION** - Align with chosen standard

##### Health Check Files:
7. **`server/health.py` (Lines 25-26, 75)**
   - Currently: Checks for both `X_API_KEY` and `API_KEY`
   - Status: ✅ Already supports X_API_KEY as primary

### 3. Environment Configuration Files

#### `.env.example` (Line 13)
- Currently: `X_API_KEY=your-secure-api-key-minimum-32-characters-long`
- Status: ✅ Already uses X_API_KEY

#### `.env.local.minio.n8n.example` (Line 11)
- Currently: `API_KEY=local-dev-key-123`
- Status: ❌ **NEEDS UPDATE** to use X_API_KEY

## Required Changes Summary

### Immediate Priority (Break Authentication):
1. **`routes/authenticate.py`** - Change `os.environ.get('API_KEY')` to `os.environ.get('X_API_KEY')`
2. **`routes/v1/toolkit/authenticate.py`** - Change `os.environ.get('API_KEY')` to `os.environ.get('X_API_KEY')`
3. **`.env.local.minio.n8n.example`** - Change `API_KEY` to `X_API_KEY`

### Decision Needed (Security Architecture):
- **Standardize on variable name**: Should all authentication use `X_API_KEY` or `DB_TOKEN`?
- **server/security.py** - Currently uses `DB_TOKEN`, needs alignment decision
- **security_utils.py** - Currently uses `DB_TOKEN` and `OPENAI_API_KEY`, needs alignment decision

### Recommended Approach:
1. **Standardize on `X_API_KEY`** for all API authentication
2. **Update security modules** to use `X_API_KEY` instead of `DB_TOKEN`
3. **Keep `OPENAI_API_KEY`** as separate variable for OpenAI API calls (when implemented)

## Validation Required

After making changes, test these critical endpoints:
- `/authenticate`
- `/v1/toolkit/authenticate`
- All endpoints using `@require_api_key` decorator
- All endpoints using new security module authentication

## Files Not Requiring Changes

The following files contain references but are:
- **Documentation files** (*.md files)
- **Test files** (test_*.py files) 
- **CI/CD configuration** (.github/workflows/*.yml files)
- **Example/template files**

These should be updated for consistency but don't affect runtime authentication.

## Next Steps

1. **Decide on standard variable name** (recommend: `X_API_KEY`)
2. **Update the 3 critical authentication files**
3. **Update security modules** to use chosen standard
4. **Test authentication endpoints**
5. **Update documentation and examples** for consistency

---
*Audit completed: $(date)*
*Files scanned: 70+ files across the entire codebase*
