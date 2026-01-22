# Troubleshooting Guide

Common issues encountered during setup and operation of Continue VS Code extension with GenAI Gateway, along with solutions.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Authentication Issues](#authentication-issues)
- [Autocomplete Issues](#autocomplete-issues)
- [Chat Mode Issues](#chat-mode-issues)
- [Edit Mode Issues](#edit-mode-issues)
- [Plan and Agent Mode Issues](#plan-and-agent-mode-issues)
- [Performance Issues](#performance-issues)
- [General Debugging](#general-debugging)

---

## Installation Issues

### Continue Extension Not Found

**Solution:**

1. Open VS Code Extensions (`Ctrl+Shift+X`)
2. Search for exact name: "Continue"
3. Publisher must be "Continue"
4. Extension ID: `Continue.continue`
5. Verify VS Code is updated to latest version

### Continue Icon Not Appearing

**Solution:**

1. Restart VS Code completely
2. Check Extensions view - ensure extension is enabled
3. Look for Continue icon in Activity Bar (left sidebar)
4. Test keyboard shortcut `Ctrl+L`
5. Reinstall extension if issue persists

---

## Configuration Issues

### Config File Not Found

**Solution:**

Configuration file location:

**Windows:**
```
C:\Users\<username>\.continue\config.yaml
```

**macOS/Linux:**
```
~/.continue/config.yaml
```

Create the file via Command Palette: `Ctrl+Shift+P` → "Continue: Open config.yaml"

### Invalid YAML Syntax

**Solution:**

1. Use spaces for indentation (not tabs)
2. Verify quotes around special characters
3. Check list and array formatting
4. Validate with online YAML validator
5. Compare against working example in README

### Model Not Found

**Solution:**

1. Model names are case-sensitive
2. Verify exact model name from Gateway:
```bash
curl -k https://api.example.com/v1/models \
  -H "Authorization: Bearer your-api-key-here"
```
3. Update config with exact match from response
4. For this setup, use: `meta-llama/Llama-3.2-3B-Instruct`

### API Base URL Errors

**Solution:**

1. URL must include `/v1` suffix:
```yaml
apiBase: "https://api.example.com/v1"
```
2. Verify URL is accessible:
```bash
curl -k https://api.example.com/v1/models
```
3. Remove trailing slashes from URL

### Model Timeout Missing

**Critical Issue:** Autocomplete requests fail with "Operation Aborted" errors.

**Solution:**

Add `modelTimeout` to `tabAutocompleteOptions` in config.yaml:
```yaml
tabAutocompleteOptions:
  modelTimeout: 10000
```

This setting is critical for CPU-based inference which takes 5-10 seconds. Default timeout is 150ms, which is too short.

### Settings Not Applied from Config

**Issue:** Config.yaml changes do not take effect.

**Solution:**

VS Code settings have the highest priority and override config.yaml values. Check these in order:

1. **VS Code User Settings (Highest Priority):** Open `settings.json` and verify critical settings:
   - `editor.inlineSuggest.enabled: true` (CRITICAL - must be enabled)
   - `continue.enableTabAutocomplete: true`

   See [SETUP_GUIDE.md - Required VS Code Settings](./SETUP_GUIDE.md#required-vs-code-settings) for complete configuration details.

2. **Continue UI Settings:** Click Continue icon → Settings (gear icon) and verify:
   - Autocomplete Timeout: 10000ms
   - Autocomplete Debounce: 3000ms
   - Max Tokens: Match your config

3. **Reload VS Code:** `Ctrl+Shift+P` → "Developer: Reload Window"

**Settings Priority Order:**
```
VS Code User Settings (settings.json) > Continue UI Settings > config.yaml > Hardcoded Defaults
```

---

## Authentication Issues

### Invalid API Key

**Solution:**

1. Verify API key matches Gateway credentials
2. Test API key manually:
```bash
curl -k https://api.example.com/v1/models \
  -H "Authorization: Bearer your-api-key-here"
```
3. Check for extra spaces in API key
4. Ensure `sk-` prefix is present
5. Request new API key if expired

### SSL Certificate Errors

**Solution:**

Add to config for self-signed certificates:
```yaml
ignoreSSL: true
verifySsl: false
```

Only use on trusted internal networks.

### Connection Timeout

**Solution:**

1. Verify network connectivity:
```bash
ping api.example.com
```
2. Check Gateway status:
```bash
curl -k https://api.example.com/health
```
3. Verify firewall allows outbound HTTPS (port 443)
4. Check DNS resolution
5. Ensure VPN is connected if required

---

## Autocomplete Issues

### No Suggestions Appearing

**Solution:**

1. Enable autocomplete in status bar:
   - Click "Continue" in status bar
   - Check "Enable Tab Autocomplete"
2. Verify model has `autocomplete` role in config
3. Check `useLegacyCompletionsEndpoint: true` is set
4. Verify `modelTimeout: 10000` is present in `tabAutocompleteOptions`
5. Restart VS Code
6. Test after pausing 3 seconds following typing

### Autocomplete Timeouts

**Issue:** All autocomplete requests timeout with "Operation Aborted" error.

**Solution:**

Add or update `modelTimeout` in config.yaml:
```yaml
tabAutocompleteOptions:
  modelTimeout: 10000
```

CPU-based inference requires 5-10 seconds. Default 150ms timeout is insufficient.

### Multiple Rapid Requests

**Issue:** Too many autocomplete requests sent in short time (10+ per minute).

**Solution:**

1. Increase `debounceDelay` in config.yaml:
```yaml
tabAutocompleteOptions:
  debounceDelay: 3000
```
2. Type complete line before pausing
3. Wait for debounce timer to expire (3 seconds)
4. Avoid typing while autocomplete is generating

### Suggestions Continue After Accepting

**Solution:**

1. Start typing immediately after pressing Tab
2. Debounce timer resets with new keystrokes
3. Disable autocomplete temporarily if distracting

### Autocomplete in Markdown Files

**Solution:**

Autocomplete is disabled in `.md` files by default. To enable:

1. Edit config.yaml:
```yaml
tabAutocompleteOptions:
  disableInFiles:
    # - "*.md"  # Comment out to enable
```
2. Reload VS Code

### Low Quality or Repetitive Completions

**Issue:** Completions generate repetitive or irrelevant code.

**Solution:**

1. Verify `autocompleteOptions` is configured:
```yaml
autocompleteOptions:
  maxTokens: 256
  temperature: 0.2
  stop:
    - "\n\n\n"
    - "# "
```
2. Check temperature is low (0.2) for consistency
3. Ensure `maxTokens` is limited (256) for faster completions
4. Test in clean files without repetitive patterns

---

## Chat Mode Issues

### No Response in Chat

**Solution:**

1. Check VS Code Output panel:
   - View → Output
   - Select "Continue" from dropdown
2. Test API manually:
```bash
curl -k https://api.example.com/v1/chat/completions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```
3. Verify model has `chat` role in config
4. Restart VS Code
5. Start fresh chat session (`Ctrl+L`)

### Context Too Large Errors

**Issue:** Error message stating context exceeds model's maximum capacity.

**Solution:**

1. Reduce `maxTokens` in config:
```yaml
completionOptions:
  maxTokens: 1024
```
2. Limit highlighted code blocks
3. Reduce `@Files` references to 2-3 files
4. Start fresh chat session
5. Avoid including large files (>1000 lines)

---

## Edit Mode Issues

### Edit Mode Not Responding

**Solution:**

1. Verify model has `edit` role in config
2. Check keyboard shortcut:
   - Windows/Linux: `Ctrl+I`
   - Mac: `Cmd+I`
3. Try alternative method:
   - Highlight code
   - Open Continue sidebar
   - Switch to Edit mode manually
4. Check VS Code Output panel for errors

### Diff Not Showing

**Solution:**

1. Ensure code is highlighted before pressing `Ctrl+I`
2. Provide clear instruction in edit prompt
3. Wait for model response to complete
4. Check Output panel for errors

---

## Plan and Agent Mode Issues

### Context Window Exceeded in Plan Mode

**Issue:** Error message "max_tokens is too large" when using Plan mode.

**Example Error:**
```
'max_tokens' or 'max_completion_tokens' is too large: 2048.
This model's maximum context length is 8192 tokens and your
request has 5638 input tokens
```

**Solution:**

Plan mode includes large system prompts (5000+ tokens). Reduce response tokens:

1. Lower `maxTokens` in config:
```yaml
completionOptions:
  maxTokens: 1024
```
2. Avoid complex tasks requiring long responses
3. Disable tools in UI settings if not needed:
   - Open Continue sidebar
   - Click settings icon
   - Disable unused tool options

### Context Window Exceeded in Agent Mode

**Issue:** Similar to Plan mode but with higher token usage (7000-9000 tokens).

**Solution:**

Agent mode requires more context than Plan mode. Apply same fixes:

1. Reduce `maxTokens` to 1024 or lower
2. Break tasks into smaller operations
3. Use simpler instructions
4. Consider using Chat or Edit mode for single operations

### Agent Mode Disabled or Limited

**Solution:**

1. Verify model supports tool calling
2. Check Continue output logs for compatibility messages
3. Use Plan mode as alternative for read-only operations
4. Use Edit mode for single file modifications

### Tool Call Failures

**Solution:**

1. Review tool permission prompts carefully
2. Verify file paths exist before operations
3. Check write permissions for file edits
4. Break complex tasks into 1-2 step operations

---

## Performance Issues

### Slow Response Times

**Solution:**

1. Test network latency:
```bash
ping api.example.com
```
2. Reduce context size in config:
```yaml
contextLength: 4096
completionOptions:
  maxTokens: 1024
```
3. Limit context providers:
   - Avoid `@Codebase` for large projects
   - Limit `@Files` to 2-3 files
   - Exclude large files
4. Verify Gateway has sufficient resources

### High Memory Usage

**Solution:**

1. Restart VS Code to clear cache
2. Avoid `@Codebase` on large projects
3. Close unused VS Code windows
4. Limit file references in context

### Autocomplete Latency

**Issue:** Autocomplete takes too long to respond.

**Solution:**

1. Verify `debounceDelay` is set appropriately:
```yaml
tabAutocompleteOptions:
  debounceDelay: 3000
```
2. Check `maxPromptTokens` is limited:
```yaml
tabAutocompleteOptions:
  maxPromptTokens: 100
```
3. Reduce `maxTokens` in `autocompleteOptions`:
```yaml
autocompleteOptions:
  maxTokens: 256
```
4. Set `prefixPercentage: 1.0` and `suffixPercentage: 0.0` to reduce context

---

## General Debugging

### Check Continue Version

1. Open Extensions (`Ctrl+Shift+X`)
2. Find Continue extension
3. Verify version is latest
4. Update if outdated

### Enable Debug Logging

1. Open VS Code Developer Tools:
   - `Ctrl+Shift+P` → "Toggle Developer Tools"
2. Click Console tab
3. Look for Continue errors

### View Continue Output

1. Open Output panel: View → Output
2. Select "Continue" from dropdown
3. Review logs for errors and warnings

### Reset Configuration

Backup and reset config if all else fails:

```bash
# Windows
copy C:\Users\USERNAME\.continue\config.yaml config.yaml.backup
del C:\Users\USERNAME\.continue\config.yaml

# Linux/Mac
cp ~/.continue/config.yaml config.yaml.backup
rm ~/.continue/config.yaml
```

Restart VS Code and reconfigure from scratch.

### Test Gateway Directly

Bypass Continue to isolate issues:

```bash
# Test models endpoint
curl -k https://api.example.com/v1/models \
  -H "Authorization: Bearer your-api-key-here"

# Test chat endpoint
curl -k https://api.example.com/v1/chat/completions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [{"role": "user", "content": "Test"}],
    "max_tokens": 50
  }'

# Test completions endpoint
curl -k https://api.example.com/v1/completions \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.2-3B-Instruct",
    "prompt": "def hello():\n    ",
    "max_tokens": 100
  }'
```

If manual tests work, the issue is in Continue configuration.

### Verify Configuration Values

Check that critical values are present in config.yaml:

```yaml
tabAutocompleteOptions:
  debounceDelay: 3000
  modelTimeout: 10000
  maxPromptTokens: 100

models:
  - autocompleteOptions:
      maxTokens: 256
      temperature: 0.2
```

### Restart Checklist

1. Reload Continue: Command Palette → "Continue: Reload"
2. Restart VS Code: Close and reopen
3. Clear cache: Delete `~/.continue/cache/` folder
4. Reinstall extension: Uninstall → Restart → Install → Restart

### Common Configuration Mistakes

**Missing modelTimeout:**
```yaml
# Wrong - missing modelTimeout
tabAutocompleteOptions:
  debounceDelay: 3000

# Correct
tabAutocompleteOptions:
  debounceDelay: 3000
  modelTimeout: 10000
```

**Wrong API Base URL:**
```yaml
# Wrong - missing /v1 suffix
apiBase: "https://api.example.com"

# Correct
apiBase: "https://api.example.com/v1"
```

**Missing autocompleteOptions:**
```yaml
# Wrong - only completionOptions
models:
  - completionOptions:
      maxTokens: 2048

# Correct - both sections
models:
  - completionOptions:
      maxTokens: 2048
    autocompleteOptions:
      maxTokens: 256
      temperature: 0.2
```

**Missing Legacy Endpoint:**
```yaml
# Wrong - missing setting
experimental:
  inlineEditing: true

# Correct
useLegacyCompletionsEndpoint: true
experimental:
  inlineEditing: true
```

---

## Additional Help

If issues persist after following this guide:

1. Check Continue documentation: https://docs.continue.dev/
2. Review [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed configuration, FIM templates, custom rules, and MCP servers
3. Verify GenAI Gateway logs for backend errors
4. Contact Gateway administrator for API issues
