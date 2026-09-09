import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

def setup_telemetry(service_name: str = "hyperroute-agent-runtime") -> trace.Tracer:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    processor = BatchSpanProcessor(
        otlp_exporter,
        schedule_delay_millis=200,
        max_export_batch_size=1
    )

    current_provider = trace.get_tracer_provider()
    if isinstance(current_provider, TracerProvider):
        current_provider.add_span_processor(processor)
        return trace.get_tracer(service_name)

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

def flush_telemetry():
    """Forces all buffered spans to export immediately over gRPC."""
    provider = trace.get_tracer_provider()
    if hasattr(provider, "force_flush"):
        provider.force_flush(timeout_millis=2000)

def get_traceparent_metadata() -> list[tuple[str, str]]:
    carrier = {}
    TraceContextTextMapPropagator().inject(carrier)
    return [(k.lower(), v) for k, v in carrier.items()]
