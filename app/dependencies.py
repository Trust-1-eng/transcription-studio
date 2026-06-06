import threading

# In-memory store: file_id -> { path, created, name }
temp_files: dict = {}
temp_lock = threading.Lock()

# Transcript cache: {tid: (data, timestamp)}
transcript_cache: dict = {}

# Gemini cache: {tid: (result_dict, timestamp)}
gemini_cache: dict = {}

# Original filename cache: {tid: "filename.mp4"}
filename_cache: dict = {}

# User edits cache: {tid: {"utterances": [...], "text": "..."}}
edit_cache: dict = {}

# Alignment cache: {tid: {"edited_text": str, "aligned_words": list, "cues": list}}
alignment_cache: dict = {}
