import pytest

from app.nlp.nlp_pipeline import NLPPipeline


@pytest.fixture(scope="module")
def pipeline():
    return NLPPipeline()


def test_roadmap_example(pipeline):
    assert pipeline.analyze("Analise os erros Visa do terminal 1002") == {
        "intent": "analyze_error",
        "entities": {"brand": "VISA", "terminal": "1002"},
        "keywords": ["erro", "visa", "terminal"],
    }


@pytest.mark.parametrize(("query", "intent"), [
    ("Como funciona EMV?", "explain_concept"),
    ("O que é uma APDU?", "explain_concept"),
    ("Explique o erro Visa", "explain_concept"),
    ("Busque documentação ISO8583", "search_docs"),
    ("Investigue timeout no terminal 0012", "analyze_error"),
    ("Bom dia", "unknown"),
])
def test_intents(pipeline, query, intent):
    assert pipeline.analyze(query)["intent"] == intent


def test_entities_multiple_and_deduplicated(pipeline):
    result = pipeline.analyze("VISA visa Mastercard terminal 0012 terminal 1002")
    assert result["entities"] == {"brand": ["VISA", "MASTERCARD"],
                                  "terminal": ["0012", "1002"]}


def test_boundaries_and_details(pipeline):
    result = pipeline.analyze("Avisar terminal abc", details=True)
    assert result["entities"] == {}
    assert result["tokens"] == ["Avisar", "terminal", "abc"]
    assert pipeline.analyze("American Express")["entities"]["brand"] == "AMEX"
    assert "documentacao" in pipeline.analyze("Documentação")["keywords"]


@pytest.mark.parametrize("text", ["", "   ", "a" * 10001])
def test_invalid_query(pipeline, text):
    with pytest.raises(ValueError):
        pipeline.analyze(text)
