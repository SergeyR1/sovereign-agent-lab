"""
Exercise 1 — Answers
====================
Fill this in after running exercise1_context.py.
Run `python grade.py ex1` to check for obvious issues before submitting.
"""

# ── Part A ─────────────────────────────────────────────────────────────────

# The exact answer the model gave for each condition.

PART_A_PLAIN_ANSWER    = "The Haymarket Vaults"
PART_A_XML_ANSWER      = "The Albanach"
PART_A_SANDWICH_ANSWER = "The Albanach"

# Was each answer correct? True or False.

PART_A_PLAIN_CORRECT    = True
PART_A_XML_CORRECT      = True
PART_A_SANDWICH_CORRECT = True

# Explain what you observed. Minimum 30 words.

PART_A_EXPLANATION = """
All three conditions returned correct answers on the main model (YandexGPT).
The PLAIN condition returned The Haymarket Vaults, while XML and SANDWICH
both returned The Albanach. Both are valid answers since both venues satisfy
all three constraints (capacity >= 160, vegan = yes, status = available).
The model had no difficulty with the baseline dataset regardless of formatting.
"""

# ── Part B ─────────────────────────────────────────────────────────────────

PART_B_PLAIN_ANSWER    = "The Haymarket Vaults"
PART_B_XML_ANSWER      = "The Albanach"
PART_B_SANDWICH_ANSWER = "The Albanach"

PART_B_PLAIN_CORRECT    = True
PART_B_XML_CORRECT      = True
PART_B_SANDWICH_CORRECT = True

# Did adding near-miss distractors change any results? True or False.
PART_B_CHANGED_RESULTS = False

# Which distractor was more likely to cause a wrong answer, and why?
PART_B_HARDEST_DISTRACTOR = """
The Holyrood Arms is the most dangerous distractor because it satisfies two of the three
constraints (capacity 160, vegan yes) and only fails on status being full. A model that
skims constraints rather than checking all three would likely pick this venue. It is placed
immediately before the correct answer, which exploits the attention blur between adjacent items.
"""

# ── Part C ─────────────────────────────────────────────────────────────────

PART_C_WAS_RUN = True

PART_C_PLAIN_ANSWER    = "The Ensign Ewart The Haymarket Vaults The New Town Vault The Albanach"
PART_C_XML_ANSWER      = "The Haymarket Vaults"
PART_C_SANDWICH_ANSWER = "The Haymarket Vaults"

# Explain what Part C showed, or why it wasn't needed. Minimum 30 words.
PART_C_EXPLANATION = """
Part C ran the small model (yandexgpt-lite) on the distractor dataset.
The PLAIN condition showed a clear structural failure: the model returned
four venue names instead of one, including The Ensign Ewart (capacity 120,
fails the 160 requirement) and The New Town Vault (no vegan, fails dietary
constraint). XML and SANDWICH both correctly returned The Haymarket Vaults.
This demonstrates the U-shaped recall effect from Liu et al. (2023) — when
given unstructured plain text, the smaller model cannot reliably filter all
constraints simultaneously, while structured formatting (XML tags) helps
the model process each venue individually.
"""

# ── Core lesson ────────────────────────────────────────────────────────────

CORE_LESSON = """
Context formatting matters most when the signal-to-noise ratio is low, the
context is long, or the model is less capable. With strong frontier models
and clean datasets, plain text often works fine. But when you add near-miss
distractors that are semantically close to the correct answer, or use a
smaller model, structural formatting like XML wrapping and query sandwiching
become essential. For agent engineering, this means tool outputs should
always be wrapped in structured XML tags, especially when combining multiple
data sources in a single context window. The Lost-in-the-Middle effect is
real and amplified by model size and data complexity.
"""
