import langcodes
import streamlit as st
from deep_translator import GoogleTranslator
from langdetect import DetectorFactory, LangDetectException, detect
from nltk.tokenize import TreebankWordDetokenizer, wordpunct_tokenize
from spellchecker import SpellChecker

DetectorFactory.seed = 0
MIN_INPUT_LENGTH = 3

SPELL_LANGS = {
    "en", "es", "fr", "pt", "de", "ru", "ar", "eu", "lv", "nl"
}

TARGET_LANGS = {
    "Vietnamese": "vi",
    "English": "en",
    "French": "fr",
    "Japanese": "ja",
    'Chinese': "zh-CN",
    "Korean": "ko",
    "Spanish": "es",
    "German": "de"
}

EXAMPLES_T = [
    'Every morning, I drink a cup of coffee.',
    "Bonjour, comment allez-vous?",
    "Xin chao, hom nay troi dep qua."
]

EXAMPLE_S = [
    "Yesturday, I recieveed a mesage from my freind.",
    "Definately a great oppurtunity.",
    "Je voudraiis allerr au marchee."
]

@st._cache_resource(show_spinner=False)
def get_spellchecker(code):
    return SpellChecker(language=code)

def language_name(code):
    try:
        return langcodes.Language.get(code).display_name()
    except Exception:
        return code or "Unknown"
    
def detect_language(raw):
    try:
        return detect(raw)
    except LangDetectException:
        return None
    
def fix_typos(text, code):
    spell = get_spellchecker(code)
    tokens = wordpunct_tokenize(text)
    fixed = []

    for token in tokens:
        if token.isalpha() and len(token) > 1:
            suggestion = spell.correction(token.lower()) or token
            suggestion = suggestion.title() if token.istitle() else suggestion
            suggestion = suggestion.upper() if token.isupper() else suggestion
            fixed.append(suggestion)
        else:
            fixed.append(token)

    return TreebankWordDetokenizer().detokenize(fixed), fixed != tokens

def run_translation(text, target_code):
    raw = text.strip()

    if len(raw) < MIN_INPUT_LENGTH:
        return {"ok": False, "error": f"Minimun length {MIN_INPUT_LENGTH} characters."}
    
    source = detect_language(raw)

    if source is None:
        return {"ok": False, "error": "Cannot detect language."}
    
    if source == target_code:
        return {
            "ok": True,
            "source": language_name(source),
            "target": language_name(target_code),
            "translated": raw,
            "note": "Succesfully translated!!!"
        }
    
    try:
        translated = GoogleTranslator(source=source, target=target_code).translate(raw)
    except Exception as e:
        return {"ok":False, "error": f'Translation error: {e}'}
    
    return {
        "ok": True,
        "source": language_name(source),
        "target": language_name(target_code),
        "translated": translated
    }

def run_spellcheck(text):
    raw = text.strip()

    if len(raw) < MIN_INPUT_LENGTH:
        return {"ok": False, "error": f"Minimum length {MIN_INPUT_LENGTH} characters."}

    code = detect_language(raw)

    if code is None:
        return {"ok": False, "error": "Cannot detect language."}
    
    if code not in SPELL_LANGS:
        return {
            "ok": False, 
            "error": f"pyspellchecker has not supported {language_name(code)} ({code}) yet."
        }
    
    fixed, changed = fix_typos(raw, code)

    return {
        "ok": True,
        "language": language_name(code),
        "fixed": fixed,
        "changed": changed
    }

st.set_page_config(page_title="NLP Piepline Demo", layout="centered")
st.title("Streamlit NLP Pipeline Demo")
st.caption("Two features: Translation - Spell correction")

tab_t, tab_s = st.tabs(["Translate", "Correct"])

with tab_t:
    st.session_state.setdefault("res_t", None)

    with st.expander("Example"):
        for ex in EXAMPLES_T:
            st.markdown(f"- {ex}")

    with st.form("form_translate"):
        text_t = st.text_area(
            'Prompt',
            height=90,
            placeholder="Input any language here..."
        )

        target = st.selectbox("Translate to", list(TARGET_LANGS .keys()))
        submitted_t = st.form_submit_button('Translate', type="primary")

    if submitted_t:
        st.session_state.res_t = run_translation(text_t, TARGET_LANGS[target])
    
    res = st.session_state.res_t

    if res:
        if res["ok"]:
            st.caption(f"Resource: {res['source']} -> Target: {res['target']}")
            st.success(res["translated"])
            if res.get("note"):
                st.info(res["note"])
        else:
            st.warning(res["error"])

with tab_s:
    st.session_state.setdefault("res_s", None)

    with st.expander("Example"):
        for ex in EXAMPLE_S:
            st.markdown(f"- {ex}")
    
    st.caption(f"Support: {', '.join(sorted(SPELL_LANGS))}")

    with st.form("form_spell"):
        text_s = st.text_area(
            "Prompt",
            height=90,
            placeholder="Input your prompt here..."
        )
        submitted_s = st.form_submit_button("Check", type='primary')

    if submitted_s:
        st.session_state.res_s = run_spellcheck(text_s)
    
    res = st.session_state.res_s

    if res:
        if res["ok"]:
            st.caption(f"Language: {res['language']}")
            st.success(res["fixed"])
            st.caption("The error detected" if res["changed"] else "Cannot find the error")
        else:
            st.warning(res["error"])