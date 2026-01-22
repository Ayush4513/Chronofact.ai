# How to View Backend Errors in Git Bash

When running `./start.sh`, the backend runs in the background. Here's how to see its errors:

## Method 1: View Log File in Real-Time (Recommended)

Open a **new Git Bash terminal** and run:

```bash
cd "C:\Users\lenovo\OneDrive\Desktop\Convolve 4.0\Qdrant\Chronofact.ai"
./view-backend-logs.sh
```

This will show backend logs in real-time. Press `Ctrl+C` to exit.

## Method 2: View Last N Lines

To see the last 50 lines of logs:

```bash
tail -n 50 logs/backend.log
```

Or continuously watch the last 20 lines:

```bash
watch -n 1 'tail -20 logs/backend.log'
```

## Method 3: Search for Errors

To find all error messages:

```bash
grep -i error logs/backend.log
```

Or see errors with context (5 lines before/after):

```bash
grep -i -A 5 -B 5 error logs/backend.log
```

## Method 4: Run Backend in Foreground (For Debugging)

If you want to see errors directly in the terminal, stop `start.sh` and run the backend separately:

```bash
# Stop start.sh (Ctrl+C)

# Activate virtual environment
source .venv/Scripts/activate  # Git Bash
# OR
.venv/Scripts/activate.bat      # If using cmd

# Run backend in foreground
cd "C:\Users\lenovo\OneDrive\Desktop\Convolve 4.0\Qdrant\Chronofact.ai"
python -m src.api
```

This will show all backend output directly in the terminal.

## Method 5: Check Log File Location

The backend log file is saved at:
```
Chronofact.ai/logs/backend.log
```

You can open this file in any text editor to see the full log history.

## Quick Commands

```bash
# View last 100 lines
tail -n 100 logs/backend.log

# Follow logs in real-time
tail -f logs/backend.log

# Search for specific errors
grep "Error\|Exception\|Traceback" logs/backend.log

# View only errors
grep -i error logs/backend.log | tail -20
```

## What to Look For

When debugging the 500 error, look for:

1. **BAML errors**: `BAML error`, `baml`, `coroutine`
2. **Qdrant errors**: `Qdrant`, `connection`, `collection`
3. **API errors**: `API key`, `authentication`, `quota`
4. **Python errors**: `Traceback`, `Exception`, `Error`

The logs will show the **full stack trace** and **detailed error messages** that will help identify the issue.

