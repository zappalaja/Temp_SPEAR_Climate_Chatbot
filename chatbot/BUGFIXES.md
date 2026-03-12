# Bug Fixes Applied

## Bug #1: User Messages Showing RAG Context/JSON

**Problem:** When asking a new question, the previous user message would display with all the RAG context markup instead of the clean user input.

**Root Cause:** The augmented prompt (with RAG context) was being stored in session state, and the chat history display loop would render it on the next rerun.

**Fix Applied (chatbot_app.py:348-352):**
```python
# Store BOTH clean and augmented - display clean, send augmented to model
st.session_state.messages.append({
    "role": "user",
    "content": prompt,  # Store clean prompt for display
    "content_for_model": augmented_prompt  # Store augmented for model
})
```

**Additional Change (chatbot_app.py:227-241):**
Updated `build_ollama_messages()` to use `content_for_model` when constructing messages for the LLM:
```python
def build_ollama_messages(messages: list[dict]) -> list[dict]:
    cleaned = []
    for m in messages:
        if m.get("role") == "system":
            continue
        # Use content_for_model if available (RAG-augmented), otherwise use content
        msg_copy = m.copy()
        if "content_for_model" in msg_copy:
            msg_copy["content"] = msg_copy.pop("content_for_model")
        cleaned.append(msg_copy)
    return [{"role": "system", "content": SYSTEM_PROMPT}, *cleaned]
```

**Result:**
- UI shows clean user input: "hello"
- Model receives augmented input with RAG context
- No more JSON/markup showing in chat bubbles

---

## Bug #2: Double Assistant Chat Bubbles

**Problem:** Assistant responses were appearing twice in the chat history - once during tool execution and once with the final response.

**Root Cause:** An assistant message was being appended to session state inside the tool execution loop (line 403-407), and then another assistant message was appended at the end with the final response (line 535/541).

**Fix Applied (chatbot_app.py:415-416):**
Removed the `st.session_state.messages.append()` call from inside the tool loop:

```python
# REMOVED:
# st.session_state.messages.append({
#     "role": "assistant",
#     "content": current_msg.get("content", ""),
#     "tool_calls": tool_calls,
# })

# Added comment instead:
# Note: We don't append assistant message here to avoid double bubbles
# The final response with all tool results will be appended at the end
```

**Result:**
- Only one assistant message is stored in session state
- Tool execution logs are still tracked and displayed properly
- No more duplicate chat bubbles

---

## Testing

To verify fixes:
1. **Test Bug #1:**
   - Ask a question (e.g., "hello")
   - Ask another question
   - Previous user message should show "hello", NOT "Use the retrieved context..."

2. **Test Bug #2:**
   - Ask a question that triggers tool use (e.g., "what variables are available?")
   - Should see only ONE assistant response bubble with tool execution logs
   - Should NOT see two separate assistant bubbles

---

## Files Modified

- `chatbot_app.py` (lines 227-241, 348-352, 415-416)
