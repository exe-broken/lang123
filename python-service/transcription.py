from faster_whisper import WhisperModel
import os

# Load Whisper 'base' model locally (configured with multi-threading for speed)
cpu_threads = max(1, (os.cpu_count() or 4) // 2)
print(f"[WHISPER] Loading local Whisper model 'base' with {cpu_threads} CPU threads...")
try:
    model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=cpu_threads)
    print("[WHISPER] Local model loaded successfully!")
except Exception as e:
    print(f"[WHISPER ERROR] Failed to load base model, trying tiny: {e}")
    model = WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=cpu_threads)

LANG_MAP = {
    "kannada": "kn",
    "tamil": "ta",
    "telugu": "te",
    "malayalam": "ml",
    "tulu": "kn",
    "kodava": "kn",
}

def transcribe(audio_path, language_name, phrase="", phonetics=""):
    """
    Transcribes audio locally using faster-whisper.
    Fast (< 1s), zero API cost, high accuracy.
    """
    lang_code = LANG_MAP.get(language_name.lower(), "kn")
    
    # Construct initial prompt to ground Whisper in expected script/sounds
    prompt_parts = [f"{language_name} speech practice"]
    if phrase:
        prompt_parts.append(phrase)
    if phonetics:
        prompt_parts.append(phonetics)
    initial_prompt = ", ".join(prompt_parts)

    print(f"[WHISPER] Transcribing audio for language '{language_name}' (code: {lang_code})...")
    segments, info = model.transcribe(
        audio_path,
        language=lang_code,
        beam_size=1,
        vad_filter=False,                         # Disable VAD filter so short single words/vowels are never trimmed
        initial_prompt=initial_prompt,             # Guide model to correct Indic vocabulary
        condition_on_previous_text=False,          # Prevent hallucination loops
        temperature=0.0,                           # Deterministic greedy decoding
    )
    
    text = " ".join([s.text.strip() for s in segments]).strip()
    safe_text = text.encode('ascii', 'backslashreplace').decode('ascii')
    print(f"[WHISPER SUCCESS] Spoken text: '{safe_text}' (lang prob: {info.language_probability:.2f})")
    return text