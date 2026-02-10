"""
# main.py
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from middleware import LoggingMiddleware, MetricsMiddleware
from logger.logger import LoggingSetup

app = FastAPI()

# Setup logger
logger_setup = LoggingSetup()

# Optional: Add OTEL instrumentation first
try:
    import logfire
    logfire.configure()
    logfire.instrument_fastapi(app)
except ImportError:
    pass

# Add middlewares (order matters - executed in reverse order)
# 1. Metrics middleware (outermost - measures everything)
app.add_middleware(
    MetricsMiddleware,
    skip_paths={"/health", "/metrics", "/ready"}
)

# 2. Logging middleware
app.add_middleware(
    LoggingMiddleware,
    logger_setup=logger_setup,
    skip_paths={"/health", "/metrics", "/ready"}
)

# Expose metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

"""
from .logging import LoggingMiddleware
from .metrics import MetricsMiddleware

__all__ = ["LoggingMiddleware", "MetricsMiddleware"]
