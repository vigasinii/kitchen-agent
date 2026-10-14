# Design Write-up — Kitchen Agent

## The core insight

Meal planning looks simple: pick seven dinners, buy the groceries. The real problem is the household is not a single person. It is Sarah who will not eat meat, Emma who cannot eat peanuts, George who needs soft foods and low sugar, and Mike who just wants a proper meal. Every plan has to satisfy all four simultaneously, every day, without anyone having to remind the agent about the constraints it already knows.

I chose two agents over one because the jobs are genuinely different. The Planner Agent needs broad food knowledge and the ability to negotiate. The Cook Agent needs to be fast, calm and practical mid-cooking. Splitting them means each agent can have a sharper, more focused system prompt and conversation history, which matters when the context window is short.

## Key decisions

**Dynamic meal generation over a fixed plan.** The earlier version returned a hardcoded plan regardless of the household. The new version sends household constraints to the LLM and asks it to generate a plan from scratch. This is what the founders are most likely to probe: if they add a new household member with a different restriction, the plan should change. A fixed plan cannot demonstrate that understanding.

**Pre-save safety validation as a hard gate.** LLMs hallucinate. A planner might confidently suggest a meal that contains a trigger allergen. Rather than rely on the prompt to prevent this, every meal update now runs through a deterministic validator before it reaches the database. If the validator finds a critical violation (allergy trigger, meat for a vegetarian with no noted alternative), the save is rejected and the agent is told to try a different meal. The system cannot be talked into an unsafe state by a user or the model.

**Structured approval workflow.** When the cook runs into a problem that changes the plan significantly (out of the planned protein, substituting a different dish), they flag it with the `flag_household_approval_needed` tool. The flag is persisted on the cook session. The household can then approve or reject it via a dedicated endpoint, with the decision recorded in the session notes. This gives the founders a concrete demonstration of the cook-to-household feedback loop they described.

## Trade-offs and what I left out on purpose

The ingredient safety checker is keyword-based. It will not catch every cross-contact risk (e.g. "may contain traces of" from packaged goods), which a production system would need. I left this as-is because the right solution is a food-composition API or a curated ingredient database, not more keyword rules.

Voice is powered by the browser's Web Speech API. This is real transcription, not a mock, but it only works in Chrome and Edge and has no fallback. A production version would use Whisper or a similar model.

Instamart is simulated. The grocery list generation and consolidation are real logic; the final ordering step returns a fake order ID. The interface for real API integration is clear from the code structure.

Conversation history is stored per session in SQLite. Long conversations are truncated to the 20 most recent messages to stay within the model's context window. A production version would use a proper summarization step.

## What I would do next

1. Add a household management screen to add, edit and remove members — the constraints should be editable, not hardcoded.
2. Replace keyword-based allergy detection with an ingredient-composition API for packaged foods.
3. Add a "learning from friction" loop: when the cook substitutes an ingredient three weeks in a row, the planner should update its model of what the household actually has in stock.
4. Extend the evaluation suite to cover multi-turn conversation scenarios, not just single function calls.
5. Add real Instamart integration or a WhatsApp message flow for the grocery list handoff.
