---
description: Fact-check drug, target, or clinical data using Perplexity MCP
---

Use the perplexity-fact-checker agent to verify the data specified by the user.

User query: $ARGUMENTS

If no specific query is provided, ask the user what they want to fact-check. Examples:
- A specific drug (e.g., "fact-check GSK126 clinical phase and mechanism")
- A target (e.g., "verify EZH2 tractability data")
- Recent ETL data (e.g., "spot-check the latest flagship drugs we ingested")

The agent should:
1. Identify what needs to be verified
2. Query Perplexity for authoritative sources
3. Compare against our database values
4. Report discrepancies with source citations
