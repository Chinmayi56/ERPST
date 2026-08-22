import React, { useEffect, useMemo, useState } from "react";
import {
  listRecords, getModuleStats, createRecord, updateRecord, deleteRecord,
  updateStatus, updateLeaveStatus, uploadDocument, getEmployeeOptions,
  getClientOptions, getServiceOptions, getProjectOptions,
} from "../api/erp";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";

// Fields whose type is one of these keys are rendered as a dropdown backed by
// live data from another ERP module (clients/employees/services/projects),
// instead of a free-text box. Picking an option sets BOTH the *_id field
// (this field's own key) and the paired *_name field in one go, so records
// stay genuinely connected to the client/employee/project/service they
// reference instead of relying on the user to type a matching name by hand.
const OPTION_SOURCES = {
  client_select: { list: "clients", idKey: "client_id", nameKey: "client_name", labelFn: c => c.company_name || c.name || c.client_id },
  service_select: { list: "services", idKey: "service_id", nameKey: "service_name", labelFn: s => s.name || s.service_id },
  employee_select: { list: "employees", idKey: "employee_id", nameKey: "employee_name", labelFn: e => e.full_name || e.email || e.employee_id },
  project_select: { list: "projects", idKey: "project_id", nameKey: "project_name", labelFn: p => p.name || p.project_id },
};

