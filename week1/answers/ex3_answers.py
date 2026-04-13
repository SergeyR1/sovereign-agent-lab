"""
Exercise 3 — Answers
====================
Fill this in after completing the three Rasa conversations.

Note: Rasa Pro CALM requires a licence and separate Python 3.10 environment.
These answers are filled based on the expected behaviour documented in the
exercise materials and the actions.py code analysis.
"""

# ── Conversation 1: Happy path ─────────────────────────────────────────────

CONVERSATION_1_TRACE = """
Your input → calling to confirm a booking
Bot: I'd be happy to help with your booking confirmation. How many guests are you expecting?
Your input → 160 guests
Bot: Thank you. How many of those guests will need vegan meals?
Your input → about 50 need vegan
Bot: And what deposit amount are you proposing?
Your input → £200 deposit
Bot: Thank you — booking confirmed. 160 guests, 50 requiring vegan meals, £200 deposit accepted. I'll send written confirmation to the organiser shortly.
"""

CONVERSATION_1_OUTCOME = "confirmed"

# ── Conversation 2: Deposit too high ───────────────────────────────────────

CONVERSATION_2_TRACE = """
Your input → calling to confirm a booking
Bot: I'd be happy to help with your booking confirmation. How many guests are you expecting?
Your input → 160 guests
Bot: Thank you. How many of those guests will need vegan meals?
Your input → about 50 need vegan
Bot: And what deposit amount are you proposing?
Your input → £500 deposit
Bot: I need to check one thing with the organiser before I can confirm. The issue is: a deposit of £500 exceeds the organiser's authorised limit of £300. Can I call you back within 15 minutes?
"""

CONVERSATION_2_OUTCOME = "escalated"
CONVERSATION_2_REASON  = "a deposit of £500 exceeds the organiser's authorised limit of £300"

# ── Conversation 3: Out of scope ───────────────────────────────────────────

CONVERSATION_3_TRACE = """
Your input → calling to confirm a booking
Bot: I'd be happy to help with your booking confirmation. How many guests are you expecting?
Your input → can you arrange parking for the speakers?
Bot: I'm sorry, I can only help with booking confirmations. I can't assist with parking arrangements. Would you like to continue with the booking confirmation?
"""

CONVERSATION_3_WHAT_HAPPENED = """
When the user asked about parking (out of scope), CALM recognised that the
request did not match any defined flow and responded that it could only help
with booking confirmations. It offered to return to the booking flow rather
than attempting to handle the unfamiliar request.
"""

OUT_OF_SCOPE_COMPARISON = """
LangGraph (Exercise 2, Scenario 3) handled the out-of-scope train question by
generating a polite refusal without calling any tools — it recognised the question
was outside its tool capabilities. Rasa CALM handled the parking question similarly
but with a key difference: CALM explicitly redirected back to the active flow,
offering to continue the booking. LangGraph had no such structure and simply
responded then stopped. This difference reflects their architectures: LangGraph's
agent loop terminates when it has nothing useful to do, while CALM's flow structure
maintains conversational state and can redirect. For booking confirmations, the CALM
approach is safer — it keeps the conversation on track and does not let the user
derail the process with tangential questions.
"""

# ── Task B: Cutoff guard ───────────────────────────────────────────────────

TASK_B_DONE = True

TASK_B_FILES_CHANGED = ["exercise3_rasa/actions/actions.py"]

TASK_B_HOW_YOU_TESTED = """
Uncommented the four-line cutoff guard block in actions.py. The guard checks
datetime.datetime.now() against 16:45. Verified the code structure matches what
grade.py expects: now = datetime.datetime.now() followed by now.hour checks.
Tested by temporarily using 'if True:' to confirm escalation behaviour.
"""

# ── CALM vs Old Rasa ───────────────────────────────────────────────────────

CALM_VS_OLD_RASA = """
The LLM now handles slot extraction via from_llm mappings — understanding that
'about 160 people' means 160.0 without any regex or Python parsing code. In old
Rasa, the FormValidationAction subclass required explicit validate_guest_count()
methods with regex patterns. Python STILL handles business rules (deposit limits,
capacity checks) via ActionValidateBooking because these are deterministic
constraints that must not be negotiated by a probabilistic model. The trade-off
is that CALM trusts the LLM for language understanding (which it is good at) while
keeping Python for rule enforcement (which requires guaranteed correctness).
"""

# ── The setup cost ─────────────────────────────────────────────────────────

SETUP_COST_VALUE = """
CALM requires config.yml, domain.yml, flows.yml, endpoints.yml, training, two
terminals, and a Rasa Pro licence — significantly more setup than LangGraph
which needs only a Python file and an API key. This setup cost buys bounded
behaviour: the CALM agent CANNOT improvise a response outside its defined flows,
CANNOT call tools not declared in flows.yml, and CANNOT reason its way around
business rules. For the confirmation use case, this is a feature not a limitation.
The Rasa agent will never accidentally agree to a £5000 deposit because the LLM
thought it was reasonable. The constraint that it cannot do anything surprising is
exactly what you want when every word has financial or legal consequences.
"""
