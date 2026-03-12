# RAG and Tool Calling Fixes

## Issues Found in Chat History (2026-01-15)

### Issue 1: Model Says It Will Use Tools But Doesn't
**Example from logs (line 28-31):**
```
User: "what spear data is available?"
Assistant: "To provide a comprehensive answer about the available SPEAR data,
let's first explore the variables and scenarios that are typically included.
We can use the `search_spear_variables` function to get this information.

Let's call the `search_spear_variables` function..."
```
**Problem:** The model mentions calling the function but never actually calls it. No tool execution occurs.

### Issue 2: Empty Responses After Tool-Related Questions
**Example from logs (line 46-48):**
```
User: "I want to know what files are available for the future scenario precipitation"
Assistant: ""  [completely empty]
```
**Problem:** When asked about specific data, the model returns an empty response.

### Issue 3: Welcome Message Disappears
**Problem:** After the first message is sent, the welcome message disappears and never shows again.

---

## Root Cause Analysis

### Why RAG Was Interfering with Tool Calls:

1. **Confusing Instructions:** The RAG prompt said "Use the retrieved context below if it is relevant. If it is not relevant, ignore it." This made the model think:
   - "I have context about SPEAR, so I don't need to use tools"
   - The model didn't understand that RAG = background info, Tools = actual data access

2. **Too Much Context:** Default was 5 RAG chunks per query, which could be thousands of tokens of text, potentially:
   - Pushing tool definitions out of context window
   - Overwhelming the model's decision-making
   - Making the model think it already has all the information

3. **No Clear Separation:** The RAG context looked like it was providing complete answers, so the model didn't realize it still needed to query actual data files.

---

## Fixes Applied

### Fix 1: Improved RAG Prompt Clarity (chatbot_app.py:224-231)

**Before:**
```python
return (
    "Use the retrieved context below if it is relevant. "
    "If it is not relevant, ignore it.\n\n"
    "--- RAG CONTEXT START ---\n"
    f"{rag_context}\n"
    "--- RAG CONTEXT END ---\n\n"
    f"User question: {user_text}"
)
```

**After:**
```python
return (
    "**IMPORTANT: The context below provides background information about SPEAR, "
    "but you MUST still use your MCP tools to access actual data files, variables, and real-time data. "
    "Use this context to understand concepts, but use tools to access data.**\n\n"
    "--- BACKGROUND CONTEXT START ---\n"
    f"{rag_context}\n"
    "--- BACKGROUND CONTEXT END ---\n\n"
    f"User question: {user_text}"
)
```

**Impact:** Makes it crystal clear that:
- RAG = background info only
- Tools = required for actual data access
- The model must use BOTH

### Fix 2: Reduced RAG Context Size (chatbot_app.py:219)

**Before:** `rag_k = int(os.getenv("RAG_TOP_K", "5"))`
**After:** `rag_k = int(os.getenv("RAG_TOP_K", "2"))`

**Impact:**
- 60% reduction in RAG context size
- Less chance of overwhelming the model
- More tokens available for tool definitions and responses

### Fix 3: Added RAG Enable/Disable Control (chatbot_app.py:214-216)

**New code:**
```python
# Check if RAG is enabled (default: true)
rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
if not rag_enabled:
    return user_text
```

**Impact:** Can completely disable RAG for testing by setting `RAG_ENABLED=false` in `.env`

### Fix 4: Welcome Message Now Persists (chatbot_app.py:327-333)

**Before:**
```python
# Display welcome message if chat is empty
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        st.markdown(WELCOME_MESSAGE)
```

**After:**
```python
# Always display welcome message at the top (even with chat history)
with st.chat_message("assistant"):
    st.markdown(WELCOME_MESSAGE)

# Add separator if there's chat history
if len(st.session_state.messages) > 0:
    st.markdown("---")
```

**Impact:** Welcome message now always visible at the top, providing context about chatbot capabilities

### Fix 5: Updated .env with RAG Controls

**New environment variables:**
```bash
# RAG (Retrieval Augmented Generation) Settings
RAG_ENABLED=true        # Set to 'false' to disable RAG entirely
RAG_TOP_K=2             # Reduced from 5 to 2 chunks
RAG_API_URL=http://localhost:8002
```

---

## Testing Recommendations

### Test 1: Verify Tool Calls Work
```
User: "what variables are available in SPEAR?"
Expected: Model should call browse_spear_directory or search_spear_variables
```

### Test 2: Verify RAG Doesn't Block Tools
```
User: "show me precipitation data for 2050"
Expected: Model should use tools to access actual data, not just describe from RAG
```

### Test 3: Test with RAG Disabled
```bash
# In .env, set:
RAG_ENABLED=false

# Restart chatbot, then ask:
User: "what is SPEAR?"
Expected: Model uses tools to browse and explain, not RAG context
```

### Test 4: Welcome Message Persists
```
1. Send first message
2. Send second message
Expected: Welcome message still visible at top
```

---

## If Issues Persist

If the model still doesn't use tools properly:

1. **Check MCP server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Temporarily disable RAG completely:**
   ```bash
   # In .env:
   RAG_ENABLED=false
   ```

3. **Check Ollama model supports tools:**
   ```bash
   curl -X POST http://localhost:11434/api/chat \
     -d '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"test"}],"tools":[{"type":"function","function":{"name":"test","description":"test","parameters":{"type":"object","properties":{}}}}],"stream":false}'
   ```
   Should return tool_calls in response

4. **Increase logging:** Check `chat_logs/chat_history_latest.json` after each interaction to see if tool_calls are present in messages

---

## Files Modified

- `chatbot_app.py` (lines 208-232, 327-333)
- `.env` (added RAG control variables)
