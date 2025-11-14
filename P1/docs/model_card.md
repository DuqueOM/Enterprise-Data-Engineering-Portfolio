
# Model Card — Asistente PYME (LoRA)

## Model details
Base model: google/flan-t5-base (recommended for Seq2Seq fine-tuning)
PEFT: LoRA (r=8, alpha=32), training on Q/A dataset for legal-administrative language.

## Intended use
Assist SMEs with administrative queries. Not a substitute for professional legal or tax advice.
Include a visible disclaimer in the UI.

## Limitations & Risks
- Factuality depends on retrieval quality and source freshness.
- Must cite sources and dates.
- Avoid indexing PII.
