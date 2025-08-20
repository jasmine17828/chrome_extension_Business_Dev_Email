
# FastAPI backend for the Chrome Extension (with diagnostics & health endpoints)
# Run: uvicorn server:app --host 0.0.0.0 --port 8000 --reload

import os, logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

app = FastAPI(title="AI Business Dev Email Backend", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Health & diagnostics ----
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Backend is running",
        "endpoints": ["POST /generate", "GET /healthz"],
        "lite_mode": os.getenv("LITE_MODE", "0"),
        "version": "1.1.0"
    }

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/generate")
def generate_get_hint():
    return {
        "error": "Use POST /generate",
        "example_payload": {
            "your_company": "Your Co.",
            "your_name": "Jasmine",
            "your_title": "BD Manager",
            "target_company": "Acme Inc.",
            "company_profile": "Paste the target company's intro here..."
        }
    }

# ---- Models (lazy loaded) ----
LITE_MODE = os.getenv("LITE_MODE", "0") == "1"

if not LITE_MODE:
    from transformers import pipeline, MarianMTModel, MarianTokenizer
    from langdetect import detect
    import langid

def robust_lang_detect(text: str) -> str:
    if LITE_MODE:
        return "en"
    try:
        lang = detect(text)
    except Exception:
        lang = ""
    if lang not in ['zh-cn', 'zh-tw', 'zh', 'en']:
        lang2, _ = langid.classify(text)
        lang = lang2
    return lang

def remove_duplicate_lines(text: str) -> str:
    lines = text.strip().split('\n')
    new_lines = []
    for line in lines:
        if not new_lines or line.strip() != new_lines[-1].strip():
            new_lines.append(line)
    return '\n'.join(new_lines)

_tokenizer_zh2en = None
_model_zh2en = None
_summarizer = None
_generator = None

def _get_zh2en():
    global _tokenizer_zh2en, _model_zh2en
    if _tokenizer_zh2en is None or _model_zh2en is None:
        log.info("Loading zh->en translation model... This may download weights on first run.")
        _tokenizer_zh2en = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-zh-en")
        _model_zh2en = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-zh-en")
    return _tokenizer_zh2en, _model_zh2en

def _get_summarizer():
    global _summarizer
    if _summarizer is None:
        log.info("Loading summarization model (bart-large-cnn)...")
        _summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    return _summarizer

def _get_generator():
    global _generator
    if _generator is None:
        log.info("Loading generator model (flan-t5-base)...")
        _generator = pipeline("text2text-generation", model="google/flan-t5-base")
    return _generator

class GenPayload(BaseModel):
    your_company: str
    your_name: str
    your_title: str
    target_company: str
    company_profile: str

@app.post("/generate")
def generate(payload: GenPayload):
    your_company = payload.your_company.strip() or "Your Company"
    your_name = payload.your_name.strip() or "Your Name"
    your_title = payload.your_title.strip() or "BD Manager"
    target_company = payload.target_company.strip() or "Target Company"
    company_profile = payload.company_profile.strip()

    if not company_profile:
        return {"error": "Empty company profile."}

    if LITE_MODE:
        # Lightweight template path (no models required)
        summary_en = company_profile[:180]
        interest = ("We see strong partnership potential given your capabilities and our offerings. "
                    "We'd love to explore a collaboration that drives mutual growth.")
        email_body_en = (
            f"Dear {target_company} Team,\n\n"
            f"My name is {your_name}, and I am a {your_title} at {your_company}.\n\n"
            f"I recently learned about your company and was impressed by: {summary_en}\n\n"
            f"{interest}\n\n"
            f"We believe there are meaningful opportunities for partnership between our companies. "
            f"If you are interested, I would be delighted to schedule a call or meeting to discuss further.\n\n"
            f"Best regards,\n{your_name}\n{your_title}\n{your_company}"
        )
        filename = f"Business_Dev_Email_{target_company}_{datetime.today().strftime('%Y%m%d')}.txt"
        return {"email_body_en": email_body_en, "filename": filename}

    # Full model path with graceful error messages
    try:
        lang = robust_lang_detect(company_profile)
        if lang.startswith('zh'):
            tok, mdl = _get_zh2en()
            tokens = tok(company_profile, return_tensors="pt", truncation=True, max_length=512)
            translation = mdl.generate(**tokens)
            intro_en = tok.decode(translation[0], skip_special_tokens=True)
        else:
            intro_en = company_profile
    except Exception as e:
        return {
            "error": "Translation model unavailable.",
            "hint": "First run requires internet to download Hugging Face weights. Or set LITE_MODE=1 to skip models.",
            "details": str(e)[:500]
        }

    try:
        if len(intro_en.strip()) < 60 or intro_en.count('.') < 2:
            summary_en = intro_en[:180] if intro_en else "(No valid summary found)"
        else:
            summarizer = _get_summarizer()
            summary_en = summarizer(intro_en, max_length=80, min_length=15, do_sample=False)[0]['summary_text']
    except Exception as e:
        return {
            "error": "Summarization model unavailable.",
            "hint": "Ensure model download completed. Or set LITE_MODE=1 to skip models.",
            "details": str(e)[:500]
        }

    try:
        generator = _get_generator()
        interest_prompt = (
            f"As a business development manager at {your_company}, write 3-4 sentences explaining why you are "
            f"interested in partnering with {target_company}, using the following summary: {summary_en} "
            f"Do not mention job applications, do not write as a candidate. Focus on B2B cooperation."
        )
        interest_detail = generator(
            interest_prompt,
            max_length=140,
            do_sample=False,
            num_beams=4,
            no_repeat_ngram_size=4
        )[0]['generated_text']
        interest_detail = remove_duplicate_lines(interest_detail)
    except Exception as e:
        return {
            "error": "Generation model unavailable.",
            "hint": "Ensure model download completed. Or set LITE_MODE=1 to skip models.",
            "details": str(e)[:500]
        }

    greeting = f"Dear {target_company} Team,"
    self_intro = f"My name is {your_name}, and I am a {your_title} at {your_company}."
    summary_part = f"I recently learned about your company and was impressed by: {summary_en}"
    action = (
        "We believe there are meaningful opportunities for partnership between our companies. "
        "If you are interested, I would be delighted to schedule a call or meeting to discuss further."
    )
    closing = f"Best regards,\n{your_name}\n{your_title}\n{your_company}"

    email_body_en = f"{greeting}\n\n{self_intro}\n\n{summary_part}\n\n{interest_detail}\n\n{action}\n\n{closing}"
    if len(interest_detail.strip()) < 20:
        fallback_interest = (
            "We admire your company's accomplishments and are eager to explore how we can collaborate "
            "to achieve mutual growth and innovation."
        )
        email_body_en = f"{greeting}\n\n{self_intro}\n\n{summary_part}\n\n{fallback_interest}\n\n{action}\n\n{closing}"

    filename = f"Business_Dev_Email_{target_company}_{datetime.today().strftime('%Y%m%d')}.txt"
    return {"email_body_en": email_body_en.strip(), "filename": filename}
