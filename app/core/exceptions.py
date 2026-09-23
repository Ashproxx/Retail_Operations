"""Safe public errors. Never put private details in messages."""
class RetailOpsError(Exception):
    code = "retailops_error"
    status_code = 500


class NotFoundError(RetailOpsError):
    code = "not_found"
    status_code = 404


class DataValidationError(RetailOpsError):
    code = "invalid_data"
    status_code = 422


class ComponentUnavailableError(RetailOpsError):
    code = "component_unavailable"
    status_code = 503
