"""Transparent article-screening proposals; human review remains a distinct step."""
import csv
from pathlib import Path
import re
import unicodedata

REFERENCE = Path(__file__).resolve().parents[1] / "reference"
SCREENING_METHOD = "export_focus_and_document_cues_v3"
with (REFERENCE / "activities.csv").open(encoding="utf8", newline="") as stream:
    ACTIVITIES = [row["activity"] for row in csv.DictReader(stream)]


def normalized(text):
    text = re.sub(r"\s+\|\s+El Colombiano\s*$", "", text, flags=re.I)
    return " ".join(re.findall(r"[a-z0-9]+", "".join(c for c in unicodedata.normalize("NFKD", text.casefold()) if not unicodedata.combining(c))))


GOODS = ["bienes", "mercancias", "productos", "cafe", "flores", "banano", "aguacate", "cacao", "frutas", "lima", "limon",
         "carne", "ganado", "lacteos", "huevos", "agro", "agropecuario", "manufacturas", "manufactura", "textil", "calzado",
         "petroleo", "carbon", "oro", "combustibles", "minerales", "energia", "electricidad", "vehiculos", "cosmetica"]
ACTIVITY_CUES = {
    "Agriculture": ["cafe", "flores", "banano", "aguacate", "cacao", "ganado", "agropecuario", "agropecuarias", "agricola", "frutas", "lima", "limon"],
    "Manufacturing": ["manufacturas", "manufactura", "textiles", "textil", "confecciones", "calzado", "vehiculos", "cosmetica", "plastico", "quimicos"],
    "Mining": ["petroleo", "carbon", "oro", "combustibles", "minerales", "coque", "hidrocarburos"],
    "Public Services": ["energia electrica", "electricidad"],
    "Transport": ["flete", "fletes", "puertos", "transporte maritimo", "logistica"],
}


def matches(text, terms):
    value = " " + normalized(text) + " "
    return [term for term in terms if " " + term + " " in value]


def propose(title, body):
    headline, text = normalized(title), normalized(title+" "+body)
    goods = matches(text, GOODS)
    scope, reason = "include", "Colombian_exports_and_goods_cues_in_article"
    if not re.search(r"\bexport\w*\b", text) or not re.search(r"\b(colombia|colombian[oa]s?)\b", text):
        scope, reason = "exclude", "no_explicit_Colombian_exports_context"
    elif re.search(r"\b(cocaina|narcotrafico|futbolistas|jugadores)\b", headline):
        scope, reason = "exclude", "outside_merchandise_scope"
    elif matches(headline, ["las noticias del", "resumen de noticias", "resumen del dia"]):
        scope, reason = "review", "multi_topic_news_roundup_requires_review"
    elif re.search(r"\bexport\w*(?:\s+\w+){0,8}\s+(?:a|hacia|para)\s+colombia\b", headline):
        scope, reason = "review", "possible_inbound_exports_to_Colombia"
    elif not re.search(r"\bcolombia\b|\bcolombian[oa]s?\b", headline) and re.search(
            r"\bexportaciones (?:de |desde )(?:china|estados unidos|mexico|peru|chile|brasil|ecuador|argentina|venezuela|alemania|espana|rusia|japon)\b"
            r"|\bexportaciones (?:chinas|estadounidenses|mexicanas|peruanas|chilenas|brasilenas|ecuatorianas|argentinas)\b", headline):
        scope, reason = "review", "foreign_export_origin_requires_Colombian_relevance_review"
    elif matches(headline, ["servicios", "software", "turismo", "bpo", "ciberseguridad"]):
        scope, reason = "review" if matches(headline, GOODS) else "exclude", "services_or_mixed_headline"
    elif not goods:
        scope, reason = "review", "merchandise_not_resolved"
    elif not re.search(r"\bexport\w*\b", headline):
        scope, reason = "review", "headline_export_focus_unresolved"
    elif re.search(r"\b(importaciones|importacion|importar)\b", headline):
        scope, reason = "review", "mixed_trade_flow_headline_requires_review"
    evidence = {activity: matches(text, terms) for activity, terms in ACTIVITY_CUES.items()}
    evidence = {activity: terms for activity, terms in evidence.items() if terms}
    activity = next(iter(evidence)) if len(evidence) == 1 else "Global Context" if evidence else "Other Activity"
    report_cues = matches(headline, ["informe de exportaciones", "informe exportaciones", "informe de comercio exterior",
                                   "informe comercio exterior", "balance de exportaciones"])
    statistical_source = matches(text, ["dane", "dian", "cifras oficiales", "estadisticas de exportaciones"])
    retrospective = bool(re.search(r"\b(crecieron|cayeron|aumentaron|disminuyeron|registraron|alcanzaron|sumaron|fueron|crecen|caen|aumentan|disminuyen|registran|alcanzan|suman)\b", headline))
    period_cue = bool(re.search(r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre|trimestre|semestre|acumulado)\b", headline))
    magnitude_cue = bool(re.search(r"\b\d+\b|\bmillones\b|\bmiles\b", headline))
    event_cues = matches(headline, ["expectativas", "perspectivas", "espera", "esperan", "exportara", "exportaran",
        "exportaria", "exportarian", "reactivara", "reactivaran", "restriccion", "restricciones", "arancel", "aranceles",
        "prohibicion", "acuerdo", "acuerdos", "pedidos", "suspension", "suspende", "retomara", "retomaran"])
    reporting = bool(report_cues or (statistical_source and (retrospective or period_cue and magnitude_cue)))
    role = "mixed_cues" if reporting and event_cues else "statistical_reporting_candidate" if reporting else "event_or_expectation_candidate" if event_cues else "unresolved"
    return {"scope_proposal": scope, "scope_reason": reason, "goods_evidence": goods,
            "screening_method": SCREENING_METHOD, "document_role_proposal": role,
            "document_role_evidence": {"report_title_cues": report_cues, "statistical_source_cues": statistical_source,
                                       "retrospective_title_verb": retrospective, "statistical_period_in_title": period_cue,
                                       "magnitude_in_title": magnitude_cue, "event_title_cues": event_cues},
            "activity_proposal": activity, "activity_evidence": evidence,
            "classification_status": "automatic_proposal_pending_human_review", "topic": "exports"}
