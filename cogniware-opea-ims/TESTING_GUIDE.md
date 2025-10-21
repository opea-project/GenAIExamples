# ✅ TESTING GUIDE - What to Check

## 🔍 Quick Debug Test

**Step 1: Open Debug Page**
```
http://localhost:8000/debug-check.html
```

**You should see:**
- ✓ Green checkmarks for all tests
- ✓ Examples rendered below
- ✓ Examples are clickable
- ✓ Clicking an example fills the input field

**If you see ✗ (red X):** Note which item failed and let me know.

---

## 🧪 Test Each Feature

### 1. Code Generation ✨

**URL:** http://localhost:8000/user-portal.html → Code Generation tab

**What you should see:**
1. Natural language input field
2. "✨ Process with CogniDream" button  
3. **5 example cards** below (REST API, Data Processing, etc.)
4. Each example should be clickable

**To test:**
1. Click "🌐 REST API Creation" example
2. Input field should fill with: "Create a complete REST API in Python..."
3. Click "✨ Process with CogniDream"
4. Should see:
   - Button changes to "⚙️ Processing..."
   - LLM execution cards appear
   - Code output appears
   - **📋 Copy** and **💾 Download** buttons

**Expected result:** Working code with download button

---

### 2. Documents 📄

**URL:** http://localhost:8000/user-portal.html → Documents tab

**What you should see:**
1. Natural language input field
2. **FILE UPLOAD section** with gradient purple background
   ```
   📤 Upload Document (Required)
   [Choose File] button
   ```
3. **5 example cards** below

**To test:**
1. Click "Choose File" → Select any PDF/DOCX
2. Should see: "✅ filename.pdf uploaded successfully!"
3. Click "📋 Contract Analysis" example
4. Click "✨ Process with CogniDream"
5. Should see processing → results

**Expected result:** File uploads, processing works, results shown

---

### 3. Browser Automation 🌐

**URL:** http://localhost:8000/user-portal.html → Browser Automation tab

**What you should see:**
1. Natural language input field
2. **URL INPUT field** with gradient purple background
   ```
   🌐 Website URL (Required)
   [https://google.com]
   ```
3. **5 example cards** below

**To test:**
1. URL field should show: `https://google.com`
2. Click "📸 Screenshot Capture" example
3. Input fills with: "Take a screenshot of google.com..."
4. Click "✨ Process with CogniDream"
5. Should see processing → results

**Expected result:** All examples clickable, processing works

---

### 4. Database Q&A 🗄️

**URL:** http://localhost:8000/user-portal.html → Database Q&A tab

**What you should see:**
1. Natural language input field
2. **DATABASE NAME field** with gradient purple background
   ```
   🗄️ Database Name (Required)
   [main_database]
   ```
3. **5 example cards** below

**To test:**
1. Database field should show: `main_database`
2. Click "👥 Customer Analytics" example
3. Input fills with: "Show me all customers..."
4. Click "✨ Process with CogniDream"
5. Should see processing → results

**Expected result:** All examples clickable, processing works

---

## 🐛 If Something Doesn't Work

### Examples Not Showing
**Open browser console (F12)**
Look for error messages. Should see:
```
User Portal: DOM loaded, initializing examples...
✅ Successfully rendered examples for code_generation
```

**If you see errors, copy and share them.**

### Examples Not Clickable
**Click an example and check console:**
Should see:
```
useExample called: code_generation Create a complete...
✅ Example text set successfully
```

**If nothing appears when clicking:** The onclick isn't working.

### File Upload Not Visible
**Check:**
- Go to Documents tab
- Look for a purple gradient card
- Should say "📤 Upload Document (Required)"
- Should have a file input button

**If not visible:** Share screenshot of what you see.

### Download Button Not Showing
**After generating code:**
- Should see "📋 Copy" button
- Should see "💾 Download" button
- Both should be in top-right of result card

**If not visible:** Check browser console for errors.

---

## 📊 What I Fixed

### Changes Made:
1. ✅ Added debug logging to all functions
2. ✅ Fixed button onclick handlers (added `this` parameter)
3. ✅ Created debug-check.html for testing
4. ✅ Added file upload section to Documents tab
5. ✅ Added URL input to Browser Automation
6. ✅ Added Database Name input to Database Q&A
7. ✅ Added download button to code results
8. ✅ Added copy button to all results
9. ✅ Made all required fields visible on load
10. ✅ Added validation for required fields

### File Locations:
- **Main HTML:** `/ui/user-portal.html`
- **Examples JS:** `/ui/workspace-examples.js`
- **Visualizer:** `/ui/parallel-llm-visualizer-enhanced.js`
- **Debug Page:** `/ui/debug-check.html`

---

## 🚀 Quick Test Commands

### Test file accessibility:
```bash
curl http://localhost:8000/workspace-examples.js | head -20
curl http://localhost:8000/parallel-llm-visualizer-enhanced.js | head -20
```

### Check if services running:
```bash
curl http://localhost:8000/
curl http://localhost:8090/health
```

---

## 📝 Reporting Issues

**Please provide:**

1. **Which feature** doesn't work
2. **What you see** vs what you expect
3. **Browser console output** (F12 → Console tab)
4. **Screenshot** if helpful

**Example good report:**
```
Feature: Code Generation examples
Issue: Examples don't appear
Console: "renderExamplesSection is not a function"
Screenshot: [shows empty space where examples should be]
```

This helps me fix it quickly!

---

## ✨ Services Running

All 6 services should be running:
- ✅ Admin (8099)
- ✅ Production (8090)
- ✅ Business Protected (8096)
- ✅ Business (8095)
- ✅ Demo (8080)
- ✅ Web Server (8000)

**Check with:**
```bash
./scripts/06_verify_deliverables.sh
```

---

**Ready to test! Start with:**
http://localhost:8000/debug-check.html

Then move to:
http://localhost:8000/user-portal.html

