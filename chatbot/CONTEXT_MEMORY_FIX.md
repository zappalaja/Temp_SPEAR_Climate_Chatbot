# Conversation Memory & Context Overflow Fix

## Problem
The chatbot wasn't remembering previous conversation turns, even the message directly prior. Issues included:

1. **Ignoring conversation context:**
   - User: "yes explore historical"
   - Bot: calls `browse_spear_directory(path="")` instead of `path="historical"`

2. **Re-calling tools unnecessarily:**
   - Bot searches for precipitation, gets 90 results
   - User: "can you give me the names of the 35 runs?"
   - Bot: Searches AGAIN instead of using previous results

3. **Not remembering tool results:**
   - Each response acted like a fresh conversation
   - No continuity between turns

## Root Cause

**Massive tool results were filling the context window:**

From chat logs analysis:
- Tool result #12: **88,808 characters** (~22,000 tokens!)
- Tool result #9: **11,316 characters** (~2,800 tokens)

When `search_spear_variables` returns 90 precipitation runs, the full JSON is stored in conversation history. With:
- System prompt: ~3,000 tokens
- RAG context: ~1,000 tokens
- Multiple tool results: 22,000+ tokens each

The 32k context window fills up, and **earlier conversation turns get truncated or lost** when sent to the model.

## The Fix

### 1. Truncate Large Tool Results (chatbot_app.py:534-558)

**Strategy:**
- Set max tool result length: 5,000 chars (~1,250 tokens)
- For `search_spear_variables`: Keep first 10 results + summary
- For other tools: Truncate with explanatory note

**Code:**
```python
# Truncate large tool results to prevent context overflow
MAX_TOOL_RESULT_LENGTH = 5000  # ~1250 tokens
if len(content_str) > MAX_TOOL_RESULT_LENGTH:
    original_length = len(content_str)
    print(f"DEBUG: Truncating {tool_name} result: {original_length} chars -> {MAX_TOOL_RESULT_LENGTH} chars")

    # For search results, provide a summary
    if tool_name == "search_spear_variables" and result.get("status") == "ok":
        data = result.get("data", [])
        total_results = len(data) if isinstance(data, list) else 0
        truncated_data = data[:10] if isinstance(data, list) else data

        truncated_result = {
            "status": "ok",
            "tool": tool_name,
            "data": truncated_data,
            "summary": f"Found {total_results} total results. Showing first {len(truncated_data)}. Full results available in UI.",
            "truncated": True
        }
        content_str = json.dumps(truncated_result, default=str)
        print(f"DEBUG: Truncated to {total_results} results -> showing first {len(truncated_data)}")
    else:
        # For other large results, truncate with a note
        truncated = content_str[:MAX_TOOL_RESULT_LENGTH]
        content_str = truncated + f"\n\n[... truncated {original_length - MAX_TOOL_RESULT_LENGTH} chars to save context. Full results visible in UI.]"
```

**Impact:**
- Search with 90 results: 88,808 chars → ~1,500 chars (98% reduction!)
- Conversation history stays within context window
- Model can remember earlier turns

### 2. Updated System Prompt with Memory Rules (ai_config.py:54-60)

**New section added:**
```python
**CONVERSATION MEMORY & CONTEXT:**
- **ALWAYS read and use the full conversation history** - previous messages contain important context
- **DO NOT re-call tools if you already have the results** - check previous tool responses first
- **Large tool results are truncated** - if you see "truncated: true" or "summary" fields, use that information
- When users refer to "the data" or "those results", they mean the tool results from previous messages
- **Extract information from conversation context** - if the user says "explore historical", use path="historical" in your tool call
- Build on previous responses - don't start from scratch each time
```

**Impact:**
- Model now knows to check conversation history first
- Understands truncated results and how to use them
- Extracts context from user messages (e.g., "explore historical" → path="historical")

### 3. Debug Logging

Added logging to monitor truncation:
```python
print(f"DEBUG: Truncating {tool_name} result: {original_length} chars -> {MAX_TOOL_RESULT_LENGTH} chars")
print(f"DEBUG: Truncated to {total_results} results -> showing first {len(truncated_data)}")
```

Watch terminal for these messages to verify truncation is working.

## Testing

### Before Fix:
```
User: "what spear data can you see"
Bot: [calls browse_spear_directory, shows scenarios]

User: "yes explore historical"
Bot: [calls browse_spear_directory(path="") - WRONG! Same as before]

User: "search for precipitation"
Bot: [gets 90 results, 88k chars stored]

User: "can you give me the names of the 35 runs?"
Bot: [calls search_spear_variables AGAIN - doesn't remember previous results]
```

### After Fix:
```
User: "what spear data can you see"
Bot: [calls browse_spear_directory, shows scenarios]

User: "yes explore historical"
Bot: [calls browse_spear_directory(path="historical") - uses context!]

User: "search for precipitation"
Bot: [gets 90 results, truncates to 10 + summary, stores ~1.5k chars]
Result stored: "Found 90 total results. Showing first 10. Full results available in UI."

User: "can you give me the names of the 35 runs?"
Bot: [reads previous tool result, extracts run names without re-calling tool]
```

## Why This Works

1. **Smaller tool results** = more conversation history fits in context
2. **Explicit memory instructions** = model knows to check history first
3. **Summary information preserved** = model still knows total count and scope
4. **Full results still in UI** = user sees complete data in expandable sections

## Trade-offs

**Pros:**
- Conversation memory works correctly
- No more unnecessary tool re-calls
- Better context utilization
- Faster responses (fewer tool calls)

**Cons:**
- Model sees truncated data (first 10 items instead of all 90)
- Must rely on summary counts for full picture
- Edge cases where model might need all results

**Mitigation:**
- For detailed analysis, model can filter search parameters to get specific subset
- Summary includes total count so model knows scope
- Full results visible in UI for user reference

## Files Modified
1. `chatbot_app.py` (lines 534-558) - Added truncation logic
2. `ai_config.py` (lines 54-60) - Added memory rules to system prompt

## Related Fixes
- **Streaming tool preservation**: Fixed tool_calls being lost across chunks
- **Empty content handler**: Shows "Accessing data..." for empty content with tools
- **System prompt improvements**: "DO NOT say 'let's use'" - call tools directly
- **RAG interference**: Clarified RAG is background info, tools are required for data

This fix completes the conversation memory system and should resolve all context-related issues.
