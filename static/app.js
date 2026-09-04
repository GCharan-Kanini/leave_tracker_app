const errorElement = document.getElementById("error");

function showError(message) {
  errorElement.textContent = message || "";
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      if (data.detail) {
        detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch (_error) {
      // Ignore parse errors and keep default.
    }
    throw new Error(detail);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function employeeIdValue() {
  return Number(document.getElementById("employee-id").value || 0);
}

function managerIdValue() {
  return Number(document.getElementById("manager-id").value || 0);
}

function adminIdValue() {
  return Number(document.getElementById("admin-id").value || 0);
}

async function loadEmployeeView() {
  const employeeId = employeeIdValue();
  if (!employeeId) {
    return;
  }
  const balance = await apiFetch(`/api/employees/${employeeId}/balance`);
  document.getElementById("balance-card").textContent = JSON.stringify(balance);

  const history = await apiFetch(`/api/leaves/myrequests?employee_id=${employeeId}`);
  const table = document.getElementById("history-table");
  table.innerHTML = `<tr><th>ID</th><th>Type</th><th>Status</th><th>Days</th><th>Action</th></tr>`;
  history.forEach((request) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${request.request_id}</td><td>${request.leave_type}</td><td>${request.status}</td><td>${request.working_days}</td><td><button id="cancel-${request.request_id}" data-id="${request.request_id}">Cancel</button></td>`;
    table.appendChild(row);
  });

  table.querySelectorAll("button[data-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await apiFetch(`/api/leaves/${button.dataset.id}?employee_id=${employeeId}`, {
          method: "DELETE",
        });
        await refreshAll();
      } catch (error) {
        showError(error.message);
      }
    });
  });
}

async function submitLeaveApplication(event) {
  event.preventDefault();
  const employeeId = employeeIdValue();
  const payload = {
    employee_id: employeeId,
    leave_type: document.getElementById("leave-type").value,
    start_date: document.getElementById("start-date").value,
    end_date: document.getElementById("end-date").value,
    reason: document.getElementById("reason").value,
  };
  await apiFetch("/api/leaves/apply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await refreshAll();
}

async function loadManagerView() {
  const managerId = managerIdValue();
  if (!managerId) {
    return;
  }
  const pending = await apiFetch(`/api/managers/${managerId}/pending`);
  const pendingList = document.getElementById("pending-list");
  pendingList.innerHTML = "";
  pending.forEach((request) => {
    const item = document.createElement("li");
    item.innerHTML = `Request ${request.request_id} (${request.employee_name})
      <button id="approve-${request.request_id}" data-action="approve" data-id="${request.request_id}">Approve</button>
      <button id="reject-${request.request_id}" data-action="reject" data-id="${request.request_id}">Reject</button>`;
    pendingList.appendChild(item);
  });

  pendingList.querySelectorAll("button[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.action;
      try {
        await apiFetch(`/api/leaves/${button.dataset.id}/${action}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ manager_id: managerId }),
        });
        await refreshAll();
      } catch (error) {
        showError(error.message);
      }
    });
  });

  const month = new Date().toISOString().slice(0, 7);
  const calendar = await apiFetch(`/api/managers/${managerId}/calendar?month=${month}`);
  document.getElementById("team-calendar").textContent = JSON.stringify(calendar);
}

async function loadAdminView() {
  const adminId = adminIdValue();
  const employeeList = await apiFetch("/api/reports/summary?admin_id=" + adminId);
  document.getElementById("employee-list").textContent = JSON.stringify(employeeList);

  const leaveTypes = await apiFetch("/api/leave-types");
  const leaveTypesContainer = document.getElementById("leave-types");
  leaveTypesContainer.innerHTML = "";
  leaveTypes.forEach((entry) => {
    const wrapper = document.createElement("div");
    wrapper.innerHTML = `${entry.type}: <input data-type="${entry.type}" type="number" value="${entry.allowance}" />
      <button data-update="${entry.type}">Update</button>`;
    leaveTypesContainer.appendChild(wrapper);
  });
  leaveTypesContainer.querySelectorAll("button[data-update]").forEach((button) => {
    button.addEventListener("click", async () => {
      const leaveType = button.dataset.update;
      const allowanceInput = leaveTypesContainer.querySelector(`input[data-type="${leaveType}"]`);
      const allowance = Number(allowanceInput.value);
      try {
        await apiFetch(`/api/leave-types/${leaveType}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ allowance, admin_id: adminId }),
        });
        await refreshAll();
      } catch (error) {
        showError(error.message);
      }
    });
  });

  const summary = await apiFetch(`/api/reports/summary?admin_id=${adminId}`);
  document.getElementById("summary-report").textContent = JSON.stringify(summary);
}

async function submitEmployeeForm(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById("new-employee-name").value,
    email: document.getElementById("new-employee-email").value,
    role: document.getElementById("new-employee-role").value,
    manager_id: document.getElementById("new-employee-manager-id").value
      ? Number(document.getElementById("new-employee-manager-id").value)
      : null,
  };
  await apiFetch("/api/employees", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  await refreshAll();
}

async function refreshAll() {
  showError("");
  try {
    await loadEmployeeView();
    await loadManagerView();
    const adminId = adminIdValue();
    if (adminId) {
      await loadAdminView();
    }
  } catch (error) {
    showError(error.message);
  }
}

document.getElementById("employee-refresh").addEventListener("click", refreshAll);
document.getElementById("manager-refresh").addEventListener("click", refreshAll);
document.getElementById("admin-refresh").addEventListener("click", refreshAll);
document.getElementById("apply-form").addEventListener("submit", (event) => {
  submitLeaveApplication(event).catch((error) => showError(error.message));
});
document.getElementById("employee-form").addEventListener("submit", (event) => {
  submitEmployeeForm(event).catch((error) => showError(error.message));
});

document.getElementById("view-employee").addEventListener("click", refreshAll);
document.getElementById("view-manager").addEventListener("click", refreshAll);
document.getElementById("view-admin").addEventListener("click", refreshAll);
