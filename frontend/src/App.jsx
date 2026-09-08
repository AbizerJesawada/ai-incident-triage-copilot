import { useEffect, useMemo, useState } from "react";
import "./App.css";
import {
  clearAccessToken,
  createIncident,
  getAccessToken,
  getCorrelationTimeline,
  getCurrentUser,
  getIncidents,
  getRecommendations,
  getSimilarIncidents,
  loginUser,
  registerUser,
  resolveIncident,
} from "./api";

const initialReportForm = {
  title: "",
  description: "",
  service_name: "",
  source: "user_report",
};

const initialResolutionForm = {
  resolution_note: "",
};

const initialAuthForm = {
  full_name: "",
  email: "",
  password: "",
};

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  return new Date(value).toLocaleString();
}

function formatSlaStatus(value) {
  return (value || "on_track").replace("_", " ");
}

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [authState, setAuthState] = useState(() => {
    return getAccessToken() ? "checking" : "ready";
  });
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState(initialAuthForm);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");

  const [activeView, setActiveView] = useState("report");
  const [reportForm, setReportForm] = useState(
    initialReportForm,
  );
  const [reportState, setReportState] = useState("idle");
  const [reportError, setReportError] = useState("");
  const [submittedIncident, setSubmittedIncident] = useState(
    null,
  );

  const [incidents, setIncidents] = useState([]);
  const [workspaceState, setWorkspaceState] = useState("idle");
  const [workspaceError, setWorkspaceError] = useState("");
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [severityFilter, setSeverityFilter] = useState("all");
  const [serviceFilter, setServiceFilter] = useState("all");
  const [slaFilter, setSlaFilter] = useState("all");

  const [selectedIncident, setSelectedIncident] = useState(null);
  const [detailsState, setDetailsState] = useState("idle");
  const [similarIncidents, setSimilarIncidents] = useState([]);
  const [correlations, setCorrelations] = useState([]);
  const [recommendations, setRecommendations] = useState([]);

  const [resolutionForm, setResolutionForm] = useState(
    initialResolutionForm,
  );
  const [resolutionState, setResolutionState] = useState("idle");
  const [resolutionError, setResolutionError] = useState("");

  const isEngineer = currentUser?.role === "engineer";

  useEffect(() => {
    if (!getAccessToken()) {
      return;
    }

    getCurrentUser()
      .then((user) => {
        setCurrentUser(user);
        setAuthState("ready");
      })
      .catch(() => {
        clearAccessToken();
        setAuthState("ready");
      });
  }, []);

  async function loadIncidents() {
    setWorkspaceState("loading");
    setWorkspaceError("");

    try {
      const loadedIncidents = await getIncidents();

      setIncidents(loadedIncidents);
      setWorkspaceState("ready");
    } catch (error) {
      setWorkspaceError(error.message);
      setWorkspaceState("error");
    }
  }

  const serviceOptions = useMemo(() => {
    return [...new Set(
      incidents.map((incident) => incident.service_name),
    )].sort();
  }, [incidents]);

  const filteredIncidents = useMemo(() => {
    const normalizedSearch = searchText.trim().toLowerCase();

    return incidents.filter((incident) => {
      const incidentText = [
        incident.title,
        incident.description,
        incident.service_name,
      ].join(" ").toLowerCase();

      const matchesSearch = !normalizedSearch
        || incidentText.includes(normalizedSearch);

      const matchesStatus = statusFilter === "all"
        || incident.status === statusFilter;

      const matchesSeverity = severityFilter === "all"
        || (
          incident.predicted_severity
          || incident.severity
        ) === severityFilter;

      const matchesService = serviceFilter === "all"
        || incident.service_name === serviceFilter;

      const matchesSla = slaFilter === "all"
        || incident.sla_status === slaFilter;

      return (
        matchesSearch
        && matchesStatus
        && matchesSeverity
        && matchesService
        && matchesSla
      );
    });
  }, [
    incidents,
    searchText,
    statusFilter,
    severityFilter,
    serviceFilter,
    slaFilter,
  ]);

  function updateAuthField(event) {
    const { name, value } = event.target;

    setAuthForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  }

  function updateReportField(event) {
    const { name, value } = event.target;

    setReportForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  }

  function updateResolutionField(event) {
    const { name, value } = event.target;

    setResolutionForm((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  }

  async function submitAuthentication(event) {
    event.preventDefault();

    setAuthState("submitting");
    setAuthError("");
    setAuthSuccess("");

    try {
      if (authMode === "register") {
        await registerUser({
          full_name: authForm.full_name,
          email: authForm.email,
          password: authForm.password,
        });

        setAuthForm({
          full_name: "",
          email: authForm.email,
          password: "",
        });
        setAuthMode("login");
        setAuthSuccess(
          "Account created. Sign in with your email and password.",
        );
        setAuthState("ready");

        return;
      }

      await loginUser({
        email: authForm.email,
        password: authForm.password,
      });

      const user = await getCurrentUser();

      setCurrentUser(user);
      setActiveView(
        user.role === "engineer" ? "workspace" : "report",
      );

      if (user.role === "engineer") {
        loadIncidents();
      }

      setAuthForm(initialAuthForm);
      setAuthState("ready");
    } catch (error) {
      setAuthError(error.message);
      setAuthState("error");
    }
  }

  function logout() {
    clearAccessToken();
    setCurrentUser(null);
    setActiveView("report");
    setIncidents([]);
    setSelectedIncident(null);
    setSubmittedIncident(null);
    setAuthForm(initialAuthForm);
    setAuthError("");
    setAuthSuccess("");
    setAuthState("ready");
  }

  async function submitIncident(event) {
    event.preventDefault();

    setReportState("submitting");
    setReportError("");
    setSubmittedIncident(null);

    try {
      const incident = await createIncident({
        ...reportForm,
        severity: "unknown",
        status: "open",
      });

      setSubmittedIncident(incident);
      setReportForm(initialReportForm);
      setReportState("success");
    } catch (error) {
      setReportError(error.message);
      setReportState("error");
    }
  }

  async function selectIncident(incident) {
    setSelectedIncident(incident);
    setResolutionForm(initialResolutionForm);
    setResolutionState("idle");
    setResolutionError("");
    setDetailsState("loading");

    if (!isEngineer) {
      setSimilarIncidents([]);
      setCorrelations([]);
      setRecommendations([]);
      setDetailsState("ready");

      return;
    }

    try {
      const [
        similar,
        correlationTimeline,
        remediationRecommendations,
      ] = await Promise.all([
        getSimilarIncidents(incident.id),
        getCorrelationTimeline(incident.id),
        getRecommendations(incident.id),
      ]);

      setSimilarIncidents(similar);
      setCorrelations(correlationTimeline);
      setRecommendations(remediationRecommendations);
      setDetailsState("ready");
    } catch {
      setDetailsState("error");
    }
  }

  async function submitResolution(event) {
    event.preventDefault();

    if (!selectedIncident) {
      return;
    }

    setResolutionState("submitting");
    setResolutionError("");

    try {
      const resolvedIncident = await resolveIncident(
        selectedIncident.id,
        resolutionForm,
      );

      setSelectedIncident(resolvedIncident);
      setIncidents((currentIncidents) => {
        return currentIncidents.map((incident) => {
          return incident.id === resolvedIncident.id
            ? resolvedIncident
            : incident;
        });
      });
      setResolutionForm(initialResolutionForm);
      setResolutionState("success");
    } catch (error) {
      setResolutionError(error.message);
      setResolutionState("error");
    }
  }

  function openWorkspace() {
    setActiveView("workspace");
    loadIncidents();
  }

  if (authState === "checking") {
    return (
      <main className="auth-page">
        <p className="state-message">Checking your session...</p>
      </main>
    );
  }

  if (!currentUser) {
    const isRegistering = authMode === "register";

    return (
      <main className="auth-page">
        <section className="auth-panel">
          <p className="product-name">
            AI Incident Triage Copilot
          </p>
          <h1>
            {isRegistering ? "Create account" : "Sign in"}
          </h1>

          <form
            className="auth-form"
            onSubmit={submitAuthentication}
          >
            {isRegistering && (
              <>
                <label htmlFor="full_name">Full name</label>
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  value={authForm.full_name}
                  onChange={updateAuthField}
                  minLength="2"
                  maxLength="100"
                  required
                />
              </>
            )}

            <label htmlFor="email">Email address</label>
            <input
              id="email"
              name="email"
              type="email"
              value={authForm.email}
              onChange={updateAuthField}
              required
            />

            <label htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              value={authForm.password}
              onChange={updateAuthField}
              minLength="8"
              required
            />

            <button
              className="primary-button"
              type="submit"
              disabled={authState === "submitting"}
            >
              {authState === "submitting"
                ? "Please wait..."
                : isRegistering
                  ? "Create account"
                  : "Sign in"}
            </button>

            {authError && (
              <p className="error-message">{authError}</p>
            )}

            {authSuccess && (
              <p className="success-message">{authSuccess}</p>
            )}
          </form>

          <button
            className="text-button"
            type="button"
            onClick={() => {
              setAuthMode(
                isRegistering ? "login" : "register",
              );
              setAuthError("");
              setAuthSuccess("");
            }}
          >
            {isRegistering
              ? "Already have an account? Sign in"
              : "Need an account? Create one"}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="product-name">
            AI Incident Triage Copilot
          </p>
          <h1>Incident operations</h1>
        </div>

        <div className="header-actions">
          <div className="current-user">
            <strong>{currentUser.full_name}</strong>
            <span>{currentUser.role}</span>
          </div>

          <nav className="view-tabs" aria-label="Application views">
            <button
              className={
                activeView === "report"
                  ? "tab-button tab-active"
                  : "tab-button"
              }
              type="button"
              onClick={() => setActiveView("report")}
            >
              {isEngineer ? "New incident" : "Report issue"}
            </button>
            <button
              className={
                activeView === "workspace"
                  ? "tab-button tab-active"
                  : "tab-button"
              }
              type="button"
              onClick={openWorkspace}
            >
              {isEngineer
                ? "Engineer workspace"
                : "My incidents"}
            </button>
          </nav>

          <button
            className="secondary-button"
            type="button"
            onClick={logout}
          >
            Log out
          </button>
        </div>
      </header>

      {activeView === "report" && (
        <section className="report-page">
          <div className="report-intro">
            <p className="eyebrow">
              {isEngineer ? "For engineers" : "For users"}
            </p>
            <h2>
              {isEngineer ? "Create incident" : "Report an issue"}
            </h2>
            <p>
              Describe what is not working and submit the issue
              for triage.
            </p>
          </div>

          <div className="report-layout">
            <form
              className="report-form"
              onSubmit={submitIncident}
            >
              <label htmlFor="title">Issue title</label>
              <input
                id="title"
                name="title"
                type="text"
                value={reportForm.title}
                onChange={updateReportField}
                placeholder="Unable to complete checkout"
                minLength="5"
                maxLength="200"
                required
              />

              <label htmlFor="service_name">
                Affected service
              </label>
              <input
                id="service_name"
                name="service_name"
                type="text"
                value={reportForm.service_name}
                onChange={updateReportField}
                placeholder="payment-api"
                minLength="2"
                maxLength="100"
                required
              />

              <label htmlFor="description">
                What happened?
              </label>
              <textarea
                id="description"
                name="description"
                value={reportForm.description}
                onChange={updateReportField}
                placeholder={
                  "Describe what you expected and what "
                  + "happened instead."
                }
                minLength="10"
                required
              />

              <button
                className="primary-button"
                type="submit"
                disabled={reportState === "submitting"}
              >
                {reportState === "submitting"
                  ? "Submitting..."
                  : "Submit incident"}
              </button>

              {reportState === "error" && (
                <p className="error-message">{reportError}</p>
              )}
            </form>

            <aside className="info-panel">
              <h3>Report status</h3>
              <p>
                You can view incidents reported from your account
                in My incidents.
              </p>
            </aside>
          </div>

          {reportState === "success" && submittedIncident && (
            <section className="success-panel">
              <p className="success-label">Incident submitted</p>
              <h3>{submittedIncident.title}</h3>
              <p>
                Reference ID:{" "}
                <code>{submittedIncident.id}</code>
              </p>
              <p>
                Initial assessment:{" "}
                <strong>
                  {submittedIncident.predicted_severity}
                </strong>{" "}
                severity,{" "}
                <strong>
                  {submittedIncident.predicted_category}
                </strong>{" "}
                category.
              </p>
              <button
                className="text-button"
                type="button"
                onClick={openWorkspace}
              >
                {isEngineer
                  ? "Open engineer workspace"
                  : "View my incidents"}
              </button>
            </section>
          )}
        </section>
      )}

      {activeView === "workspace" && (
        <section className="workspace-page">
          <div className="workspace-heading">
            <div>
              <p className="eyebrow">
                {isEngineer ? "For engineers" : "For users"}
              </p>
              <h2>
                {isEngineer
                  ? "Engineer workspace"
                  : "My incidents"}
              </h2>
              <p>
                {isEngineer
                  ? "Search incidents, investigate evidence, and record resolutions."
                  : "Review the incidents submitted from your account."}
              </p>
            </div>

            <button
              className="secondary-button"
              type="button"
              onClick={loadIncidents}
            >
              Refresh incidents
            </button>
          </div>

          <section className="filter-bar" aria-label="Filters">
            <input
              aria-label="Search incidents"
              type="search"
              value={searchText}
              onChange={(event) => {
                setSearchText(event.target.value);
              }}
              placeholder="Search incidents"
            />

            <select
              aria-label="Filter by status"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
              }}
            >
              <option value="all">All statuses</option>
              <option value="open">Open</option>
              <option value="resolved">Resolved</option>
            </select>

            <select
              aria-label="Filter by severity"
              value={severityFilter}
              onChange={(event) => {
                setSeverityFilter(event.target.value);
              }}
            >
              <option value="all">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>

            <select
              aria-label="Filter by service"
              value={serviceFilter}
              onChange={(event) => {
                setServiceFilter(event.target.value);
              }}
            >
              <option value="all">All services</option>
              {serviceOptions.map((serviceName) => (
                <option key={serviceName} value={serviceName}>
                  {serviceName}
                </option>
              ))}
            </select>

            <select
              aria-label="Filter by SLA status"
              value={slaFilter}
              onChange={(event) => {
                setSlaFilter(event.target.value);
              }}
            >
              <option value="all">All SLA states</option>
              <option value="on_track">On track</option>
              <option value="at_risk">At risk</option>
              <option value="breached">Breached</option>
              <option value="resolved">Resolved</option>
            </select>
          </section>

          {workspaceState === "loading" && (
            <p className="state-message">Loading incidents...</p>
          )}

          {workspaceState === "error" && (
            <p className="error-message">{workspaceError}</p>
          )}

          {workspaceState === "ready" && (
            <section className="workspace-layout">
              <section className="incident-table-panel">
                <div className="panel-title-row">
                  <h3>Incidents</h3>
                  <span>{filteredIncidents.length} shown</span>
                </div>

                {filteredIncidents.length === 0 ? (
                  <p className="state-message">
                    No incidents match these filters.
                  </p>
                ) : (
                  <div className="incident-table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Incident</th>
                          <th>Service</th>
                          <th>Severity</th>
                          <th>SLA</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredIncidents.map((incident) => (
                          <tr
                            key={incident.id}
                            className={
                              selectedIncident?.id === incident.id
                                ? "selected-row"
                                : ""
                            }
                            onClick={() => selectIncident(incident)}
                          >
                            <td>
                              <strong>{incident.title}</strong>
                              <span className="table-subtext">
                                {formatDate(incident.created_at)}
                              </span>
                            </td>
                            <td>{incident.service_name}</td>
                            <td>
                              <span
                                className={
                                  `status-badge severity-`
                                  + `${
                                    incident.predicted_severity
                                    || incident.severity
                                  }`
                                }
                              >
                                {incident.predicted_severity
                                  || incident.severity}
                              </span>
                            </td>
                            <td>
                              <span
                                className={
                                  `status-badge sla-`
                                  + `${incident.sla_status}`
                                }
                              >
                                {formatSlaStatus(
                                  incident.sla_status,
                                )}
                              </span>
                            </td>
                            <td>{incident.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>

              <aside className="detail-panel">
                {!selectedIncident && (
                  <p className="state-message">
                    Select an incident to view its details.
                  </p>
                )}

                {selectedIncident && (
                  <>
                    <div className="detail-heading">
                      <div>
                        <p className="eyebrow">
                          Incident detail
                        </p>
                        <h3>{selectedIncident.title}</h3>
                      </div>
                      <span
                        className={
                          `status-badge sla-`
                          + `${selectedIncident.sla_status}`
                        }
                      >
                        {formatSlaStatus(
                          selectedIncident.sla_status,
                        )}
                      </span>
                    </div>

                    <p className="detail-description">
                      {selectedIncident.description}
                    </p>

                    <dl className="detail-grid">
                      <div>
                        <dt>Service</dt>
                        <dd>{selectedIncident.service_name}</dd>
                      </div>
                      <div>
                        <dt>Severity</dt>
                        <dd>
                          {selectedIncident.predicted_severity
                            || selectedIncident.severity}
                        </dd>
                      </div>
                      <div>
                        <dt>SLA due</dt>
                        <dd>
                          {formatDate(
                            selectedIncident.sla_due_at,
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Triage route</dt>
                        <dd>
                          {selectedIncident.triage_route
                            || "Not available"}
                        </dd>
                      </div>
                    </dl>

                    {isEngineer && (
                      <>
                        <section className="evidence-section">
                          <h4>Similar past incidents</h4>
                          {detailsState === "loading" && (
                            <p>
                              Loading investigation evidence...
                            </p>
                          )}
                          {detailsState === "ready"
                            && similarIncidents.length === 0 && (
                            <p>No similar incidents found.</p>
                          )}
                          {detailsState === "ready"
                            && similarIncidents.length > 0 && (
                            <ul>
                              {similarIncidents.map((incident) => (
                                <li key={incident.id}>
                                  <strong>{incident.title}</strong>
                                  <span>
                                    {Math.round(
                                      incident.similarity_score * 100,
                                    )}
                                    % similar
                                  </span>
                                </li>
                              ))}
                            </ul>
                          )}
                        </section>

                        <section className="evidence-section">
                          <h4>Change evidence</h4>
                          {detailsState === "ready"
                            && correlations.length === 0 && (
                            <p>No saved change evidence.</p>
                          )}
                          {detailsState === "ready"
                            && correlations.length > 0 && (
                            <p>
                              {correlations[0].correlation_reason}
                            </p>
                          )}
                        </section>

                        <section className="evidence-section">
                          <h4>Recommendations</h4>
                          {detailsState === "ready"
                            && recommendations.length === 0 && (
                            <p>No recommendations saved.</p>
                          )}
                          {detailsState === "ready"
                            && recommendations.length > 0 && (
                            <p>
                              {recommendations[0].recommendation}
                            </p>
                          )}
                        </section>
                      </>
                    )}

                    {selectedIncident.status === "resolved" && (
                      <section className="resolution-record">
                        <h4>Resolution record</h4>
                        <p>
                          Resolved by:{" "}
                          <strong>
                            {selectedIncident.resolved_by}
                          </strong>
                        </p>
                        <p>{selectedIncident.resolution_note}</p>
                        <p>
                          Resolved at:{" "}
                          {formatDate(selectedIncident.resolved_at)}
                        </p>
                      </section>
                    )}

                    {isEngineer
                      && selectedIncident.status !== "resolved" && (
                      <form
                        className="resolution-form"
                        onSubmit={submitResolution}
                      >
                        <h4>Resolve incident</h4>

                        <label htmlFor="resolution_note">
                          Resolution note
                        </label>
                        <textarea
                          id="resolution_note"
                          name="resolution_note"
                          value={resolutionForm.resolution_note}
                          onChange={updateResolutionField}
                          placeholder="Describe the fix and verification."
                          minLength="10"
                          required
                        />

                        <button
                          className="resolve-button"
                          type="submit"
                          disabled={
                            resolutionState === "submitting"
                          }
                        >
                          {resolutionState === "submitting"
                            ? "Resolving..."
                            : "Mark as resolved"}
                        </button>

                        {resolutionState === "success" && (
                          <p className="success-message">
                            Incident resolved successfully.
                          </p>
                        )}

                        {resolutionState === "error" && (
                          <p className="error-message">
                            {resolutionError}
                          </p>
                        )}
                      </form>
                    )}
                  </>
                )}
              </aside>
            </section>
          )}
        </section>
      )}
    </main>
  );
}

export default App;