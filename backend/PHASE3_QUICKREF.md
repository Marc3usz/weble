# Phase 3 Quick Reference Guide

## TL;DR

Phase 3 adds **AI-powered assembly instruction generation** using OpenRouter's Gemini API. When enabled, instructions are generated with tone awareness (IKEA/TECHNICAL/BEGINNER) and include exploded view diagrams. Falls back to rules-based generation if the API is unavailable.

---

## Setup (5 minutes)

### 1. Set API Key
```bash
# backend/.env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxx
```
Get key at: https://openrouter.ai/keys

### 2. Verify Installation
```bash
cd backend
python -m pytest tests/test_llm_assembly_generator.py -v
# Should see: 25 passed
```

### 3. Run Full Test Suite
```bash
python -m pytest tests/ -v
# Should see: 139 passed (50 Phase 1-2 + 89 Phase 3)
```

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENROUTER_API_KEY` | (required) | API authentication |
| `ASSEMBLY_LLM_ENABLED` | `True` | Enable/disable Phase 3 |
| `ASSEMBLY_TONE` | `ikea` | Default tone (ikea/technical/beginner) |
| `ASSEMBLY_LLM_MODEL` | `google/gemini-2.0-flash` | LLM model |
| `LLM_TIMEOUT_SECONDS` | `30` | API call timeout |
| `LLM_MAX_TOKENS` | `2000` | Max response tokens |

### Code Configuration (`backend/app/core/config.py`)

```python
from app.core.config import AssemblyTone

# Use in API requests
tone = AssemblyTone.IKEA        # Friendly & accessible
tone = AssemblyTone.TECHNICAL   # Precise & technical
tone = AssemblyTone.BEGINNER    # Extra detailed & safe
```

---

## Usage

### Basic API Call (Flask/FastAPI)

```python
from app.services.assembly_generator import AssemblyGeneratorService
from app.core.config import AssemblyTone

# Initialize service (LLM auto-injected if enabled)
service = AssemblyGeneratorService()

# Generate instructions
steps = service.process(
    parts=extracted_parts,
    tone=AssemblyTone.IKEA,  # or TECHNICAL, BEGINNER
    preview_mode=False
)

# Each step has:
# - title: str
# - description: str
# - detail_description: str (LLM-generated)
# - assembly_sequence: List[AssemblyAction] (LLM-generated)
# - is_llm_generated: bool (True if LLM, False if fallback)
# - exploded_view_svg: str (SVG diagram)
# - confidence_score: float (0.0-1.0)
```

### With Custom LLM Service

```python
from app.services.llm_assembly_generator import LLMAssemblyGeneratorService

llm_service = LLMAssemblyGeneratorService(api_key="sk-or-v1-xxx")
service = AssemblyGeneratorService(llm_service=llm_service)
steps = service.process(parts, tone=AssemblyTone.TECHNICAL)
```

---

## Assembly Tones at a Glance

### 🎈 IKEA
- **For:** General users
- **Style:** Friendly, encouraging, emoji-heavy
- **Example:** "This is fun! 👍 Just pop the bracket in here..."

### 🔧 TECHNICAL  
- **For:** Engineers, precise specifications
- **Style:** Formal, spec-focused, no emoji
- **Example:** "Insert bracket at 90° angle with 15mm tolerance..."

### 📚 BEGINNER
- **For:** First-time assemblers
- **Style:** Very detailed, safety-focused, extra tips
- **Example:** "Carefully insert bracket (the metal L-shaped part). Make sure the longer edge points up..."

---

## Testing

### Run Phase 3 Tests Only
```bash
pytest tests/test_llm_assembly_generator.py -v
pytest tests/test_exploded_view_generator.py -v
pytest tests/test_assembly_generator_phase3.py -v
pytest tests/test_phase3_integration.py -v
pytest tests/test_phase3_performance.py -v
```

### Run Regression Tests (Phase 1-2)
```bash
pytest tests/test_assembly_generator.py -v
pytest tests/test_parts_extractor.py -v
pytest tests/test_step_loader.py -v
pytest tests/test_svg_generator.py -v
```

### Run All Tests
```bash
pytest tests/ -v  # 139 tests total
```

---

## Common Tasks

### Disable LLM (Use Rules-Based Only)
```bash
# backend/.env
ASSEMBLY_LLM_ENABLED=False
```
Instructions will use rules-based generation without API calls.

### Use Different Model
```bash
# backend/.env
ASSEMBLY_LLM_MODEL=anthropic/claude-3-5-sonnet
```
Must be an OpenRouter model. See: https://openrouter.ai/docs/models

### Preview Mode (No Exploded Views)
```python
steps = service.process(
    parts=extracted_parts,
    tone=AssemblyTone.IKEA,
    preview_mode=True  # Skips expensive SVG generation
)
```

### Check if Step is LLM-Generated
```python
for step in steps:
    if step.is_llm_generated:
        print(f"✓ LLM: {step.title}")
    else:
        print(f"⚠️  Fallback: {step.title}")
