# Troubleshooting: "Error generating timeline: 500: Failed to generate timeline"

## Common Causes & Solutions

### 1. **BAML Client Not Available** ⚠️
**Symptom**: Error 503 (not 500), but check anyway
**Solution**:
```bash
# Regenerate BAML client
./setup-qdrant.sh baml
# Or manually
uv run baml-cli generate
```

### 2. **Qdrant Connection Failed** 🔴
**Symptom**: No data retrieved from Qdrant
**Check**:
```bash
# Test Qdrant connection
./setup-qdrant.sh test

# Check if collections exist
python -c "from src.qdrant_setup import create_qdrant_client; from src.config import get_config; client = create_qdrant_client(get_config()); print([c.name for c in client.get_collections().collections])"
```

**Solution**:
- If using Cloud: Verify `QDRANT_URL` and `QDRANT_API_KEY` in `.env`
- If using Docker: Ensure Docker is running
- Re-initialize collections: `./setup-qdrant.sh init`
- Ingest data: `./setup-qdrant.sh ingest`

### 3. **No Data in Qdrant** 📊
**Symptom**: Empty collections
**Check**:
```bash
python -c "from src.qdrant_setup import create_qdrant_client; from src.config import get_config; client = create_qdrant_client(get_config()); info = client.get_collection('x_posts'); print(f'Posts: {info.points_count}')"
```

**Solution**:
```bash
# Ingest mock data
./setup-qdrant.sh ingest
# Or manually
python -m src.cli ingest mock
```

### 4. **Google API Key Missing/Invalid** 🔑
**Symptom**: BAML calls fail
**Check**:
```bash
# Verify .env has GOOGLE_API_KEY
cat .env | grep GOOGLE_API_KEY
```

**Solution**:
- Add valid Google API key to `.env`
- Restart backend after adding

### 5. **BAML GenerateTimeline Call Fails** 🤖
**Symptom**: BAML client available but call fails
**Possible causes**:
- Invalid query format
- Context too large
- API rate limits
- Network issues

**Check backend logs**:
```bash
# Look for BAML errors in backend terminal
# Or check logs if running in background
```

**Solution**:
- Check backend terminal for detailed error
- Verify Google API key is valid
- Try simpler query
- Check API quota/limits

### 6. **Query Processing Fails** 🔍
**Symptom**: `_process_query` throws exception
**Check**:
- BAML `ProcessQuery` function available
- Query is not empty

**Solution**:
- Ensure BAML client is generated
- Try different query format

### 7. **Context Retrieval Fails** 📚
**Symptom**: `_retrieve_context` throws exception
**Possible causes**:
- Qdrant connection lost
- Collection doesn't exist
- Search query malformed

**Solution**:
- Re-initialize collections: `./setup-qdrant.sh init`
- Check Qdrant connection: `./setup-qdrant.sh test`

### 8. **Import Errors** 📦
**Symptom**: Module not found errors
**Check**:
```bash
# Verify virtual environment is activated
which python  # Should show .venv path

# Verify dependencies installed
python -c "import baml_client; print('BAML OK')"
python -c "from src.timeline_builder import TimelineBuilder; print('TimelineBuilder OK')"
```

**Solution**:
```bash
# Reinstall dependencies
uv sync

# Regenerate BAML
uv run baml-cli generate
```

## Diagnostic Steps

### Step 1: Check Backend Logs
Look at the backend terminal output for detailed error messages. The error should show:
- Which step failed (query processing, context retrieval, BAML call)
- The actual exception message
- Stack trace

### Step 2: Test Components Individually

```bash
# 1. Test Qdrant
./setup-qdrant.sh test

# 2. Test BAML import
python -c "from baml_client.baml_client import b; print('BAML OK')"

# 3. Test timeline builder
python -c "
from src.timeline_builder import TimelineBuilder
from src.qdrant_setup import create_qdrant_client
from src.config import get_config
client = create_qdrant_client(get_config())
builder = TimelineBuilder(qdrant_client=client)
result = builder.build_timeline('test query', limit=5)
print('Result:', result is not None)
"

# 4. Test API endpoint directly
curl -X POST http://localhost:8000/api/timeline \
  -H "Content-Type: application/json" \
  -d '{"topic": "test", "limit": 5}'
```

### Step 3: Check Health Endpoint

```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "baml_available": true,
  "qdrant_connected": true
}
```

If `baml_available` is `false`:
- Run `./setup-qdrant.sh baml`

If `qdrant_connected` is `false`:
- Check Qdrant connection
- Verify `.env` configuration

## Quick Fix Checklist

- [ ] BAML client generated: `./setup-qdrant.sh baml`
- [ ] Qdrant connected: `./setup-qdrant.sh test`
- [ ] Collections initialized: `./setup-qdrant.sh init`
- [ ] Data ingested: `./setup-qdrant.sh ingest`
- [ ] Google API key set in `.env`
- [ ] Backend restarted after changes
- [ ] Virtual environment activated
- [ ] Dependencies installed: `uv sync`

## Most Common Fix

**90% of cases**: Missing data in Qdrant

```bash
# Complete reset and setup
./setup-qdrant.sh init
./setup-qdrant.sh ingest
# Restart backend
./start.sh
```

## Getting Detailed Error

To see the actual error (not just "Failed to generate timeline"):

1. Check backend terminal output
2. Or modify `src/api.py` line 185 to log more details:
```python
detail=f"Error generating timeline: {str(e)}"  # Already shows error
```

The backend should already log the full error with stack trace. Check the terminal where you ran `./start.sh` or `python -m src.api`.

