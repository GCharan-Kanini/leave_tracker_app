"""View functions for leave-request cancellation and listing pages."""

from __future__ import annotations

from html import escape
from pathlib import Path

from fastapi.responses import HTMLResponse

from leave_tracker_app.forms import CancelRequestForm
from leave_tracker_app.models import LeaveRequest

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "leave_tracker_app"


def _load_template(name: str) -> str:
    """Load an HTML template from disk.

    Args:
        name: Template filename in the leave_tracker_app template directory.

    Returns:
        Template text content.
    """
    return (_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def cancel_request_view(request_id: int, cancellation_reason: str | None = None) -> HTMLResponse:
    """Render or process cancellation for a leave request.

    Args:
        request_id: Target leave request identifier.
        cancellation_reason: Submitted reason; when None, render prompt form.

    Returns:
        HTML response containing either form or cancellation confirmation.
    """
    leave_request = LeaveRequest.get(request_id)
    template = _load_template("cancel_request.html")

    if cancellation_reason is None:
        return HTMLResponse(
            template.format(
                request_id=request_id,
                status=escape(leave_request.status),
                error_message="",
                cancellation_reason_value="",
            ),
            status_code=200,
        )

    form = CancelRequestForm(cancellation_reason=cancellation_reason)
    try:
        cleaned_reason = form.cleaned_reason()
    except ValueError as exc:
        return HTMLResponse(
            template.format(
                request_id=request_id,
                status=escape(leave_request.status),
                error_message=f"<p class=\"error\">{escape(str(exc))}</p>",
                cancellation_reason_value=escape(cancellation_reason),
            ),
            status_code=400,
        )

    leave_request.status = "cancelled"
    leave_request.cancellation_reason = cleaned_reason
    return HTMLResponse(
        (
            f"<html><body><h1>Cancel Request</h1><p>Request {request_id} cancelled.</p>"
            f"<p>Reason: {escape(cleaned_reason)}</p></body></html>"
        ),
        status_code=200,
    )


def request_list_view() -> HTMLResponse:
    """Render leave-request list with cancellation reason for cancelled requests."""
    rows: list[str] = []
    for request in LeaveRequest.list_all():
        reason = ""
        if request.status.lower() == "cancelled" and request.cancellation_reason:
            reason = escape(request.cancellation_reason)
        rows.append(
            "<tr>"
            f"<td>{request.id}</td>"
            f"<td>{request.employee_id}</td>"
            f"<td>{escape(request.start_date)}</td>"
            f"<td>{escape(request.end_date)}</td>"
            f"<td>{escape(request.status)}</td>"
            f"<td>{reason}</td>"
            "</tr>"
        )

    template = _load_template("request_list.html")
    return HTMLResponse(template.format(rows="".join(rows)), status_code=200)
