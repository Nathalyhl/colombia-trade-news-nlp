"""Interpretable Spanish headline rules; every tag/score retains matched evidence."""
import html
import re
import unicodedata

METHOD = "spanish_headline_lexicon_v2"
SCOPE_METHOD = "colombian_goods_export_headline_v3"
ANALYSIS_SCOPE = "Colombian goods exports to the world"
EXPORT_CUE = re.compile(r"\bexport(?:acion(?:es)?|a(?:n|r|ra|ran|ron|ndo)?|o|ador(?:a|es|as)?)\b")
THEMES = {
    "exports": ["exportacion", "exportaciones", "exporta", "exportan", "exporto", "exportar", "exportando", "exportador", "exportadora", "exportadores", "exportadoras"],
    "tariffs_and_policy": ["arancel", "aranceles", "aduana", "aduanas", "sanciones"],
    "trade_agreements": ["tratado", "acuerdo comercial", "tlc", "libre comercio", "mercosur", "alianza del pacifico"],
    "logistics": ["puerto", "puertos", "flete", "fletes", "transporte maritimo", "logistica", "contenedores"],
    "exchange_and_prices": ["dolar", "tasa de cambio", "devaluacion", "precio", "precios", "inflacion"],
    "investment": ["inversion", "inversiones", "inversion extranjera"],
}
SECTORS = {
    "agriculture": ["cafe", "cafetero", "cafeteras", "flores", "banano", "aguacate", "agro", "agricola", "agropecuario", "cacao", "limon", "lima", "frutas", "palma"],
    "energy_and_mining": ["petroleo", "petrolero", "carbon", "mineria", "oro", "gas", "hidrocarburos", "energia", "electricidad", "combustibles", "coque", "minero energetico"],
    "manufacturing": ["manufactura", "manufacturas", "industria", "industrial", "textil", "textiles", "confecciones", "automotriz", "quimicos", "vehiculos", "carros", "cosmetica", "calzado"],
    "food": ["alimentos", "carne", "carnes", "carnicos", "lacteos", "azucar", "pesca", "pescado", "huevos", "ganado"],
}
GOODS_CUES = ["bienes", "mercancias", "productos", "manufacturas", "manufactura", "vehiculos", "carros", "automoviles",
              "cosmetica", "cosmeticos", "flores", "cafe", "banano", "aguacate", "cacao", "limon", "lima", "frutas",
              "vegetales", "semillas", "oro", "petroleo", "carbon", "coque", "energia", "electricidad", "combustibles",
              "hidrocarburos", "gas", "minerales", "carne", "carnes", "carnicos", "ganado", "lacteos", "leche",
              "alimentos", "snacks", "huevos", "palma", "textiles", "textil", "confecciones", "calzado", "madera",
              "plastico", "plasticos", "quimicos", "medicamentos", "agro", "agropecuario", "agropecuarias",
              "agricola", "agricolas", "minero energetico", "minero energeticas", "minero energeticos"]
SERVICE_CUES = ["servicios", "software", "turismo", "bpo", "ciberseguridad", "consultoria", "productos digitales"]
PARTNERS = {
    "United States": ["estados unidos", "ee uu", "eeuu", "usa", "estadounidense"],
    "China": ["china", "chino", "chinos"], "European Union": ["union europea", "ue"],
    "Venezuela": ["venezuela", "venezolano"], "Ecuador": ["ecuador", "ecuatoriano"],
    "Peru": ["peru", "peruano"], "Brazil": ["brasil", "brasileno"],
    "Mexico": ["mexico", "mexicano"], "Spain": ["espana", "espanol"],
    "Panama": ["panama", "panameno"], "India": ["india"],
    "Israel": ["israel", "israeli"], "Philippines": ["filipinas", "filipino", "filipina"],
    "Italy": ["italia", "italiano", "italiana"], "Canada": ["canada", "canadiense"],
    "United Kingdom": ["reino unido", "britanico", "britanica"],
    "Germany": ["alemania", "aleman", "alemana"], "France": ["francia", "frances", "francesa"],
    "Japan": ["japon", "japones", "japonesa"], "South Korea": ["corea del sur", "surcoreano", "surcoreana"],
    "Chile": ["chile", "chileno", "chilena"], "Argentina": ["argentina", "argentino"],
    "Costa Rica": ["costa rica", "costarricense"], "Netherlands": ["paises bajos", "holanda", "neerlandes"],
    "Turkey": ["turquia", "turco", "turca"], "United Arab Emirates": ["emiratos arabes unidos"],
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
    # Explicit inflections preserve the same cue families; no trained lemmatizer is claimed.
    "crecio": 1, "crecieron": 1, "crecer": 1, "crecera": 1, "creceran": 1,
    "creceria": 1, "crecerian": 1, "creciendo": 1,
    "aumentara": 1, "aumentaran": 1, "aumentaria": 1, "aumentarian": 1,
    "impulsan": 1, "impulsaron": 1, "impulsada": 1, "impulsadas": 1,
    "impulsado": 1, "impulsados": 1, "recuperan": 1, "recuperara": 1,
    "cayo": -1, "caido": -1, "caidas": -1, "pierden": -1, "perdio": -1,
    "perdieron": -1, "amenazan": -1,
}
NEGATORS = {"no", "nunca", "sin", "ni"}


