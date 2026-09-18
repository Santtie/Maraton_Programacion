"""Suite de pruebas automatizadas del pipeline RAG (reto extra E6).

No depende de red, de Ollama ni de descargar modelos de embeddings: se inyectan un
retriever y un cliente LLM falsos para que la suite corra rápido y en cualquier máquina
("se ejecuta en vivo y pasa" sin depender de servicios externos durante la demo).
"""
from django.test import SimpleTestCase

from apps.rag.services import domain_guard, prompts
from apps.rag.services.pipeline import RAGPipeline


class FakeRetriever:
    def __init__(self, citations: list[dict]):
        self._citations = citations

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        return self._citations


class FakeLLMClient:
    def __init__(self, response: str = "respuesta simulada"):
        self.response = response
        self.calls = 0

    def generate(self, system: str, user_message: str) -> str:
        self.calls += 1
        return self.response

    def generate_stream(self, system: str, user_message: str):
        self.calls += 1
        for word in self.response.split(" "):
            yield word + " "


class DomainGuardTests(SimpleTestCase):
    def test_keyword_match_is_in_domain(self):
        self.assertTrue(domain_guard.matches_domain_keywords("¿Cómo pido la rectificación de mis datos personales?"))

    def test_unrelated_query_no_keyword_match(self):
        self.assertFalse(domain_guard.matches_domain_keywords("me estafaron comprando un carro usado"))

    def test_gibberish_with_low_score_is_noise(self):
        # Caso real observado: texto sin sentido obtiene score de similitud muy bajo (~0.2),
        # muy por debajo de cualquier consulta (incluso fuera de dominio) con contenido real.
        citations = [{"score": 0.2}, {"score": 0.15}]
        self.assertTrue(domain_guard.is_probably_noise("asdkjasd 12312 ???", citations))

    def test_coherent_out_of_domain_query_is_not_flagged_as_noise(self):
        # Importante: aunque esté fuera de dominio, una consulta coherente en español NO debe
        # tratarse como "ruido" (score de similitud moderado observado empíricamente ~0.4-0.5
        # incluso para temas no jurídicos por el pequeño tamaño/homogeneidad del corpus). Debe
        # llegar al LLM, que es quien decide dominio siguiendo el system prompt.
        citations = [{"score": 0.49}]
        self.assertFalse(domain_guard.is_probably_noise("me estafaron comprando un carro usado", citations))

    def test_keyword_match_overrides_low_score(self):
        citations = [{"score": 0.1}]
        self.assertFalse(domain_guard.is_probably_noise("quiero pedir la revocatoria de mi autorización", citations))


class RAGPipelineTests(SimpleTestCase):
    def test_empty_query_returns_prompt_without_calling_llm(self):
        llm = FakeLLMClient()
        pipeline = RAGPipeline(retriever=FakeRetriever([]), llm_client=llm)

        result = pipeline.answer("   ")

        self.assertTrue(result.empty_input)
        self.assertEqual(result.answer, prompts.EMPTY_INPUT_MESSAGE)
        self.assertEqual(llm.calls, 0)

    def test_noise_query_is_declared_without_calling_llm(self):
        llm = FakeLLMClient()
        noise_citations = [{"norma": "x", "articulo": "y", "texto": "...", "score": 0.1}]
        pipeline = RAGPipeline(retriever=FakeRetriever(noise_citations), llm_client=llm)

        result = pipeline.answer("asdkjasd 12312 ???")

        self.assertTrue(result.out_of_domain)
        self.assertEqual(result.answer, prompts.OUT_OF_DOMAIN_MESSAGE)
        self.assertEqual(result.citations, [])
        self.assertEqual(llm.calls, 0)

    def test_coherent_out_of_domain_query_is_declared_via_llm_response(self):
        # El LLM (siguiendo la regla 1 del system prompt) devuelve el texto exacto de
        # OUT_OF_DOMAIN_MESSAGE; el pipeline debe detectarlo y limpiar las citas aunque la
        # recuperación haya devuelto fragmentos con score moderado.
        llm = FakeLLMClient(response=prompts.OUT_OF_DOMAIN_MESSAGE)
        citations = [{"norma": "Ley 1581 de 2012", "articulo": "Artículo 16", "texto": "...", "score": 0.49}]
        pipeline = RAGPipeline(retriever=FakeRetriever(citations), llm_client=llm)

        result = pipeline.answer("me estafaron comprando un carro usado")

        self.assertTrue(result.out_of_domain)
        self.assertEqual(result.citations, [])
        self.assertEqual(llm.calls, 1)

    def test_in_domain_query_calls_llm_and_returns_citations(self):
        llm = FakeLLMClient(response="Debes presentar un reclamo en 15 días hábiles.")
        citations = [
            {
                "norma": "Ley 1581 de 2012",
                "articulo": "Artículo 15",
                "fuente": "Ley 1581 de 2012",
                "url": "https://example.com",
                "texto": "El término máximo para atender el reclamo será de quince (15) días hábiles.",
                "score": 0.87,
            }
        ]
        pipeline = RAGPipeline(retriever=FakeRetriever(citations), llm_client=llm)

        result = pipeline.answer("Quiero pedir la rectificación de un dato desactualizado en mi banco")

        self.assertFalse(result.out_of_domain)
        self.assertEqual(result.answer, llm.response)
        self.assertEqual(result.citations, citations)
        self.assertEqual(llm.calls, 1)

    def test_stream_answer_yields_tokens_then_done_event(self):
        llm = FakeLLMClient(response="hola mundo")
        pipeline = RAGPipeline(retriever=FakeRetriever([{"score": 0.9, "norma": "x", "articulo": "y", "texto": "z"}]), llm_client=llm)

        events = list(pipeline.stream_answer("consulta sobre habeas data"))

        self.assertGreaterEqual(len(events), 2)
        self.assertTrue(all(e["type"] == "token" for e in events[:-1]))
        self.assertEqual(events[-1]["type"], "done")
        self.assertFalse(events[-1]["out_of_domain"])

    def test_stream_answer_detects_out_of_domain_after_full_text(self):
        llm = FakeLLMClient(response=prompts.OUT_OF_DOMAIN_MESSAGE)
        citations = [{"score": 0.49, "norma": "x", "articulo": "y", "texto": "z"}]
        pipeline = RAGPipeline(retriever=FakeRetriever(citations), llm_client=llm)

        events = list(pipeline.stream_answer("me estafaron comprando un carro usado"))

        done_event = events[-1]
        self.assertEqual(done_event["type"], "done")
        self.assertTrue(done_event["out_of_domain"])
        self.assertEqual(done_event["citations"], [])
