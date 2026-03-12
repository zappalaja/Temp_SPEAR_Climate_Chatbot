# Critical Streaming Bug Fix - Tool Calls Being Lost

## Problem
When users asked questions that should trigger tool usage (like "search for precipitation" or "what spear data is available"), the chatbot returned completely empty responses.

## Root Cause
The `_ollama_native_stream()` function was **overwriting** the `final_message` object on each streaming chunk, causing `tool_calls` from earlier chunks to be lost.

### The Bug (Line 263-265 in chatbot_app.py)
```python
message = data.get("message", {})
if message:
    final_message = message  # ❌ This OVERWRITES and loses tool_calls!
```

When Ollama streams responses with tool calls:
1. **Chunk 1**: Contains `tool_calls` array
2. **Chunk 2**: Contains empty message or done signal
3. **Result**: `final_message = message` on chunk 2 overwrites chunk 1, **tool_calls are lost**

## The Fix (Applied on 2026-01-15)

### Fix 1: Preserve tool_calls Across Chunks
Instead of overwriting, **merge** each chunk into `final_message`:

```python
message = data.get("message", {})
if message:
    # Preserve tool_calls across chunks (important for qwen2.5:7b)
    if message.get("tool_calls"):
        final_message["tool_calls"] = message["tool_calls"]
    if message.get("content") is not None:
        final_message["content"] = message["content"]
    if message.get("role"):
        final_message["role"] = message["role"]
```

**Location**: `chatbot_app.py:264-271`

### Fix 2: Handle Empty Content with Tool Calls
When the model returns tool calls with empty content (common with qwen2.5), display a status message:

```python
# Handle case where model returns empty content with tool calls (e.g., qwen2.5:7b)
if tool_calls and not full_resp.strip():
    full_resp = "_Accessing SPEAR climate data..._\n\n"
    msg_placeholder.markdown(full_resp)
```

**Location**: `chatbot_app.py:420-423`

### Fix 3: Debug Logging
Added debug prints to diagnose tool call issues:

```python
# Debug: Log what we got from the model
print(f"DEBUG: full_resp length: {len(full_resp)}, tool_calls count: {len(tool_calls)}")
if tool_calls:
    print(f"DEBUG: Tool calls: {[tc.get('function', {}).get('name') for tc in tool_calls]}")
else:
    print("DEBUG: No tool calls received from model")
```

**Location**: `chatbot_app.py:413-418`

## Why This Happened
This same bug existed in the llama70b version and was already fixed there (see `spear-climate-chatbot_llama70b/chatbot_app.py:265-271`), but the fix was never ported to the qwen version.

## Testing Verification

### Before Fix
```
User: "search for precipitation"
Assistant: ""  (empty response, tool_calls lost)
```

### After Fix
```
User: "search for precipitation"
Assistant: "_Accessing SPEAR climate data..._"
[Tool executes: search_spear_variables]
[Model provides analysis of results]
```

## Files Modified
1. `chatbot_app.py` (lines 264-271, 413-423)

## Related Bugs Fixed Previously
- **Double chat bubbles**: Fixed by removing duplicate message append
- **RAG JSON showing in UI**: Fixed by storing clean vs augmented prompts separately
- **Welcome message disappearing**: Fixed by always displaying at top
- **RAG interfering with tools**: Fixed by clarifying RAG is background context only
- **Model narrating instead of calling tools**: Fixed by updating system prompt

This was the **final critical bug** preventing tool execution from working properly with qwen2.5:7b.