def clean_text(text):
    value = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
    # This outlet's brand is not evidence of Colombian export origin.
    return re.sub(r"\s+\|\s+El Colombiano\s*$", "", value, flags=re.IGNORECASE)


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


def export_scope(text):
    """Require goods and Colombian export-origin cues; hold ambiguity for review."""
    normal = normalize(text)
    result = {"scope_status": "excluded", "scope_reason": "no_explicit_export_cue",
              "export_origin_evidence": [], "relevance_method": SCOPE_METHOD,
              "goods_evidence": tag(normal, {"goods": GOODS_CUES}).get("goods", []),
              "service_evidence": tag(normal, {"services": SERVICE_CUES}).get("services", [])}
    if "observatorio de complejidad" in normal or "las noticias del" in normal:
        return {**result, "scope_reason": "static_page_or_general_news_roundup"}
    if not EXPORT_CUE.search(normal):
        return result
    if re.search(r"\b(cocaina|narcotrafico|futbolistas|jugadores)\b", normal):
        return {**result, "scope_reason": "illicit_trade_or_sports_transfer_outside_goods_scope"}
    if not re.search(r"\b(colombia|colombian[oa]s?)\b", normal):
        return {**result, "scope_reason": "no_explicit_Colombian_origin"}
    inbound = re.search(r"\bexport\w*(?:\s+\w+){0,8}\s+(?:a|hacia|para)\s+colombia\b", normal)
    foreign_origin = re.search(
        r"\bexportacion(?:es)?\s+(?:de\s+(?:ecuador|peru|china|brasil|mexico|estados unidos)|"
        r"ecuatorianas?|peruanas?|chinas?|brasilenas?|mexicanas?|estadounidenses?)\b", normal)
    patterns = [
        r"\bexport\w*(?:\s+\w+){0,6}\s+(?:de|desde|en)\s+colombia\b",
        r"\bexport\w*(?:\s+\w+){0,6}\s+colombian[oa]s?\b",
        r"\bcolombian[oa]s?(?:\s+\w+){0,6}\s+export\w*\b",
        r"\bcolombia(?:\s+\w+){0,8}\s+export\w*\b",
        r"\bexport(?:a|an|o|ara|aran)\s+colombia\b",
    ]
    evidence = [match.group() for pattern in patterns for match in re.finditer(pattern, normal)]
    if inbound or foreign_origin:
        return {**result, "scope_status": "needs_review" if evidence else "excluded",
                "scope_reason": "inbound_or_conflicting_export_origin", "export_origin_evidence": sorted(set(evidence))}
    if not evidence:
        return {**result, "scope_status": "needs_review", "scope_reason": "Colombia_and_exports_but_origin_not_resolved"}
    if "prohibir el ingreso de mercancias" in normal:
        return {**result, "scope_status": "needs_review", "scope_reason": "goods_reference_is_inbound_policy_context",
                "export_origin_evidence": sorted(set(evidence))}
    if result["service_evidence"]:
        return {**result, "scope_status": "needs_review" if result["goods_evidence"] else "excluded",
                "scope_reason": "mixed_goods_and_services_headline" if result["goods_evidence"] else "services_outside_scope",
                "export_origin_evidence": sorted(set(evidence))}
    if not result["goods_evidence"]:
        return {**result, "scope_status": "needs_review", "scope_reason": "goods_not_explicit_in_headline",
                "export_origin_evidence": sorted(set(evidence))}
    return {**result, "scope_status": "included", "scope_reason": "headline_links_goods_exports_to_Colombian_origin",
            "export_origin_evidence": sorted(set(evidence))}


def analyze(text):
    themes, sectors, partners = tag(text, THEMES), tag(text, SECTORS), tag(text, PARTNERS)
    scope = export_scope(text)
    return {"title_clean": clean_text(text), "title_normalized": normalize(text),
            "relevant": scope["scope_status"] == "included", **scope,
            "themes": list(themes), "sectors": list(sectors), "partners": list(partners),
            "tag_evidence": {"themes": themes, "sectors": sectors, "partners": partners}, **sentiment(text)}
