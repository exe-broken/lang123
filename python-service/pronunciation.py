from difflib import SequenceMatcher
import re
import unicodedata
from google import genai
from dotenv import load_dotenv

load_dotenv()

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate
    HAS_INDIC_TRANS = True
except Exception:
    HAS_INDIC_TRANS = False

try:
    client = genai.Client()
except Exception:
    client = None

# Script mapping for indic-transliteration
SCRIPT_MAP = {
    "kannada": getattr(sanscript, "KANNADA", "kannada") if HAS_INDIC_TRANS else None,
    "tamil": getattr(sanscript, "TAMIL", "tamil") if HAS_INDIC_TRANS else None,
    "telugu": getattr(sanscript, "TELUGU", "telugu") if HAS_INDIC_TRANS else None,
    "malayalam": getattr(sanscript, "MALAYALAM", "malayalam") if HAS_INDIC_TRANS else None,
    "tulu": getattr(sanscript, "KANNADA", "kannada") if HAS_INDIC_TRANS else None,
    "kodava": getattr(sanscript, "KANNADA", "kannada") if HAS_INDIC_TRANS else None,
}

# Fallback phonetic maps for Indic digits & characters
CHAR_PHONETIC_MAP = {
    # Digits
    '೦': 'sonne', '೧': 'ondu', '೨': 'eradu', '೩': 'mooru', '೪': 'naalku',
    '೫': 'aidu', '೬': 'aaru', '೭': 'elu', '೮': 'entu', '೯': 'ombhattu',
    '௦': 'sonna', '௧': 'ondru', '௨': 'irandu', '௩': 'moondru', '௪': 'naangu',
    '௫': 'ainthu', '௬': 'aaru', '௭': 'ezhu', '௮': 'ettu', '௯': 'onbadhu',
}

def to_latin(text, language="kannada"):
    if not text:
        return ""
    text = re.sub(r"\([^)]*\)", "", text).strip()
    
    # Check fallback map first for character/number matches
    for k, v in CHAR_PHONETIC_MAP.items():
        text = text.replace(k, v)

    if HAS_INDIC_TRANS:
        script = SCRIPT_MAP.get(language.lower())
        if script:
            try:
                res = transliterate(text, script, sanscript.ITRANS)
                return res.lower().strip()
            except Exception:
                pass
    return text.lower().strip()

def clean(text):
    if not text:
        return ""
    # Strip parenthetical annotations e.g. "೦ (0)" -> "೦"
    text = re.sub(r"\([^)]*\)", "", text)
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return text

def similar(a, b, language="kannada"):
    if not a or not b:
        return 0.0
    
    a_clean, b_clean = clean(a), clean(b)
    if not a_clean or not b_clean:
        return 0.0

    # 1. Direct clean similarity
    sim_direct = SequenceMatcher(None, a_clean, b_clean).ratio()
    if sim_direct > 0.85:
        return sim_direct

    # 2. Transliterated Latin similarity
    a_lat = to_latin(a, language)
    b_lat = to_latin(b, language)
    sim_lat = SequenceMatcher(None, clean(a_lat), clean(b_lat)).ratio()

    # 3. Cross-mix (a_clean vs b_lat, a_lat vs b_clean)
    sim_cross1 = SequenceMatcher(None, a_clean, clean(b_lat)).ratio()
    sim_cross2 = SequenceMatcher(None, clean(a_lat), b_clean).ratio()

    return max(sim_direct, sim_lat, sim_cross1, sim_cross2)

def get_ai_tip(expected, transcription, word_breakdown, language):
    """
    Optional AI tip generator using Gemini.
    Catches 429 rate-limits silently so the app NEVER fails!
    """
    if not client:
        return None
    mistakes = [w for w in word_breakdown if w.get('status') != 'correct']
    if not mistakes:
        return None
        
    mistakes_str = ", ".join([f"Expected '{w['word']}' but heard '{w.get('spoken_as', 'nothing')}'" for w in mistakes])
    
    prompt = f"""You are a gentle {language} language tutor. The student tried to say: '{expected}'.
They said: '{transcription}'.
Specific mistakes: {mistakes_str}

Give a 1-sentence tip on how to improve the pronunciation of the specific sounds they got wrong. Be extremely concise. Focus purely on phonetic placement (e.g. lips, tongue) or sound. No greetings."""

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        return response.text.strip() if response and response.text else None
    except Exception as e:
        safe_e = str(e).encode('ascii', 'backslashreplace').decode('ascii')
        print(f"[AI TIP NOTICE] Could not generate tip (API limit/error): {safe_e}")
        return None

def _calculate_score(transcription, expected, language="kannada"):
    trans_clean = clean(transcription)
    exp_clean = clean(expected)

    if not trans_clean or not exp_clean:
        return 0, []

    trans_words = trans_clean.split()
    expected_words = exp_clean.split()

    # Sentence-level similarity
    sentence_sim = similar(exp_clean, trans_clean, language)

    # Word-level partial credit
    word_score = 0.0
    word_breakdown = []

    for exp_word in expected_words:
        if trans_words:
            best_match = max(trans_words, key=lambda t: similar(exp_word, t, language))
            best_score = similar(exp_word, best_match, language)
        else:
            best_match = None
            best_score = 0.0
            
        word_score += best_score
        score_percent = round(best_score * 100)
        
        if score_percent >= 70:
            status = "correct"
        elif score_percent >= 40:
            status = "mispronounced"
        else:
            status = "missing"
            
        word_breakdown.append({
            "word": exp_word,
            "spoken_as": best_match if status != "missing" else None,
            "score": score_percent,
            "status": status
        })

    word_sim = word_score / len(expected_words) if expected_words else 0.0
    accuracy = round(((sentence_sim * 0.4) + (word_sim * 0.6)) * 100)
    
    return accuracy, word_breakdown

def assess(transcription, expected_native, expected_phonetics="", language="Language"):
    # Compare against native script
    acc_native, breakdown_native = _calculate_score(transcription, expected_native, language)
    
    # Compare against phonetics if available
    acc_phonetics = 0
    breakdown_phonetics = []
    if expected_phonetics:
        acc_phonetics, breakdown_phonetics = _calculate_score(transcription, expected_phonetics, language)
        
    # Pick whichever match is better (native vs phonetics)
    if acc_phonetics > acc_native:
        accuracy = acc_phonetics
        word_breakdown = breakdown_phonetics
        target = expected_phonetics
    else:
        accuracy = acc_native
        word_breakdown = breakdown_native
        target = expected_native

    # Generate AI tip (fails gracefully if API quota is reached)
    ai_tip = get_ai_tip(target, transcription, word_breakdown, language)
    
    return accuracy, word_breakdown, ai_tip