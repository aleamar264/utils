# middleware/metrics.py
import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware


class MetricsMiddleware(BaseHTTPMiddleware):
	"""Middleware for collecting Prometheus metrics on HTTP requests."""

	def __init__(
		self,
		app,
		skip_paths: set[str] | None = None,
		track_in_progress: bool = True,
	):
		"""
		Initialize the MetricsMiddleware.

		Args:
            app: The FastAPI application instance.
            skip_paths: Optional set of URL paths to skip metrics collection.
            track_in_progress: Whether to track in-progress requests.
		"""
		super().__init__(app)
		self.skip_paths = skip_paths or {"/health", "/ready"}
		self.track_in_progress = track_in_progress

		# Define metrics
		self.request_count = Counter(
			"http_requests_total",
			"Total HTTP requests",
			["method", "endpoint", "status"],
		)

		self.request_duration = Histogram(
			"http_request_duration_seconds",
			"HTTP request duration in seconds",
			["method", "endpoint"],
			buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
		)

		if self.track_in_progress:
			from prometheus_client import Gauge

			self.requests_in_progress = Gauge(
				"http_requests_in_progress",
				"HTTP requests currently being processed",
				["method", "endpoint"],
			)

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		"""Collect metrics for HTTP request/response."""
		# Skip metrics for certain paths
		if request.url.path in self.skip_paths:
			return await call_next(request)

		method = request.method
		path = request.url.path

		# Track in-progress requests
		if self.track_in_progress:
			self.requests_in_progress.labels(method=method, endpoint=path).inc()

		start = time.perf_counter()

		try:
			response = await call_next(request)
			status = response.status_code
		except Exception:
			# Track failed requests
			status = 500
			raise
		finally:
			# Record metrics
			duration = time.perf_counter() - start

			self.request_count.labels(method=method, endpoint=path, status=status).inc()

			self.request_duration.labels(method=method, endpoint=path).observe(duration)

			if self.track_in_progress:
				self.requests_in_progress.labels(method=method, endpoint=path).dec()

		return response
