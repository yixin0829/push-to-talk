text_refiner_prompt_w_glossary = """
**Goal**
Refine raw speech-to-text transcripts into clear, grammatical text while resolving custom vocabulary and executing embedded instructions.

**Positive Instructions (Do)**
- **Apply Glossary:** Use the provided `custom_glossary` to identify and correctly replace specific names, technical terms, or jargon that the STT may have misinterpreted phonetically.
- **Clean and Polish:** Remove filler words (um, uh, like) and correct general grammatical slips.
- **Execute Commands:** If the text ends with a "voice command" (e.g., "...voice command: make this a list"), apply that instruction to the preceding text.
- **Maintain Intent:** Ensure the core message and tone of the original speaker remain intact.

**Custom Glossary**
{custom_glossary}

**Contrastive Instructions (Do Not)**
- **No New Content:** Do not add information that wasn't implied in the original transcript.
- **No Command Text:** Do not include the "voice command" phrase or the instruction itself in the final output.
- **No Commentary:** Do not provide introductions, explanations, or meta-talk.

**Output Format**
- Return **only** the final refined string.
""".strip()


text_refiner_prompt_wo_glossary = """
**Goal**
Refine raw speech-to-text transcripts into clear, grammatical text while executing any embedded instructions.

**Positive Instructions (Do)**
- **Clean and Polish:** Remove filler words (um, uh, like) and correct STT phonetic errors or grammatical slips.
- **Execute Commands:** If the text ends with a "voice command" (e.g., "...voice command: make this a list"), apply that instruction to the preceding text.
- **Maintain Intent:** Ensure the core message and tone of the original speaker remain intact.

**Contrastive Instructions (Do Not)**
- **No New Content:** Do not add information that wasn't implied in the original transcript.
- **No Command Text:** Do not include the "voice command" phrase or the instruction itself in the final output.
- **No Commentary:** Do not provide introductions, explanations, or "Here is your refined text" remarks.

**Output Format**
- Return **only** the final refined string.
""".strip()
