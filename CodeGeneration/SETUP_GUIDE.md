# Continue Extension Setup Guide

Comprehensive configuration guide for Continue VS Code extension with GenAI Gateway backend using Meta Llama 3.2 3B Instruct model.

## Table of Contents

- [Understanding Continue Modes](#understanding-continue-modes)
- [Installation](#installation)
- [Configuration](#configuration)
- [Configuration Variables Reference](#configuration-variables-reference)
- [FIM Template Formats](#fim-template-formats)
- [Feature Usage](#feature-usage)
- [Best Practices](#best-practices)
- [Advanced Configuration](#advanced-configuration)
- [Custom Rules](#custom-rules)
- [MCP Servers](#mcp-servers-model-context-protocol)

---

## Understanding Continue Modes

Continue provides five interaction modes for different development workflows:

### 1. Chat Mode

Interactive AI assistant for code discussions and problem-solving.

**Capabilities:**
- Answer questions about code
- Explain code functionality
- Provide implementation suggestions
- Debug issues with conversation context

**Keyboard Shortcuts:**
- VS Code: `Ctrl+L` (Windows/Linux) or `Cmd+L` (Mac)

**How It Works:**
- Gathers context from selected code, current file, and conversation history
- Constructs prompt with user input and context
- Streams real-time response from AI model
- Provides action buttons to apply, insert, or copy code

**Best For:** Quick interactions, code explanations, iterative problem-solving

### 2. Edit Mode

Targeted code modifications using natural language instructions.

**Capabilities:**
- Refactor selected code
- Add documentation and comments
- Fix bugs in specific sections
- Convert code between languages
- Apply formatting changes

**Keyboard Shortcut:** `Ctrl+I` (Windows/Linux) or `Cmd+I` (Mac)

**How It Works:**
1. Captures highlighted code and current file contents
2. Sends context and user instructions to AI model
3. Streams proposed changes with diff formatting
4. User accepts or rejects changes

**Best For:** Precise, localized code modifications

### 3. Autocomplete

Intelligent inline code suggestions as you type.

**Capabilities:**
- Context-aware code completion
- Multi-line suggestions
- Function implementations
- Boilerplate code generation

**Keyboard Shortcuts:**
- Accept: `Tab`
- Reject: `Esc`
- Partial accept: `Ctrl+→` or `Cmd+→`
- Force trigger: `Ctrl+Alt+Space` or `Cmd+Alt+Space`

**How It Works:**
- Uses debouncing to prevent requests on every keystroke
- Retrieves relevant code snippets from codebase
- Caches suggestions for rapid reuse
- Post-processes AI output (removes tokens, fixes indentation)

**Best For:** Fast, inline coding assistance without breaking flow

### 4. Plan Mode

Read-only exploration mode for safe codebase analysis.

**Capabilities:**
- Read project files
- Search code using grep and glob patterns
- View repository structure and diffs
- Fetch web content for context
- NO file editing or terminal commands

**Keyboard Shortcut:** `Ctrl+.` or `Cmd+.` to cycle modes

**How It Works:**
- Same as Agent mode but filters tools to read-only operations
- Prevents accidental modifications
- Allows safe exploration of unfamiliar codebases

**Best For:** Understanding codebases, planning implementations before execution

### 5. Agent Mode

Autonomous coding assistant with tool access for complex, multi-step tasks.

**Capabilities:**
- Read and analyze multiple files
- Create and edit files
- Run terminal commands
- Search codebase
- Execute multi-step implementations

**Keyboard Shortcut:** `Ctrl+.` or `Cmd+.` to cycle modes

**How It Works:**
- Receives available tools alongside user requests
- Model proposes tool calls (read file, edit file, run command)
- User grants permission (or auto-approval if configured)
- Tool executes and returns results
- Process repeats iteratively until task complete

**Requirements:**
- Model must support tool calling (function calling)
- Requires larger context windows for multi-step operations

**Best For:** Implementing features, fixing bugs, running tests, refactoring

---

## Installation

### Step 1: Install Continue Extension

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search for "Continue"
4. Install: **Continue - open-source AI code agent**
5. Publisher: **Continue**
6. Extension ID: `Continue.continue`

### Step 2: Verify Installation

- Continue icon should appear in left sidebar
- Test keyboard shortcut: `Ctrl+L` should open Continue chat
- Status bar should show "Continue" button

---

## Configuration

### Configuration File Location

Continue uses a YAML configuration file located at:

**Windows:**
```
C:\Users\<username>\.continue\config.yaml
```

**macOS/Linux:**
```
~/.continue/config.yaml
```

**Access via Command Palette:**
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: "Continue: Open config.yaml"
3. Press Enter

### Complete Configuration

Replace your `config.yaml` with the following configuration:

```yaml
name: GenAI Gateway Config
version: 1.0.0
schema: v1

tabAutocompleteOptions:
  multilineCompletions: "always"
  debounceDelay: 3000
  maxPromptTokens: 100
  prefixPercentage: 1.0
  suffixPercentage: 0.0
  maxSuffixPercentage: 0.0
  modelTimeout: 10000
  showWhateverWeHaveAtXMs: 2000
  useCache: true
  onlyMyCode: true
  useRecentlyEdited: true
  useRecentlyOpened: true
  useImports: true
  transform: true
  experimental_includeClipboard: false
  experimental_includeRecentlyVisitedRanges: true
  experimental_includeRecentlyEditedRanges: true
  experimental_includeDiff: true
  disableInFiles:
    - "*.md"

models:
  - name: "Llama 3.2 3B (Chat & Agent + Autocomplete)"
    provider: openai
    model: "meta-llama/Llama-3.2-3B-Instruct"
    apiBase: "https://api.example.com/v1"
    apiKey: "your-api-key-here"
    ignoreSSL: true
    contextLength: 8192
    completionOptions:
      maxTokens: 2048
      temperature: 0.1
      stop:
        - "\n\n"
        - "def "
        - "class "
    requestOptions:
      maxTokens: 2048
      temperature: 0.1
    autocompleteOptions:
      maxTokens: 256
      temperature: 0.2
      stop:
        - "\n\n\n"
        - "# "
    roles:
      - chat
      - edit
      - apply
      - autocomplete
    promptTemplates:
      autocomplete: "{{{prefix}}}"

useLegacyCompletionsEndpoint: true
experimental:
  inlineEditing: true
allowAnonymousTelemetry: false
```

### Apply Configuration

1. Save the `config.yaml` file
2. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"

### Required VS Code Settings

Continue requires specific VS Code settings to function properly. These settings **override** values in `config.yaml`, so they must be configured correctly.

#### Access VS Code Settings

**Method 1: Command Palette**
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type: "Preferences: Open User Settings (JSON)"
3. Press Enter

**Method 2: Settings UI**
1. Go to File → Preferences → Settings
2. Click the "Open Settings (JSON)" icon in the top right

#### Critical Settings

Add the following settings to your `settings.json` file:

```json
{
    // ===== CONTINUE.DEV CONFIGURATION =====

    // Enable tab-based autocomplete
    "continue.enableTabAutocomplete": true,

    // Disable Continue telemetry for privacy
    "continue.telemetryEnabled": false,

    // Enable console logs for debugging (optional)
    "continue.enableConsole": true,

    // ===== INLINE SUGGESTIONS (REQUIRED) =====

    // CRITICAL: Must be enabled for Continue to work
    "editor.inlineSuggest.enabled": true,

    // Show inline suggestion toolbar always
    "editor.inlineSuggest.showToolbar": "always",

    // Enable inline edits (for Edit mode)
    "editor.inlineSuggest.edits.enabled": true
}
```

#### Why These Settings Matter

**continue.enableTabAutocomplete**
- Controls whether autocomplete is enabled globally
- Can be toggled via status bar "Continue" button
- Must be `true` for autocomplete to work

**continue.telemetryEnabled**
- Controls anonymous usage data collection
- Set to `false` for privacy
- No code or sensitive data is sent when enabled

**continue.enableConsole**
- Shows detailed logs in VS Code Output panel
- Useful for debugging connection issues
- Access logs: View → Output → Select "Continue" from dropdown

**editor.inlineSuggest.enabled**
- **CRITICAL**: VS Code's master switch for inline suggestions
- Without this, Continue's network requests are blocked
- Must be `true` or Continue will not function

**editor.inlineSuggest.showToolbar**
- Controls visibility of inline suggestion toolbar
- Set to `"always"` for easier acceptance/rejection of suggestions

**editor.inlineSuggest.edits.enabled**
- Enables inline editing capabilities
- Required for Edit mode (`Ctrl+I`) to work properly

#### Settings Priority

Settings are applied in this order (later overrides earlier):

1. Continue hardcoded defaults (in extension source code)
2. `config.yaml` settings
3. **VS Code User Settings (highest priority)**

This means VS Code settings **override** config.yaml values. For example:
- If `config.yaml` has autocomplete enabled but VS Code settings has `"continue.enableTabAutocomplete": false`, autocomplete will be **disabled**
- Always check VS Code settings first when troubleshooting

#### Apply Settings

1. Save `settings.json`
2. Reload VS Code: `Ctrl+Shift+P` → "Developer: Reload Window"
3. Verify Continue is active: Status bar should show "Continue" button

---

## Configuration Variables Reference

### Global Settings

**name**
- Description: Display name for the configuration
- Type: String
- Purpose: Identifies configuration in Continue UI
- Example: `"GenAI Gateway Config"`

**version**
- Description: Configuration version
- Type: String
- Purpose: Track configuration changes
- Example: `"1.0.0"`

**schema**
- Description: Configuration schema version
- Type: String
- Purpose: Ensure compatibility with Continue extension
- Example: `"v1"`

### tabAutocompleteOptions

Global settings controlling autocomplete behavior across all files.

**multilineCompletions**
- Description: Enable multi-line code completions
- Type: String
- Values: `"always"`, `"never"`, `"auto"`
- Purpose: Control when autocomplete generates multiple lines
- Recommended: `"always"` for full function implementations

**debounceDelay**
- Description: Wait time in milliseconds after typing stops before triggering autocomplete
- Type: Integer (milliseconds)
- Purpose: Prevent excessive API calls on every keystroke
- Recommended: `3000` (3 seconds) for CPU-based inference
- Note: Lower values (500-1000ms) work better with GPU inference

**maxPromptTokens**
- Description: Maximum tokens sent as context to autocomplete model
- Type: Integer
- Purpose: Limit context size for faster inference
- Recommended: `100` for quick responses
- Note: Larger values provide more context but slower responses

**prefixPercentage**
- Description: Percentage of context taken from code before cursor (0.0 to 1.0)
- Type: Float
- Purpose: Balance prefix vs suffix context
- Recommended: `1.0` (100% prefix, no suffix) for faster processing

**suffixPercentage**
- Description: Percentage of context taken from code after cursor (0.0 to 1.0)
- Type: Float
- Purpose: Provide code after cursor as context
- Recommended: `0.0` for FIM-based models unless suffix is needed

**maxSuffixPercentage**
- Description: Maximum allowed suffix context (0.0 to 1.0)
- Type: Float
- Purpose: Cap suffix context even when enabled
- Recommended: `0.0` unless using Fill-in-Middle extensively

**modelTimeout**
- Description: Maximum wait time for model response in milliseconds
- Type: Integer (milliseconds)
- Purpose: Prevent indefinite waiting on slow inference
- Recommended: `10000` (10 seconds) for CPU inference, `5000` for GPU
- Critical: Must be longer than typical model inference time

**showWhateverWeHaveAtXMs**
- Description: Display partial completion after X milliseconds
- Type: Integer (milliseconds)
- Purpose: Show incomplete suggestions if model is slow
- Recommended: `2000` (2 seconds)

**useCache**
- Description: Cache autocomplete results for reuse
- Type: Boolean
- Purpose: Reuse previous completions for identical contexts
- Recommended: `true` for better performance

**onlyMyCode**
- Description: Limit context to user-written code (exclude dependencies)
- Type: Boolean
- Purpose: Reduce noise from third-party libraries
- Recommended: `true` for cleaner suggestions

**useRecentlyEdited**
- Description: Include recently edited files in context
- Type: Boolean
- Purpose: Provide relevant context from active development
- Recommended: `true` for better context awareness

**useRecentlyOpened**
- Description: Include recently opened files in context
- Type: Boolean
- Purpose: Include files you're currently working with
- Recommended: `true`

**useImports**
- Description: Include imported modules and libraries in context
- Type: Boolean
- Purpose: Understand dependencies and APIs
- Recommended: `true` for better API completions

**transform**
- Description: Apply post-processing transformations to completions
- Type: Boolean
- Purpose: Clean up and format model output
- Recommended: `true` for better formatting

**experimental_includeClipboard**
- Description: Include clipboard contents in context
- Type: Boolean
- Purpose: Use copied code as context
- Recommended: `false` (privacy concern, unstable feature)

**experimental_includeRecentlyVisitedRanges**
- Description: Include code ranges recently viewed
- Type: Boolean
- Purpose: Context from browsing history
- Recommended: `true` for enhanced context

**experimental_includeRecentlyEditedRanges**
- Description: Include specific code ranges recently edited
- Type: Boolean
- Purpose: Focus on active editing areas
- Recommended: `true`

**experimental_includeDiff**
- Description: Include git diff in context
- Type: Boolean
- Purpose: Understand recent changes
- Recommended: `true` for change-aware completions

**disableInFiles**
- Description: File patterns where autocomplete is disabled
- Type: Array of glob patterns
- Purpose: Prevent autocomplete in specific file types
- Example: `["*.md", "*.txt", "*.json"]`
- Recommended: Disable in markdown, config files

### models

Array of model configurations. Each model represents a connection to an AI model endpoint.

**name**
- Description: Display name for the model in Continue UI
- Type: String
- Purpose: Identify model in dropdowns and status messages
- Example: `"Llama 3.2 3B (Chat & Agent + Autocomplete)"`

**provider**
- Description: API provider type
- Type: String
- Values: `openai`, `anthropic`, `ollama`, `huggingface`, etc.
- Purpose: Determines API format and authentication method
- Recommended: `openai` for OpenAI-compatible endpoints (LiteLLM, vLLM, etc.)

**model**
- Description: Model identifier sent to API endpoint
- Type: String
- Purpose: Specify which model to use on the backend
- Example: `"meta-llama/Llama-3.2-3B-Instruct"`
- Note: Must match exact model name registered in GenAI Gateway (case-sensitive)

**apiBase**
- Description: Base URL for API endpoint
- Type: String (URL)
- Purpose: Backend service URL
- Example: `"https://api.example.com/v1"`
- Required: Must include `/v1` suffix for OpenAI-compatible APIs
- Note: Replace `api.example.com` with your actual GenAI Gateway URL

**apiKey**
- Description: Authentication key for API access
- Type: String
- Purpose: Authenticate requests to GenAI Gateway
- Example: `"your-api-key-here"`
- Security: Never commit real API keys to version control
- Note: Obtain from GenAI Gateway administrator

**ignoreSSL**
- Description: Skip SSL certificate verification
- Type: Boolean
- Purpose: Allow self-signed certificates
- Recommended: `true` for internal deployments with self-signed certs
- Security: Only use on trusted internal networks

**contextLength**
- Description: Maximum context window in tokens
- Type: Integer
- Purpose: Define model's maximum input capacity
- Example: `8192` for Llama 3.2 3B
- Note: Set according to model's actual capacity, not higher

### completionOptions

Settings applied to chat and edit mode responses.

**maxTokens**
- Description: Maximum tokens in model response
- Type: Integer
- Purpose: Limit response length
- Recommended: `2048` for chat/edit modes
- Note: Lower values (1024) if encountering context window errors

**temperature**
- Description: Randomness in generation (0.0 to 2.0)
- Type: Float
- Purpose: Control creativity vs consistency
- Recommended: `0.1` for code generation (deterministic)
- Range: `0.0` (deterministic) to `2.0` (very creative)

**stop**
- Description: Stop sequences to terminate generation
- Type: Array of strings
- Purpose: Prevent over-generation
- Example: `["\n\n", "def ", "class "]`
- Recommended: Language-specific keywords and double newlines

### requestOptions

Alternative settings for chat/edit modes (overrides completionOptions if present).

**maxTokens**
- Description: Same as completionOptions.maxTokens
- Purpose: Explicit control for request-level settings

**temperature**
- Description: Same as completionOptions.temperature
- Purpose: Request-level temperature override

### autocompleteOptions

Settings specifically for autocomplete mode (overrides completionOptions for autocomplete).

**maxTokens**
- Description: Maximum tokens in autocomplete suggestions
- Type: Integer
- Purpose: Keep completions short and fast
- Recommended: `256` for quick inline suggestions
- Note: Shorter = faster inference

**temperature**
- Description: Randomness in autocomplete (0.0 to 2.0)
- Type: Float
- Purpose: Control consistency of suggestions
- Recommended: `0.2` for consistent, predictable completions
- Note: Higher values create more varied but less reliable suggestions

**stop**
- Description: Stop sequences for autocomplete
- Type: Array of strings
- Purpose: Prevent excessive continuation
- Example: `["\n\n\n", "# "]`
- Recommended: Triple newlines, comment markers

### roles

Array of Continue modes this model handles.

**Available Roles:**
- `chat` - Chat mode interactions
- `edit` - Edit mode transformations
- `apply` - Apply code suggestions
- `autocomplete` - Inline autocomplete

**Purpose:** Assign specific models to specific tasks

**Example:** Single model handling all roles:
```yaml
roles:
  - chat
  - edit
  - apply
  - autocomplete
```

### promptTemplates

Custom prompt formats for different modes.

**autocomplete**
- Description: Template for autocomplete prompts
- Type: String with mustache variables
- Purpose: Format code context for model
- Variables:
  - `{{{prefix}}}` - Code before cursor
  - `{{{suffix}}}` - Code after cursor
  - `{{{filename}}}` - Current file name
  - `{{{language}}}` - Programming language
- Example: `"{{{prefix}}}"` for prefix-only completion
- See [FIM Template Formats](#fim-template-formats) for advanced examples

### useLegacyCompletionsEndpoint

**Description:** Use `/v1/completions` instead of `/v1/chat/completions` for autocomplete
**Type:** Boolean
**Purpose:** Required for FIM-based autocomplete with many models
**Recommended:** `true` for Llama, CodeLlama, StarCoder models
**Note:** Modern chat models may work without this, but legacy endpoint is more reliable

### experimental

Experimental features under development.

**inlineEditing**
- Description: Enable inline edit mode
- Type: Boolean
- Purpose: Edit code directly in editor (vs sidebar diff)
- Recommended: `true` for better UX

### allowAnonymousTelemetry

**Description:** Send anonymous usage data to Continue developers
**Type:** Boolean
**Purpose:** Help improve Continue extension
**Recommended:** `false` for privacy, `true` to support development
**Privacy:** No code or sensitive data is sent when enabled

---

## FIM Template Formats

Fill-in-Middle (FIM) allows models to complete code based on context before and after the cursor position. Different models use different FIM token formats.

### Basic Prefix-Only Format

Simplest format using only code before cursor.

```yaml
promptTemplates:
  autocomplete: "{{{prefix}}}"
```

**Use case:** When model doesn't support FIM or suffix context is not needed.

### Llama and CodeLlama Format

Standard format used by Meta's Llama and CodeLlama models.

```yaml
promptTemplates:
  autocomplete: "<|fim_prefix|>{{{prefix}}}<|fim_suffix|>{{{suffix}}}<|fim_middle|>"
```

**Tokens:**
- `<|fim_prefix|>` - Marks beginning of prefix context
- `<|fim_suffix|>` - Marks beginning of suffix context
- `<|fim_middle|>` - Marks where model should generate completion

**Use case:** Llama 3.x, CodeLlama 7B/13B/34B models

### StarCoder Format

Format used by BigCode's StarCoder models.

```yaml
promptTemplates:
  autocomplete: "<fim_prefix>{{{prefix}}}<fim_suffix>{{{suffix}}}<fim_middle>"
```

**Tokens:**
- `<fim_prefix>` - Prefix marker (no pipes)
- `<fim_suffix>` - Suffix marker (no pipes)
- `<fim_middle>` - Generation marker (no pipes)

**Use case:** StarCoder, StarCoder2, StarCoderBase models

### DeepSeek Coder Format

Format used by DeepSeek Coder models.

```yaml
promptTemplates:
  autocomplete: "<|fim▁begin|>{{{prefix}}}<|fim▁hole|>{{{suffix}}}<|fim▁end|>"
```

**Tokens:**
- `<|fim▁begin|>` - Marks beginning (note the ▁ character)
- `<|fim▁hole|>` - Marks gap to fill
- `<|fim▁end|>` - Marks end of context

**Use case:** DeepSeek Coder 1.3B/6.7B/33B models

### CodeGemma Format

Format used by Google's CodeGemma models.

```yaml
promptTemplates:
  autocomplete: "<|fim_prefix|>{{{prefix}}}<|fim_suffix|>{{{suffix}}}<|fim_middle|>"
```

**Note:** Same as Llama format

**Use case:** CodeGemma 2B/7B models

### Custom Format with File Context

Enhanced format including file metadata.

```yaml
promptTemplates:
  autocomplete: |
    File: {{{filename}}}
    Language: {{{language}}}

    <|fim_prefix|>{{{prefix}}}<|fim_suffix|>{{{suffix}}}<|fim_middle|>
```

**Additional variables:**
- `{{{filename}}}` - Current file name
- `{{{language}}}` - Programming language

**Use case:** When model benefits from explicit file context

### Determining FIM Format

Check model documentation or training details:

1. **Llama/CodeLlama family:** Use `<|fim_prefix|>` format with pipes
2. **StarCoder family:** Use `<fim_prefix>` format without pipes
3. **DeepSeek family:** Use `<|fim▁begin|>` format with special character
4. **Unknown models:** Start with prefix-only `"{{{prefix}}}"`, then test with Llama format

### Testing FIM Templates

Verify FIM template works correctly:

1. Configure template in config.yaml
2. Reload VS Code
3. Create test file with known completion
4. Type partial code and pause
5. Check if completion is relevant and correctly positioned

**Example test:**
```python
def fibonacci(n):
    # Pause here and check if completion continues logically
```

---

## Feature Usage

### Using Chat Mode

**Purpose:** Ask questions, get explanations, solve problems

**Steps:**
1. Press `Ctrl+L` to open chat
2. Type your question or request
3. Press Enter
4. Review response
5. Use action buttons:
   - **Apply**: Replace highlighted code with suggestion
   - **Insert**: Add suggestion at cursor position
   - **Copy**: Copy to clipboard

**Adding Context:**
- Highlight code before opening chat (auto-included)
- Use `@Files` to reference specific files
- Use `@Terminal` to include terminal output
- Use `@Codebase` to search entire project

**Examples:**
```
"Explain how this function works"
"Fix the bug in the highlighted code"
"Refactor this to use async/await"
"@Files package.json - What dependencies can I update?"
```

### Using Edit Mode

**Purpose:** Make targeted changes to selected code

**Steps:**
1. Highlight code to modify
2. Press `Ctrl+I`
3. Type instruction (e.g., "Add error handling")
4. Press Enter
5. Review diff preview
6. Accept or reject changes

**Examples:**
```
"Add JSDoc comments"
"Convert to TypeScript"
"Optimize for performance"
"Add input validation"
"Handle edge cases"
```

### Using Autocomplete

**Purpose:** Get real-time code suggestions while typing

**Setup:**
1. Click "Continue" in status bar
2. Enable "Tab Autocomplete"
3. Start typing code
4. Suggestions appear automatically

**Accepting Suggestions:**
- `Tab`: Accept full suggestion
- `Esc`: Reject suggestion
- `Ctrl+→` (or `Cmd+→`): Accept word-by-word
- `Ctrl+Alt+Space`: Force trigger suggestion

**Best Practices:**
- Write clear function names and comments
- Use type annotations (TypeScript/Python)
- Provide meaningful variable names
- Context helps improve suggestions

**Examples of When Autocomplete Shines:**
```python
def calculate_fibonacci(n: int) -> int:
    # Autocomplete suggests full implementation
```

```javascript
// After typing: const fetchUserData = async (userId) =>
// Autocomplete suggests: { try { const response = await... }
```

### Using Plan Mode

**Purpose:** Explore codebase safely before making changes

**Steps:**
1. Open Continue sidebar
2. Click mode selector dropdown
3. Choose "Plan"
4. Ask questions or request analysis
5. Review read-only findings
6. Switch to Agent mode to implement changes

**Safe Operations:**
- Read files, search code, view diffs
- No file modifications possible
- Cannot run terminal commands

**Examples:**
```
"Show me all API endpoints in this project"
"Find where user authentication is implemented"
"Analyze the database schema structure"
"List all TODO comments in the codebase"
```

### Using Agent Mode

**Purpose:** Complex, multi-step tasks requiring file operations

**Steps:**
1. Open Continue sidebar
2. Click mode selector dropdown
3. Choose "Agent"
4. Type task instruction
5. Review proposed tool calls
6. Grant permission for each operation
7. Verify final changes

**Tool Permission:**
- Agent asks before: Reading files, editing files, running commands
- Review each proposed action carefully
- Can reject individual tool calls

**Examples:**
```
"Implement a new authentication middleware in Express"
"Fix all ESLint errors in the src directory"
"Add unit tests for the UserService class"
"Refactor the database connection to use connection pooling"
```

---

## Best Practices

### For Chat Mode

1. Start new session for different topics (`Ctrl+L`)
2. Provide context by highlighting code or using `@Files`
3. Be specific: "Fix the null pointer error on line 45" vs "Fix bugs"
4. Ask follow-up questions to refine responses

### For Edit Mode

1. Highlight exact code section to modify
2. Give clear instructions: "Add type hints" vs "Improve code"
3. Review diffs before accepting
4. Use VS Code undo (`Ctrl+Z`) if needed

### For Autocomplete

1. Enable strategically (disable during presentations or pairing)
2. Review suggestions before accepting
3. Learn what triggers good suggestions
4. Provide context with clear function signatures and comments

### For Plan Mode

1. Explore codebase before implementing changes
2. Understand project structure first
3. Safe analysis with no risk of breaking code

### For Agent Mode

1. Review proposed tool calls before accepting
2. Break complex tasks into smaller operations
3. Commit code before running agent tasks
4. Monitor tool execution and verify outputs

### Performance Optimization

1. Keep `contextLength` within model capacity
2. Set reasonable `maxTokens` to reduce latency
3. Use lower temperature (0.1-0.3) for consistent output
4. Autocomplete caching is automatic, no action needed

### Security and Privacy

1. Never commit API keys to version control
2. Use environment variables or secure vaults for keys
3. All processing happens on your GenAI Gateway (no external services)
4. Use `ignoreSSL: true` only for trusted self-signed certificates

---

## Advanced Configuration

### Custom Rules

Rules allow you to define custom system prompts and behavior guidelines for Continue. Rules can be project-specific or global, helping tailor AI responses to your coding standards and requirements.

#### What Are Rules?

Rules are markdown files containing instructions that are automatically included in the context when interacting with Continue. They guide the model's behavior, enforce coding standards, or provide project-specific context.

**Use Cases:**
- Enforce coding style guidelines
- Define project-specific conventions
- Add company policies or security requirements
- Provide context about project architecture
- Set response format preferences

#### Creating Global Rules

Global rules apply to all projects.

**Location:**
```
Windows: C:\Users\<username>\.continue\rules\
macOS/Linux: ~/.continue/rules/
```

**Steps:**

1. Create the rules directory:
```bash
# Windows
mkdir C:\Users\<username>\.continue\rules

# macOS/Linux
mkdir -p ~/.continue/rules
```

2. Create a rule file (e.g., `coding-style.md`):
```markdown
# Coding Style Guidelines

Follow these conventions when generating code:

## Python
- Use type hints for all function parameters and return values
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use docstrings for all functions and classes

## JavaScript/TypeScript
- Use const/let instead of var
- Prefer arrow functions for callbacks
- Use async/await instead of promises
- Add JSDoc comments for all functions

## General
- Write clear, descriptive variable names
- Add comments for complex logic
- Include error handling
- Write modular, reusable code
```

3. Rules are automatically loaded when Continue starts

#### Creating Project-Specific Rules

Project rules apply only to a specific project.

**Location:**
```
<project-root>/.continue/rules/
```

**Steps:**

1. Navigate to your project root
2. Create the rules directory:
```bash
mkdir -p .continue/rules
```

3. Create a project rule file (e.g., `architecture.md`):
```markdown
# Project Architecture

This project follows a microservices architecture.

## Structure
- `/api` - REST API endpoints
- `/services` - Business logic layer
- `/models` - Database models
- `/utils` - Utility functions

## Database
- PostgreSQL with SQLAlchemy ORM
- Migrations in `/migrations`

## Authentication
- JWT tokens for API authentication
- Keycloak for user management

## Code Generation Guidelines
- All new endpoints must include authentication
- Add unit tests for all new services
- Use async/await for database operations
```

#### Rule Examples

**Security Rule** (`.continue/rules/security.md`):
```markdown
# Security Guidelines

When generating code:
- Never log sensitive information (passwords, API keys, tokens)
- Validate all user inputs
- Use parameterized queries to prevent SQL injection
- Sanitize data before rendering in HTML
- Always use HTTPS for external API calls
```

**Documentation Rule** (`.continue/rules/documentation.md`):
```markdown
# Documentation Standards

All functions must include:
- Brief description of purpose
- Parameter descriptions with types
- Return value description
- Example usage
- Exceptions that may be raised

Format:
```python
def function_name(param1: type1, param2: type2) -> return_type:
    """
    Brief description.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ExceptionType: When this exception occurs

    Example:
        >>> function_name(value1, value2)
        expected_output
    """
```
```

**Testing Rule** (`.continue/rules/testing.md`):
```markdown
# Testing Requirements

When creating new features:
- Write unit tests for all functions
- Aim for 80% code coverage
- Include edge cases and error scenarios
- Mock external dependencies

Test file structure:
- Test files in `/tests` directory
- Mirror source directory structure
- Name test files: `test_<module_name>.py`
```

#### Using Rules

Rules are automatically included in context. You can reference them explicitly:

1. In Chat mode, rules influence all responses
2. In Edit mode, rules guide code transformations
3. In Agent mode, rules affect code generation decisions

**Note:** Rules add to context token count. Keep rules concise to avoid exceeding context limits with smaller models.

---

### MCP Servers (Model Context Protocol)

MCP servers extend Continue's functionality by adding custom tools, context providers, and external integrations. They enable Continue to interact with databases, APIs, file systems, and other services.

#### What Is MCP?

Model Context Protocol is a standard for connecting AI assistants to external tools and data sources. MCP servers provide:
- Custom context providers (fetch data from external sources)
- Custom tools (perform actions like API calls, database queries)
- Integration with external services

#### Use Cases

- Query databases directly from Continue
- Fetch documentation from internal wikis
- Integrate with project management tools
- Access company knowledge bases
- Call internal APIs for data retrieval
- Run custom scripts and automation

#### MCP Server Installation

MCP servers are configured in `config.yaml` under the `mcpServers` section.

**Basic Structure:**
```yaml
mcpServers:
  server-name:
    command: node
    args:
      - /path/to/server/index.js
    env:
      API_KEY: your-api-key
```

#### Example: Filesystem MCP Server

Access local file system through Continue.

**Install MCP Server:**
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

**Add to config.yaml:**
```yaml
mcpServers:
  filesystem:
    command: node
    args:
      - /usr/local/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js
      - /path/to/allowed/directory
    env: {}
```

**Usage in Continue:**
- Access files outside workspace
- Read configuration files from system directories
- Query logs from application directories

#### Example: PostgreSQL MCP Server

Query databases directly from Continue.

**Install MCP Server:**
```bash
npm install -g @modelcontextprotocol/server-postgres
```

**Add to config.yaml:**
```yaml
mcpServers:
  postgres:
    command: node
    args:
      - /usr/local/lib/node_modules/@modelcontextprotocol/server-postgres/dist/index.js
    env:
      POSTGRES_CONNECTION_STRING: postgresql://user:password@localhost:5432/database
```

**Usage in Continue:**
```
"@postgres - Show me the schema for the users table"
"@postgres - Query all orders from last month"
"@postgres - Find customers with more than 10 orders"
```

#### Example: GitHub MCP Server

Integrate with GitHub repositories.

**Install MCP Server:**
```bash
npm install -g @modelcontextprotocol/server-github
```

**Add to config.yaml:**
```yaml
mcpServers:
  github:
    command: node
    args:
      - /usr/local/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js
    env:
      GITHUB_TOKEN: your-github-token
```

**Usage in Continue:**
```
"@github - Show open pull requests"
"@github - List recent issues"
"@github - Get commit history for main branch"
```

#### Creating Custom MCP Server

Build custom MCP servers for internal tools and services.

**1. Create Server Project:**
```bash
mkdir my-mcp-server
cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk
```

**2. Create Server Code (`index.js`):**
```javascript
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

// Create server instance
const server = new Server(
  {
    name: 'my-custom-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define custom tool
server.setRequestHandler('tools/list', async () => {
  return {
    tools: [
      {
        name: 'query_internal_api',
        description: 'Query internal company API',
        inputSchema: {
          type: 'object',
          properties: {
            endpoint: {
              type: 'string',
              description: 'API endpoint to query',
            },
            params: {
              type: 'object',
              description: 'Query parameters',
            },
          },
          required: ['endpoint'],
        },
      },
    ],
  };
});

// Implement tool execution
server.setRequestHandler('tools/call', async (request) => {
  if (request.params.name === 'query_internal_api') {
    const { endpoint, params } = request.params.arguments;

    // Call your internal API
    const response = await fetch(`https://internal-api.company.com/${endpoint}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${process.env.API_KEY}` },
    });

    const data = await response.json();

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

**3. Add to config.yaml:**
```yaml
mcpServers:
  my-custom-server:
    command: node
    args:
      - /path/to/my-mcp-server/index.js
    env:
      API_KEY: your-internal-api-key
```

**4. Use in Continue:**
```
"@my-custom-server - Query the users endpoint"
"@my-custom-server - Get latest metrics from analytics"
```

#### MCP Server Best Practices

**Security:**
- Store sensitive credentials in environment variables
- Never commit API keys to version control
- Use read-only access where possible
- Validate all inputs before processing

**Performance:**
- Cache frequently accessed data
- Implement request timeouts
- Limit result set sizes
- Use pagination for large datasets

**Error Handling:**
- Return clear error messages
- Log errors for debugging
- Handle network failures gracefully
- Provide fallback responses

**Documentation:**
- Document all available tools
- Provide clear input schemas
- Include usage examples
- Document environment variables required

#### Troubleshooting MCP Servers

**Server Not Loading:**
1. Check `command` path is correct
2. Verify Node.js is installed: `node --version`
3. Check server is executable
4. Review VS Code Output → Continue for errors

**Tool Not Appearing:**
1. Reload VS Code after config changes
2. Check server implements `tools/list` handler
3. Verify tool schema is valid
4. Check Continue output logs

**Tool Execution Fails:**
1. Verify environment variables are set correctly
2. Check network connectivity to external services
3. Validate API credentials
4. Review error messages in Continue output

---

## Troubleshooting

For comprehensive troubleshooting guidance, common issues, and solutions, refer to [TROUBLESHOOTING.md](./TROUBLESHOOTING.md).

---

## Additional Resources

- Continue Documentation: https://docs.continue.dev/
- Continue GitHub: https://github.com/continuedev/continue
- Continue Discord: https://discord.gg/NWtdYexhMs
- LiteLLM Documentation: https://docs.litellm.ai/
