"""Foundation API: no retail domain endpoints are registered yet."""
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import Settings
from app.core.exceptions import RetailOpsError
from app.core.logging import configure_logging
from app.services.database_service import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()
    logger = configure_logging(config.log_level)

    @asynccontextmanager
    async def lifespan(api: FastAPI):
        database = Database(config.database_url.get_secret_value())
        api.state.database = database
        try:
            yield
        finally:
            database.close()

    api = FastAPI(title=config.app_name, version="0.1.0", lifespan=lifespan)

    @api.middleware("http")
    async def request_metadata(request: Request, call_next):
        request.state.request_id = str(uuid4())
        try:
            response = await call_next(request)
        except Exception:
            # Never return or log raw exception text, payloads or credentials.
            response = error(request, 500, "internal_error", "An internal error occurred.")
        response.headers["X-Request-ID"] = request.state.request_id
        logger.info("request", extra={"event": "http_request", "request_id": request.state.request_id,
                                      "status_code": response.status_code})
        return response

    def error(request: Request, status: int, code: str, message: str):
        return JSONResponse(status_code=status, content={"code": code, "message": message,
                            "request_id": request.state.request_id})

    @api.exception_handler(RetailOpsError)
    async def domain_error(request: Request, exc: RetailOpsError):
        # Class-specific messages are deliberately fixed to avoid data leaks.
        messages = {404: "Requested resource was not found.", 422: "Invalid data.",
                    503: "Required component is unavailable."}
        return error(request, exc.status_code, exc.code, messages.get(exc.status_code, "An internal error occurred."))

    @api.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        return error(request, 422, "invalid_request", "Request does not match the required schema.")

    @api.get("/")
    def root():
        return {"service": config.app_name, "stage": "foundation", "docs": "/docs"}

    @api.get("/health")
    def health(request: Request):
        try:
            if not request.app.state.database.ping():
                raise RuntimeError("Database unavailable")
        except Exception:
            return error(request, 503, "database_unavailable", "Database health check failed.")
        return {"status": "ok", "database": "ok", "stage": "foundation"}

    return api


app = create_app()