const CONFIG = {
  clients: {
    title: "Client Management", subtitle: "Manage customers, contacts and account status.",
    statuses: ["ACTIVE", "INACTIVE"],
    fields: [
      ["company_name", "Company Name", "text", true], ["name", "Client / Contact Name", "text", true],
      ["contact_person", "Contact Person", "text"], ["email", "Email", "email"], ["phone", "Phone", "text"],
      ["address", "Address", "textarea"], ["status", "Status", "select"],
    ],
    columns: ["company_name", "contact_person", "email", "phone", "status"],
  },
  projects: {
    title: "Project Management", subtitle: "Track projects, clients, teams, budgets and delivery status.",
    statuses: ["PLANNED", "ACTIVE", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELLED"],
    fields: [
      ["name", "Project Name", "text", true], ["project_code", "Project Code", "text"],
      ["client_id", "Client", "client_select", true],
      ["priority", "Priority", "select", false, ["LOW", "MEDIUM", "HIGH", "URGENT"]],
      ["start_date", "Start Date", "date"], ["end_date", "End Date", "date"], ["budget", "Budget", "number"],
      ["assigned_employee_ids", "Assigned Employees", "employee_multiselect"],
      ["status", "Status", "select"], ["description", "Description", "textarea"],
    ], columns: ["name", "client_name", "priority", "start_date", "end_date", "status"],
  },
  tasks: {
    title: "Task Management", subtitle: "Assign and track tasks across projects, employees, priority and progress.",
    statuses: ["TODO", "IN_PROGRESS", "REVIEW", "COMPLETED", "BLOCKED"],
    fields: [
      ["title", "Task Title", "text", true],
      ["project_id", "Project", "project_select"],
      ["employee_id", "Assigned Employee", "employee_select"],
      ["priority", "Priority", "select", false, ["LOW", "MEDIUM", "HIGH", "URGENT"]],
      ["due_date", "Due Date", "date"],
      ["progress", "Progress % (0-100)", "number"],
      ["status", "Status", "select"],
      ["description", "Description", "textarea"],
    ], columns: ["title", "project_name", "employee_name", "priority", "due_date", "progress", "status"],
  },
  leaves: {
    title: "Leave Requests", subtitle: "Review employee leave requests and approval history.",
    statuses: ["PENDING", "APPROVED", "REJECTED"],
    fields: [
      ["employee_id", "Employee", "employee_select", true],
      ["leave_type", "Leave Type", "select", true, ["CASUAL", "SICK", "ANNUAL", "UNPAID", "OTHER"]],
      ["start_date", "Start Date", "date", true], ["end_date", "End Date", "date", true], ["reason", "Reason", "textarea", true], ["status", "Status", "select"],
    ], columns: ["employee_name", "leave_type", "start_date", "end_date", "reason", "status"],
  },
  attendance: {
    title: "Attendance Management", subtitle: "Monitor employee attendance by date and status. Check-in/out is also recorded automatically when an employee logs in or out.",
    statuses: ["PRESENT", "ABSENT", "LATE", "HALF_DAY", "LEAVE"],
    fields: [
      ["employee_id", "Employee", "employee_select", true], ["date", "Date", "date", true],
      ["status", "Attendance Status", "select", true], ["check_in", "Check In", "time"], ["check_out", "Check Out", "time"], ["hours", "Hours", "number"], ["notes", "Notes", "textarea"],
    ], columns: ["employee_name", "date", "status", "check_in", "check_out", "hours"],
  },
  services: {
    title: "Services", subtitle: "Manage the services offered to clients.", statuses: ["ACTIVE", "INACTIVE"],
    fields: [["name", "Service Name", "text", true], ["category", "Category", "text"], ["description", "Description", "textarea"], ["price", "Price", "number"], ["duration", "Duration", "text"], ["status", "Status", "select"]],
    columns: ["name", "category", "price", "duration", "status"],
  },
  bookings: {
    title: "Services / Bookings", subtitle: "Schedule and manage client service bookings.", statuses: ["PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"],
    fields: [
      ["client_id", "Client", "client_select", true], ["service_id", "Service", "service_select", true],
      ["employee_id", "Assigned Employee", "employee_select"],
      ["booking_date", "Booking Date", "date", true], ["booking_time", "Time", "time"], ["status", "Status", "select"], ["notes", "Notes", "textarea"],
    ],
    columns: ["client_name", "service_name", "employee_name", "booking_date", "booking_time", "status"],
  },
  documents: {
    title: "Documents Management", subtitle: "Store documents against employees, clients or projects.", statuses: ["ACTIVE", "ARCHIVED"],
    fields: [["name", "Document Name", "text", true], ["type", "Document Type", "text", true], ["owner_type", "Owner Type", "select", true, ["EMPLOYEE", "CLIENT", "PROJECT", "OTHER"]], ["owner_id", "Owner ID", "text"], ["owner_name", "Owner Name", "text"], ["status", "Status", "select"], ["url", "File URL", "text"]],
    columns: ["name", "type", "owner_type", "owner_name", "status"],
  },
};

const titleFor = key => key.replaceAll("_", " ").replace(/\b\w/g, x => x.toUpperCase());

export default function ERPManagement({ module }) {
  const cfg = CONFIG[module];
  const [rows, setRows] = useState([]), [stats, setStats] = useState({}), [loading, setLoading] = useState(true);
  const [q, setQ] = useState(""), [status, setStatus] = useState(""), [page, setPage] = useState(1), [pages, setPages] = useState(1);
  const [formOpen, setFormOpen] = useState(false), [editing, setEditing] = useState(null), [form, setForm] = useState({});
  const [error, setError] = useState(""), [saving, setSaving] = useState(false);
  const [options, setOptions] = useState({ employees: [], clients: [], services: [], projects: [] });
  const pageSize = 10;

  const idField = { clients: "client_id", projects: "project_id", tasks: "task_id", leaves: "leave_id", attendance: "attendance_id", services: "service_id", bookings: "booking_id", documents: "document_id" }[module];

  const load = async (requestedPage = page) => {
    setLoading(true); setError("");
    try {
      const [data, stat] = await Promise.all([listRecords(module, { q: q || undefined, status: status || undefined, page: requestedPage, page_size: pageSize }), getModuleStats(module)]);
      setRows(data.items || []); setPages(data.pages || 1); setStats(stat || {});
    } catch (e) { setError(e.response?.data?.detail || "Could not load data."); }
    finally { setLoading(false); }
  };

  useEffect(() => { setPage(1); load(1); }, [module, status]);
  useEffect(() => { const t = setTimeout(() => load(1), 350); setPage(1); return () => clearTimeout(t); }, [q]);

  useEffect(() => {
    Promise.all([getEmployeeOptions(), getClientOptions(), getServiceOptions(), getProjectOptions()])
      .then(([employees, clients, services, projects]) => setOptions({ employees, clients, services, projects }))
      .catch(() => {});
  }, []);

  const openCreate = () => {
    setEditing(null);
    const initial = {};
    cfg.fields.forEach(([key, , type]) => { initial[key] = key === "status" ? cfg.statuses[0] : (type === "employee_multiselect" ? [] : ""); });
    setForm(initial); setFormOpen(true); setError("");
  };
  const openEdit = row => {
    const f = {};
    cfg.fields.forEach(([key, , type]) => {
      if (type === "employee_multiselect") f[key] = Array.isArray(row[key]) ? row[key] : [];
      else f[key] = Array.isArray(row[key]) ? row[key].join(", ") : (row[key] ?? "");
    });
    setEditing(row[idField]); setForm(f); setFormOpen(true); setError("");
  };
  const set = (key, value) => setForm(old => ({ ...old, [key]: value }));

  const submit = async e => {
    e.preventDefault(); setSaving(true); setError("");
    try {
      const payload = { ...form };
      if (editing) await updateRecord(module, editing, payload); else await createRecord(module, payload);
      setFormOpen(false); setEditing(null); setForm({}); await load(page);
    } catch (e) { setError(e.response?.data?.detail || "Save failed."); }
    finally { setSaving(false); }
  };

  const remove = async row => {
    if (!window.confirm(`Delete ${row.name || row.title || row.company_name || row[idField]}?`)) return;
    try { await deleteRecord(module, row[idField]); await load(page); } catch (e) { setError(e.response?.data?.detail || "Delete failed."); }
  };

  const changeStatus = async (row, next) => {
    try { if (module === "leaves") await updateLeaveStatus(row[idField], next); else await updateStatus(module, row[idField], next); await load(page); }
    catch (e) { setError(e.response?.data?.detail || "Status update failed."); }
  };

  const renderInput = ([key, label, type = "text", required, choices]) => {
    if (key === "status") choices = cfg.statuses;

    if (OPTION_SOURCES[type]) {
      const src = OPTION_SOURCES[type];
      const list = options[src.list] || [];
      return (
        <select
          className="form-input"
          value={form[key] || ""}
          onChange={e => {
            const val = e.target.value;
            const match = list.find(x => x[src.idKey] === val);
            set(key, val);
            set(src.nameKey, match ? src.labelFn(match) : "");
          }}
          required={required}
        >
          <option value="">Select {label}</option>
          {list.map(x => <option key={x[src.idKey]} value={x[src.idKey]}>{src.labelFn(x)}</option>)}
        </select>
      );
    }

    if (type === "employee_multiselect") {
      const list = options.employees || [];
      const selected = Array.isArray(form[key]) ? form[key] : [];
      return (
        <select
          multiple
          className="form-input erp-multiselect"
          value={selected}
          onChange={e => {
            const vals = Array.from(e.target.selectedOptions).map(o => o.value);
            const names = vals.map(v => { const m = list.find(x => x.employee_id === v); return m ? (m.full_name || m.email) : v; });
            set(key, vals);
            set("assigned_employees", names);
          }}
        >
          {list.map(emp => <option key={emp.employee_id} value={emp.employee_id}>{emp.full_name || emp.email}</option>)}
        </select>
      );
    }

    if (choices) return <select className="form-input" value={form[key] || ""} onChange={e => set(key, e.target.value)} required={required}><option value="">Select {label}</option>{choices.map(v => <option key={v} value={v}>{titleFor(v)}</option>)}</select>;
    if (type === "textarea") return <textarea className="form-input" rows="3" value={form[key] || ""} onChange={e => set(key, e.target.value)} required={required} />;
    return <input className="form-input" type={type} value={form[key] || ""} onChange={e => set(key, e.target.value)} required={required} />;
  };

  if (!cfg) return <EmptyState title="Module not found" />;

  return <div>
    <div className="page-header"><h1>{cfg.title}</h1><p className="page-subtitle">{cfg.subtitle}</p></div>
    {error && <div className="alert alert-error">{error}</div>}

    <div className="stat-grid erp-stat-grid">{["total", ...cfg.statuses.slice(0, 4)].map(s => <div className="stat-card" key={s}><div><p className="stat-value">{stats[s] ?? 0}</p><p className="stat-label">{titleFor(s)}</p></div></div>)}</div>

    <div className="panel">
      <div className="panel-header erp-toolbar">
        <div className="erp-search"><input className="form-input" placeholder={`Search ${cfg.title.toLowerCase()}...`} value={q} onChange={e => setQ(e.target.value)} /></div>
        <select className="form-input erp-filter" value={status} onChange={e => setStatus(e.target.value)}><option value="">All Statuses</option>{cfg.statuses.map(s => <option key={s} value={s}>{titleFor(s)}</option>)}</select>
        <button className="btn btn-primary" onClick={openCreate}>+ Add {module === "leaves" ? "Leave" : module === "documents" ? "Document" : titleFor(module).replace(/s$/, "")}</button>
      </div>

      {formOpen && <form onSubmit={submit} className="form-grid erp-form">
        {cfg.fields.map(field => <div className="form-field" key={field[0]}><label>{field[1]} {field[3] && <span className="required">*</span>}</label>{renderInput(field)}
          {module === "documents" && field[0] === "url" && <input type="file" accept=".pdf,.jpg,.jpeg,.png,.doc,.docx,.xls,.xlsx,.txt" onChange={async e => { if (!e.target.files[0]) return; try { const uploaded = await uploadDocument(e.target.files[0]); set("url", uploaded.url); if (!form.name) set("name", uploaded.filename); } catch (err) { setError(err.response?.data?.detail || "Upload failed."); } }} />}
        </div>)}
        <div className="form-actions"><button className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : editing ? "Update" : "Create"}</button><button type="button" className="btn" onClick={() => setFormOpen(false)}>Cancel</button></div>
      </form>}

      {loading ? <Loader label="Loading records..." /> : rows.length === 0 ? <EmptyState title={`No ${cfg.title.toLowerCase()} found`} description="Create a record or change your search/filter." /> : <div className="table-wrap"><table className="data-table"><thead><tr>{cfg.columns.map(c => <th key={c}>{titleFor(c)}</th>)}<th>Actions</th></tr></thead><tbody>{rows.map(row => <tr key={row[idField]}>{cfg.columns.map(c => <td key={c}>{c === "status" ? <StatusBadge status={row[c]} /> : c === "url" && row[c] ? <a href={row[c]} target="_blank" rel="noreferrer">Open</a> : c === "progress" && row[c] !== undefined && row[c] !== null && row[c] !== "" ? `${row[c]}%` : Array.isArray(row[c]) ? row[c].join(", ") : String(row[c] ?? "—")}</td>)}<td><div className="erp-actions"><button className="btn btn-small" onClick={() => openEdit(row)}>Edit</button>{cfg.statuses.length > 1 && <select className="status-select" value={row.status || ""} onChange={e => changeStatus(row, e.target.value)}><option value="">Status</option>{cfg.statuses.map(s => <option key={s} value={s}>{titleFor(s)}</option>)}</select>}<button className="btn btn-small btn-danger" onClick={() => remove(row)}>Delete</button></div></td></tr>)}</tbody></table></div>}

      <div className="erp-pagination"><button className="btn btn-small" disabled={page <= 1} onClick={() => { const p = page - 1; setPage(p); load(p); }}>Previous</button><span>Page {page} of {pages}</span><button className="btn btn-small" disabled={page >= pages} onClick={() => { const p = page + 1; setPage(p); load(p); }}>Next</button></div>
    </div>
  </div>;
}
