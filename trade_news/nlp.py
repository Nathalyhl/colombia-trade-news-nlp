"""Interpretable Spanish headline rules; every tag/score retains matched evidence."""
import html
import re
import unicodedata

METHOD = "spanish_headline_lexicon_v1"
THEMES = {
    "trade_flows": ["exportacion", "exportaciones", "importacion", "importaciones", "balanza comercial", "comercio exterior"],
    "tariffs_and_policy": ["arancel", "aranceles", "aduana", "aduanas", "sanciones"],
    "trade_agreements": ["tratado", "acuerdo comercial", "tlc", "libre comercio", "mercosur", "alianza del pacifico"],
    "logistics": ["puerto", "puertos", "flete", "fletes", "transporte maritimo", "logistica", "contenedores"],
    "exchange_and_prices": ["dolar", "tasa de cambio", "devaluacion", "precio", "precios", "inflacion"],
    "investment": ["inversion", "inversiones", "inversion extranjera"],
}
SECTORS = {
    "agriculture": ["cafe", "cafetero", "cafeteras", "flores", "banano", "aguacate", "agro", "agricola", "agropecuario", "cacao"],
    "energy_and_mining": ["petroleo", "petrolero", "carbon", "mineria", "oro", "gas", "hidrocarburos"],
    "manufacturing": ["manufactura", "industria", "industrial", "textil", "textiles", "confecciones", "automotriz", "quimicos"],
    "services": ["servicios", "turismo", "software", "bpo"],
    "food": ["alimentos", "carne", "carnicos", "lacteos", "azucar", "pesca", "pescado"],
}
PARTNERS = {
    "United States": ["estados unidos", "ee uu", "eeuu", "usa", "estadounidense"],
    "China": ["china", "chino", "chinos"], "European Union": ["union europea", "ue"],
    "Venezuela": ["venezuela", "venezolano"], "Ecuador": ["ecuador", "ecuatoriano"],
    "Peru": ["peru", "peruano"], "Brazil": ["brasil", "brasileno"],
    "Mexico": ["mexico", "mexicano"], "Spain": ["espana", "espanol"],
    "Panama": ["panama", "panameno"], "India": ["india"],
}
# Review-authored tone cues; weights are transparent choices, not learned coefficients.
POLARITY = {
    "crece": 1, "crecen": 1, "crecimiento": 1, "aumenta": 1, "aumentan": 1,
    "aumento": 1, "aumentaron": 1, "repunte": 1, "recuperacion": 1,
    "recupera": 1, "record": 1, "impulsa": 1, "impulso": 1, "oportunidad": 1,
    "oportunidades": 1, "fortalece": 1, "avance": 1, "avanza": 1, "mejora": 1,
    "cae": -1, "caen": -1, "caida": -1, "cayeron": -1, "crisis": -1,
    "riesgo": -1, "riesgos": -1, "amenaza": -1, "amenazas": -1,
    "desaceleracion": -1, "retroceso": -1, "pierde": -1, "perdidas": -1,
    "incertidumbre": -1, "barrera": -1, "barreras": -1, "bloqueo": -1,
    "deficit": -1, "contraccion": -1, "tension": -1, "tensiones": -1,
}
NEGATORS = {"no", "nunca", "sin", "ni"}


def clean_text(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def normalize(text):
    value = "".join(c for c in unicodedata.normalize("NFKD", clean_text(text).casefold()) if not unicodedata.combining(c))
    return " ".join(re.findall(r"[a-z0-9]+", value))


def tag(text, vocabulary):
    value = " " + normalize(text) + " "
    evidence = {label: [term for term in terms if " " + term + " " in value]
                for label, terms in vocabulary.items()}
    return {label: terms for label, terms in evidence.items() if terms}


def sentiment(text):
    tokens = normalize(text).split()
    evidence = []
    for index, token in enumerate(tokens):
        if token not in POLARITY:
            continue
        negated = any(t in NEGATORS for t in tokens[max(0, index-3):index])
        weight = POLARITY[token] * (-1 if negated else 1)
        evidence.append({"term": token, "weight": weight, "negated": negated})
    score = sum(e["weight"] for e in evidence) / len(evidence) if evidence else None
    label = "unscored" if score is None else "positive" if score > 0 else "negative" if score < 0 else "neutral"
    return {"sentiment": label, "tone_score": score, "sentiment_evidence": evidence,
            "sentiment_method": METHOD, "validated_for_domain": False}


def analyze(text):
    themes, sectors, partners = tag(text, THEMES), tag(text, SECTORS), tag(text, PARTNERS)
    normal = normalize(text)
    geographic = bool(re.search(r"\b(colombia|colombiano|colombiana|colombianos|colombianas)\b", normal))
    commercial = bool(themes.keys() & {"trade_flows", "tariffs_and_policy", "trade_agreements", "logistics"})
    static_page = "observatorio de complejidad" in normal or "col exportaciones importaciones y socios" in normal
    return {"title_clean": clean_text(text), "title_normalized": normal,
            "relevant": geographic and commercial and not static_page,
            "relevance_method": "explicit_Colombia_and_trade_terms_in_headline_v1",
            "themes": list(themes), "sectors": list(sectors), "partners": list(partners),
            "tag_evidence": {"themes": themes, "sectors": sectors, "partners": partners}, **sentiment(text)}
