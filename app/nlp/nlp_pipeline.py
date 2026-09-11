"""NLP em português com tokenização spaCy e regras explícitas de domínio."""
import argparse
import json
import unicodedata

import spacy


def normalize(text: str) -> str:
    """Normalização para comparação; não substitui lematização linguística."""
    return "".join(
        char for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )


FORMS = {
    "erros": "erro", "falhas": "falha", "terminais": "terminal",
    "documentos": "documento", "logs": "log", "timeouts": "timeout",
}
ACTIONS = {
    "analise", "analisar", "investigue", "investigar", "diagnostique", "diagnosticar",
    "explique", "explicar", "busque", "buscar", "procure", "procurar",
    "encontre", "encontrar", "pesquise", "pesquisar",
}
ERROR_WORDS = {"erro", "falha", "timeout", "problema"}
EXPLAIN_WORDS = {"explique", "explicar", "como", "significa"}
SEARCH_WORDS = {"busque", "buscar", "procure", "procurar", "encontre", "encontrar",
                "pesquise", "pesquisar", "documentacao", "documento"}


class NLPPipeline:
    """Baseline determinístico; não carrega modelo estatístico nem consulta LLM."""
    def __init__(self):
        self.nlp = spacy.blank("pt")
        ruler = self.nlp.add_pipe("entity_ruler")
        patterns = [
            {"label": "BRAND", "pattern": [{"LOWER": brand}]}
            for brand in ("visa", "mastercard", "elo", "amex")
        ]
        patterns += [
            {"label": "BRAND", "pattern": [{"LOWER": "american"}, {"LOWER": "express"}]},
            {"label": "TERMINAL", "pattern": [
                {"LOWER": "terminal"}, {"TEXT": {"REGEX": r"^[0-9]+$"}}
            ]},
        ]
        ruler.add_patterns(patterns)

    def analyze(self, text: str, *, details: bool = False) -> dict:
        if not text.strip():
            raise ValueError("A consulta não pode estar vazia.")
        if len(text) > 10000:
            raise ValueError("A consulta deve ter no máximo 10000 caracteres.")
        doc = self.nlp(text)
        words = [FORMS.get(normalize(t.text), normalize(t.text)) for t in doc
                 if not t.is_space and not t.is_punct]
        # Prioridade explícita: explicação → erro → busca → desconhecido.
        # Não interpreta negações ou múltiplas intenções.
        if EXPLAIN_WORDS.intersection(words) or {"o", "que", "e"}.issubset(words):
            intent = "explain_concept"
        elif ERROR_WORDS.intersection(words):
            intent = "analyze_error"
        elif SEARCH_WORDS.intersection(words):
            intent = "search_docs"
        else:
            intent = "unknown"

        entities: dict[str, str | list[str]] = {}
        for ent in doc.ents:
            key = "brand" if ent.label_ == "BRAND" else "terminal"
            value = ent.text.upper() if key == "brand" else ent[-1].text
            if value == "AMERICAN EXPRESS":
                value = "AMEX"
            if key not in entities:
                entities[key] = value
            elif value != entities[key]:
                previous = entities[key]
                values = previous if isinstance(previous, list) else [previous]
                if value not in values:
                    entities[key] = [*values, value]

        keywords = []
        for token in doc:
            word = FORMS.get(normalize(token.text), normalize(token.text))
            if (token.is_space or token.is_punct or token.is_stop or token.like_num
                    or word in ACTIONS):
                continue
            if word not in keywords:
                keywords.append(word)

        result = {"intent": intent, "entities": entities, "keywords": keywords}
        if details:
            result["tokens"] = [token.text for token in doc if not token.is_space]
            result["normalized_tokens"] = words
            result["method"] = "spacy_tokenizer_and_rules"
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Fase 2: NLP local sem LLM.")
    parser.add_argument("text", help="Consulta entre aspas.")
    parser.add_argument("--details", action="store_true", help="Mostra tokens e normalização.")
    args = parser.parse_args()
    try:
        result = NLPPipeline().analyze(args.text, details=args.details)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
