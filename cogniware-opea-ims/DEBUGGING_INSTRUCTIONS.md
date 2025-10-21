# 🔍 DEBUGGING INSTRUCTIONS

## Testing the Examples System

### 1. Open Debug Page
Open in your browser: **http://localhost:8000/debug-check.html**

This page will show:
- ✓ Which scripts loaded successfully
- ✓ Which functions are available
- ✓ Which input fields exist
- ✓ Which example divs exist
- ✓ Actual rendered examples

### 2. Check Browser Console

Open browser developer tools (F12) and look for:

**Expected Console Output:**
```
Debug page loaded
✓ renderExamplesSection function found
✓ useExample function found
✓ workspaceExamples object found
...
✓ Successfully rendered code_generation examples
✓ Successfully rendered browser examples
✓ Successfully rendered database examples
✓ Successfully rendered documents examples
```

**If you see errors, note them down**

### 3. Test User Portal

Open: **http://localhost:8000/user-portal.html**

**Open Browser Console (F12) and look for:**
```
User Portal: DOM loaded, initializing examples...
renderExamplesSection function available? function
Module: code_generation, Div ID: codegenerationExamples, Found: true
✅ Successfully rendered examples for code_generation
...
```

### 4. Test Examples Functionality

**In User Portal:**

1. Go to "Code Generation" tab
2. Open browser console (F12)
3. Click any example
4. You should see:
   ```
   useExample called: code_generation Create a complete REST API...
   Looking for input: nlCodeInput
   Input element found? true
   ✅ Example text set successfully
   ```
5. The input field should be filled with the example text

### 5. Test File Upload (Documents)

1. Go to "Documents" tab
2. You should see a **file upload button** with gradient background
3. Try uploading a PDF/DOCX file
4. You should see "✅ filename uploaded successfully!"

### 6. Test Required Fields

**Browser Automation:**
- Should see URL input field pre-filled with `https://google.com`

**Database Q&A:**
- Should see Database Name field pre-filled with `main_database`

### 7. Test Processing

1. Click any example (should fill input)
2. Click "✨ Process with CogniDream"
3. Button should show "⚙️ Processing..." with spinner
4. Should see LLM execution cards
5. Should see results with Copy/Download buttons

## Common Issues & Solutions

### Issue: Examples not appearing

**Check:**
```javascript
// In browser console, type:
typeof renderExamplesSection
// Should return: "function"

document.getElementById('codegenerationExamples')
// Should return: <div> element, not null
```

**Fix:** If function not found, check if `workspace-examples.js` loaded:
```
http://localhost:8000/workspace-examples.js
```

### Issue: Examples not clickable

**Check:**
```javascript
// Click an example, should see in console:
useExample called: code_generation ...
```

**If nothing happens:** The onclick handler isn't firing. Check HTML for `onclick="useExample(...)"`

### Issue: File upload not visible

**Check:**
```javascript
document.getElementById('docFileUpload')
// Should return: <input> element
```

**Navigate to Documents tab and inspect the page** - you should see a gradient card with file input.

### Issue: Download button not showing

**Check console after code generation:**
```javascript
// Should see button with:
onclick="downloadCode(`...`, 'cogniware_generated.py')"
```

## Quick Fixes

### If workspace-examples.js not loading:
```bash
cd /home/deadbrainviv/Documents/GitHub/cogniware-core/ui
ls -la workspace-examples.js
# Should exist and be readable
```

### If examples still not rendering:
Check the setTimeout in user-portal.html - might need longer delay.

### If buttons not working:
Check browser console for JavaScript errors.

## Report Format

**Please provide:**
1. Debug page output (screenshot or text)
2. Browser console output from user-portal.html
3. Which specific feature isn't working
4. Any error messages you see

This will help identify the exact issue quickly!

