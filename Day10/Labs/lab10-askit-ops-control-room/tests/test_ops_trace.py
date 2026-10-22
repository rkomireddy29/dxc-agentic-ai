import unittest

import model_factory
import ops_agent
import ops_trace


class FakeObservation:
    def __init__(self, trace_id="trace-123"):
        self.trace_id = trace_id
        self.updates = []

    def update(self, **kwargs):
        self.updates.append(kwargs)


class FakeObservationContext:
    def __init__(self, observation):
        self.observation = observation
        self.exit_args = None

    def __enter__(self):
        return self.observation

    def __exit__(self, exc_type, exc_value, traceback):
        self.exit_args = (exc_type, exc_value, traceback)


class FakeLangfuse:
    def __init__(self):
        self.observations = []
        self.contexts = []
        self.flush_count = 0

    def start_as_current_observation(self, **kwargs):
        observation = FakeObservation()
        context = FakeObservationContext(observation)
        self.observations.append((kwargs, observation))
        self.contexts.append(context)
        return context

    def flush(self):
        self.flush_count += 1

    def get_trace_url(self, trace_id):
        return f"https://langfuse.test/trace/{trace_id}"


class LangfuseTracingTests(unittest.TestCase):
    def test_trace_masks_sensitive_data_and_records_generation_usage(self):
        langfuse = FakeLangfuse()
        tracer = ops_trace.Tracer(
            "askit-run",
            model="example-model",
            provider="offline",
            price_key="offline",
            lf=langfuse,
        )

        with tracer.run("Reset EMP-1001 ticket TKT-0004 for pat@example.com"):
            with tracer.span(
                "llm",
                "model call 1",
                input=[{"role": "user", "content": "EMP-1001 pat@example.com"}],
            ) as span:
                span.update(tokens_in=12, tokens_out=3, cost_usd=0.25)
                span["output"] = "TKT-0004"
            tracer.trace["answer"] = "Completed TKT-0004"

        root_kwargs, root_observation = langfuse.observations[0]
        generation_kwargs, generation_observation = langfuse.observations[1]
        self.assertEqual(root_kwargs["as_type"], "agent")
        self.assertEqual(root_kwargs["input"], "Reset [REDACTED_EMPLOYEE_ID] ticket [REDACTED_TICKET_ID] for [REDACTED_EMAIL]")
        self.assertEqual(generation_kwargs["as_type"], "generation")
        self.assertEqual(generation_kwargs["name"], "askit-model-call")
        self.assertIn("[REDACTED_EMPLOYEE_ID]", generation_kwargs["input"][0]["content"])
        self.assertEqual(generation_observation.updates[0]["usage_details"], {"input": 12, "output": 3})
        self.assertEqual(generation_observation.updates[0]["cost_details"], {"total": 0.25})
        self.assertEqual(generation_observation.updates[0]["output"], "[REDACTED_TICKET_ID]")
        self.assertEqual(root_observation.updates[0]["output"], "Completed [REDACTED_TICKET_ID]")
        self.assertEqual(tracer.trace["spans"][0]["output"], "TKT-0004")
        self.assertEqual(langfuse.flush_count, 1)
        self.assertEqual(tracer.trace["langfuse_url"], "https://langfuse.test/trace/trace-123")

    def test_langfuse_start_failure_does_not_break_the_agent(self):
        class BrokenLangfuse:
            def start_as_current_observation(self, **kwargs):
                raise RuntimeError("unavailable")

        tracer = ops_trace.Tracer("askit-run", lf=BrokenLangfuse())
        with self.assertLogs(ops_trace.logger, level="WARNING"):
            with tracer.run("question"):
                with tracer.span("tool", "search_kb", input={"query": "question"}) as span:
                    span["output"] = "result"

        self.assertEqual(tracer.trace["spans"][0]["output"], "result")
        self.assertEqual(tracer.trace["tool_calls"], 1)

    def test_offline_agent_records_each_generation_and_retriever(self):
        langfuse = FakeLangfuse()
        tracer = ops_trace.Tracer(
            "askit-run",
            model="offline-standin",
            provider="offline",
            price_key="offline",
            lf=langfuse,
        )

        answer = ops_agent.run_agent(
            "My VPN shows error 809 - what should I try?",
            model_factory.OfflineChatModel(),
            "offline",
            tracer,
        )

        observations = [kwargs for kwargs, _ in langfuse.observations]
        self.assertTrue(answer)
        self.assertEqual(observations[0]["as_type"], "agent")
        self.assertEqual(
            [item["as_type"] for item in observations[1:]],
            ["generation", "retriever", "generation"],
        )
        self.assertEqual(
            [item["name"] for item in observations[1:]],
            ["askit-model-call", "search_kb", "askit-model-call"],
        )
        self.assertEqual(observations[1]["input"][0]["role"], "system")
        self.assertEqual(observations[1]["input"][1]["role"], "user")
        self.assertTrue(
            any(item["role"] == "tool" for item in observations[3]["input"])
        )


if __name__ == "__main__":
    unittest.main()
