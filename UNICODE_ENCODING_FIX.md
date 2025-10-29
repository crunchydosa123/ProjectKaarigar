# Unicode Encoding Fix - Windows Console

## 🐛 Issue
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 2: character maps to <undefined>
```

The listing generation script (`3_listing_model.py`) was failing when trying to print Unicode characters like:
- `→` (arrow, \u2192)
- `✓` (checkmark)
- `✗` (cross)
- `⬇` (down arrow)

## 🔍 Root Cause

**Windows Console Encoding**

Windows command prompt uses CP1252 (Windows-1252) encoding by default, which doesn't support Unicode characters. When Python tries to print Unicode characters to stdout/stderr, it fails with a `UnicodeEncodeError`.

## ✅ Solution

Applied a **two-part fix**:

### 1. Python Script Configuration (`3_listing_model.py`)

Added UTF-8 encoding configuration at the top of the file:

```python
# -*- coding: utf-8 -*-
import os
import re
import sys
# ... other imports ...

# Configure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    # Set UTF-8 for stdout and stderr to handle Unicode characters
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

**What this does**:
- Detects Windows platform
- Wraps stdout and stderr with UTF-8 encoding
- Uses `errors='replace'` to substitute unsupported characters instead of crashing

### 2. Subprocess Configuration (`marketplace_listing.py`)

Updated subprocess call to explicitly use UTF-8:

```python
# Set UTF-8 environment for subprocess to handle Unicode characters
env = os.environ.copy()
env['PYTHONIOENCODING'] = 'utf-8'

process = subprocess.run(
    [sys.executable, listing_script],
    input=input_text,
    capture_output=True,
    text=True,
    timeout=120,
    cwd=model_dir,
    env=env,
    encoding='utf-8',      # ✅ Explicitly set UTF-8
    errors='replace'       # ✅ Replace unsupported characters
)
```

**What this does**:
- Sets `PYTHONIOENCODING=utf-8` environment variable
- Explicitly specifies `encoding='utf-8'` for subprocess
- Uses `errors='replace'` to handle any encoding issues gracefully

## 📝 Changes Made

### File: `Model/3_listing_model.py`

**Lines 1-7**: Added UTF-8 configuration
- Added encoding declaration: `# -*- coding: utf-8 -*-`
- Added Windows-specific stdout/stderr wrapper with UTF-8 encoding
- Only applies on Windows platform (checked via `sys.platform`)

### File: `backend/routes/marketplace_listing.py`

**Lines ~120-133**: Updated subprocess call
- Added `PYTHONIOENCODING` environment variable
- Added `encoding='utf-8'` parameter to subprocess.run()
- Added `errors='replace'` parameter for graceful error handling

## 🚀 Test Steps

1. **Restart Backend Server**:
   ```powershell
   # Stop with Ctrl+C, then:
   cd D:\Barclays\ProjectKaarigar\backend
   python app.py
   ```

2. **Try Listing Again**:
   - Open product detail page
   - Click "List on Marketplace" → Select Amazon
   - Watch backend logs

3. **Expected Output**:
   ```
   ✅ Product fetched successfully
      📦 Product Name: Red Pot
      💰 Product Price: 200
   📸 Image URLs (1):
      1. https://storage.googleapis.com/...
   🚀 Starting listing generation subprocess...
   ✅ Subprocess completed!
      Return code: 0  ✅ (Should be 0, not 1)
   ```

## 🎯 Why This Approach

### Alternative Solutions Considered:

1. **Remove Unicode characters** ❌
   - Loses visual clarity in logs
   - Makes debugging harder

2. **Use ASCII-only** ❌
   - Less user-friendly output
   - Doesn't solve root cause

3. **Change Windows console encoding** ❌
   - Requires user configuration
   - Not portable/automated

4. **UTF-8 configuration (CHOSEN)** ✅
   - Handles Unicode properly
   - Works automatically
   - Graceful fallback with `errors='replace'`
   - No user configuration needed

## 📊 Technical Details

### Python Encoding Chain:

```
Script (UTF-8 source)
  ↓
sys.stdout (wrapped with UTF-8)
  ↓
subprocess.run (encoding='utf-8')
  ↓
Backend logs (UTF-8)
  ↓
Console output ✅
```

### Error Handling:

- `errors='replace'`: Replaces unsupported chars with `?`
- Prevents crashes
- Allows script to continue execution

## ✅ Status

**FIXED** - The listing generation script now handles Unicode characters properly on Windows.

---

**Date**: October 30, 2025  
**Issue**: UnicodeEncodeError with Unicode characters (→, ✓, ✗, ⬇)  
**Cause**: Windows CP1252 encoding doesn't support Unicode  
**Fix**: UTF-8 configuration in script + subprocess
