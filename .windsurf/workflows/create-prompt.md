---
description: prompt generation workflow
---

## Usage Rules

1. **Default (`create prompt`)** – When the user simply says "create prompt" (with no leading keyword), craft a new prompt tailored to the user’s latest message. The prompt should align with their stated goal and be ready to hand off to another AI for execution.
2. **Special (`analyze this ...`)** – When the user’s command begins with "analyze this", read the provided material and build a prompt that instructs another AI to analyze or verify that exact content. Ensure the requested output (analysis, validation, verification, etc.) matches the user’s wording.
3. Always clarify scope, deliverables, and constraints inside the generated prompt so the receiving AI can act without further clarification.
4. Include any relevant environment details (paths, commands, credentials) only if explicitly provided or already known to be safe to share.
5. Output the finished prompt in plain Markdown (no extra commentary) so it can be copy-pasted directly.
