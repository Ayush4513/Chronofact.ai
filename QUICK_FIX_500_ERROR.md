# Quick Fix: 500 Error - Failed to Generate Timeline

## Most Common Causes (90% of cases)

### 1. **No Data in Qdrant** ⭐ MOST COMMON
**Fix**:
```bash
./setup-qdrant.sh ingest
```

### 2. **BAML Client Not Generated**
**Fix**:
```bash
./setup-qdrant.sh baml
```

### 3. **Qdrant Not Connected**
**Fix**:
```bash
# Test connection
./setup-qdrant.sh test

# If fails, re-initialize
./setup-qdrant.sh init
```

### 4. **Google API Key Missing/Invalid**
**Fix**:
- Check `.env` has `GOOGLE_API_KEY=your-key`
- Restart backend after adding

## Complete Reset (If Nothing Works)

```bash
# 1. Stop everything
./stop.sh

# 2. Regenerate BAML
./setup-qdrant.sh baml

# 3. Re-initialize Qdrant
./setup-qdrant.sh init

# 4. Ingest data
./setup-qdrant.sh ingest

# 5. Restart
./start.sh
```

## Check Backend Logs

The backend terminal will show the **actual error**. Look for:
- `BAML error:` - BAML client issue
- `Qdrant error:` - Qdrant connection issue
- `API error:` - Google API key issue
- `Error building timeline:` - General error with details

## Quick Diagnostic

```bash
# Check health
curl http://localhost:8000/health

# Should show:
# {
#   "status": "healthy",
#   "baml_available": true,
#   "qdrant_connected": true
# }
```

If `baml_available: false` → Run `./setup-qdrant.sh baml`
If `qdrant_connected: false` → Check Qdrant connection

---

**Most likely fix**: Run `./setup-qdrant.sh ingest` and restart backend.

