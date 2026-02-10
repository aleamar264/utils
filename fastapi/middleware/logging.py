import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from logger.logger import LoggingSetup
from starlette.middleware.base import BaseHTTPMiddleware

try:
	from opentelemetry import trace

	OTEL_AVAILABLE = True
except ImportError:
	OTEL_AVAILABLE = False


class LoggingMiddleware(BaseHTTPMiddleware):
	"""
	Module for HTTP request/response logging middleware.

	This module provides a FastAPI middleware that logs incoming requests and outgoing responses
	with detailed information for debugging and monitoring purposes.
	"""

	def __init__(
		self,
		app,
		logger_setup: LoggingSetup,
		skip_paths: set[str] | None = None,
	):
		"""
		Middleware for logging HTTP requests and responses with detailed tracing information.

		This middleware intercepts all HTTP requests and responses, generating a unique request ID
		for tracing, logging request details, handling exceptions, and measuring request processing time.
		Certain paths (health checks, metrics) can be skipped to reduce noise in logs.

		Attributes:
            logger: Logger instance configured via LoggingSetup.
            skip_paths: Set of URL paths to exclude from logging.

		Initialize the LoggingMiddleware.

		Args:
            app: The FastAPI application instance.
            logger_setup: LoggingSetup instance for configuring the logger.
            skip_paths: Optional set of URL paths to skip logging. Defaults to
                {"/health", "/metrics", "/ready"} if not provided.
		"""
		super().__init__(app)
		self.logger = logger_setup.get_logger(__name__)
		# Skip health checks and metrics endpoints
		self.skip_paths = skip_paths or {"/health", "/metrics", "/ready"}

	async def dispatch(self, request: Request, call_next: Callable) -> Response:
		"""Process incoming HTTP request and outgoing response with logging.

		Generates a unique request ID, logs request details, handles any exceptions,
		measures request processing time, and logs response information. Automatically
		adds the request ID to response headers for end-to-end request tracing.

		Args:
            request: The incoming HTTP request object.
            call_next: Callable to process the request and get the response.

		Returns:
            Response: The HTTP response object with request ID header added.

		Raises:
            Exception: Re-raises any exception that occurs during request processing
                after logging it as an error.
		"""
		if request.url.path in self.skip_paths:
			return await call_next(request)

		log_extra = self._get_trace_context(request=request)
		log_extra.update(
			{
				"method": request.method,
				"path": request.url.path,
			}
		)

		start = time.perf_counter()

		try:
			response = await call_next(request)
			process_time = time.perf_counter() - start

			log_level = (
				self.logger.error
				if response.status_code >= 500
				else self.logger.warning
				if response.status_code >= 400
				else self.logger.info
			)

			log_level(
				"Request processed",
				extra={
					**log_extra,
					"status_code": response.status_code,
					"duration_ms": round(process_time * 1000, 2),
				},
			)

			# Add trace headers
			self._add_trace_headers(response)

			return response

		except Exception as e:
			process_time = time.perf_counter() - start

			self.logger.error(
				"Request failed",
				extra={
					**log_extra,
					"error": str(e),
					"error_type": type(e).__name__,
					"duration_ms": round(process_time * 1000, 2),
				},
				exc_info=True,
			)
			raise

	def _get_trace_context(self, request: Request) -> dict:
		"""Extract trace context from current OTEL span"""
		if not OTEL_AVAILABLE:
			request_id = str(uuid.uuid4())
			request.state.request_id = request_id
			return {
				"request_id": request_id,
				"url": str(request.url),
				"client_host": request.client.host if request.client else None,
				"user_agent": request.headers.get("user-agent"),
			}

		span = trace.get_current_span()
		span_context = span.get_span_context()

		if not span_context.is_valid:
			request_id = str(uuid.uuid4())
			request.state.request_id = request_id
			return {
				"request_id": request_id,
				"url": str(request.url),
				"client_host": request.client.host if request.client else None,
				"user_agent": request.headers.get("user-agent"),
			}

		return {
			"trace_id": format(span_context.trace_id, "032x"),
			"span_id": format(span_context.span_id, "016x"),
			"url": str(request.url),
			"client_host": request.client.host if request.client else None,
			"user_agent": request.headers.get("user-agent"),
		}

	def _add_trace_headers(self, response: Response) -> None:
		"""Add trace/request ID headers to response."""
		if OTEL_AVAILABLE:
			span = trace.get_current_span()
			span_context = span.get_span_context()
			if span_context.is_valid:
				response.headers["X-Trace-ID"] = format(span_context.trace_id, "032x")
				response.headers["X-Span-ID"] = format(span_context.span_id, "016x")
