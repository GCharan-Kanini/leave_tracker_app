"""FastAPI entrypoint for leave-request cancellation UI flows."""

from __future__ import annotations

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from leave_tracker_app.views import cancel_request_view, request_list_view

app = FastAPI(title="Leave Tracker App UI")


@app.get("/cancel-request/{request_id}", response_class=HTMLResponse)
def get_cancel_request(request_id: int) -> HTMLResponse:
    """Render cancellation form for a leave request.

    Args:
        request_id: Identifier of the leave request to cancel.

    Returns:
        HTML form asking for cancellation reason.
    """
    return cancel_request_view(request_id=request_id, cancellation_reason=None)


@app.post("/cancel-request/{request_id}", response_class=HTMLResponse)
def post_cancel_request(
    request_id: int,
    cancellation_reason: str = Form(default=""),
) -> HTMLResponse:
    """Process leave cancellation submission.

    Args:
        request_id: Identifier of the leave request to cancel.
        cancellation_reason: Submitted cancellation reason from the form.

    Returns:
        HTML response with validation errors or success confirmation.
    """
    return cancel_request_view(request_id=request_id, cancellation_reason=cancellation_reason)


@app.get("/leave-requests", response_class=HTMLResponse)
def leave_requests() -> HTMLResponse:
    """Render list of leave requests including cancellation reasons."""
    return request_list_view()