```

---

## Troubleshooting

### "API key not configured"
```bash
# Check .env file exists and has valid key
cat backend/.env | grep OPENROUTER_API_KEY

# Or test directly
python -c "from app.core.config import get_settings; print(get_settings().openrouter_api_key)"
```

### API calls timing out
```bash
# Increase timeout (default: 30s)
# backend/.env
LLM_TIMEOUT_SECONDS=60
```

### Response parsing fails (falls back to rules-based)
- **Why:** API returned unexpected JSON format
- **Mitigation:** Automatic fallback to rules-based generation (is_llm_generated=False)
- **Debug:** Check test logs in `backend/test_output.txt`

### Running out of tokens (hitting max_tokens limit)
```bash
# Increase token limit
# backend/.env
LLM_MAX_TOKENS=4000
```

---

## Architecture Diagram

```
ProcessingPipeline (Stage 4)
    ↓
AssemblyGeneratorService
    ├─ If LLM enabled:
    │   ├─ LLMAssemblyGeneratorService
    │   │   ├─ Build prompts (tone-aware)
    │   │   ├─ Call OpenRouter API
    │   │   ├─ Parse JSON response
    │   │   └─ On error → Fallback
    │   └─ ExplodedViewSVGGenerator
    │       └─ Create isometric diagrams
    │
    └─ If LLM disabled or failed:
        └─ Rules-based generation (Phase 2)
```

---

## Performance Notes

- **LLM API call:** ~2-5 seconds per assembly (depends on part count)
- **SVG generation:** ~0.5-1 second per step
- **Token estimation:** ~200-500 tokens per assembly (varies by complexity)
- **Typical cost:** $0.001-0.005 USD per assembly using Gemini 2.0 Flash

---

## Files Reference

| File | Purpose | Tests |
|------|---------|-------|
| `app/services/llm_assembly_generator.py` | LLM integration | 25 |
| `app/services/exploded_view_generator.py` | Isometric views | 25 |
| `app/services/assembly_generator.py` | Orchestration | 10 |
| `app/workers/pipeline.py` | Stage 4 wiring | 14 |
| `app/core/config.py` | Settings & tones | - |
| `app/models/schemas.py` | Data models | 15 |

---

## Next Steps

1. **Deploy:** Set `OPENROUTER_API_KEY` in production environment
2. **Monitor:** Track `is_llm_generated` field to measure fallback rate
3. **Optimize:** Adjust `LLM_MAX_TOKENS` and tone based on user feedback
4. **Extend:** Add new tones or models as needed

---

## Links

- **Full Documentation:** See `PHASE3_SUMMARY.md`
- **OpenRouter API Docs:** https://openrouter.ai/docs/api-reference
- **Test Results:** `backend/test_results.txt`
- **Supported Models:** https://openrouter.ai/docs/models

---

**Last Updated:** April 2026 | Status: ✅ Phase 3 Complete (139/139 tests passing)
