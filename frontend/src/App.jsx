import { useState } from "react";
import "./App.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  || "http://localhost:8000";

const initialForm = {
  title: "",
  description: "",
  service_name: "",
  source: "user_report",
};

function App() {
  const [formData, setFormData] = useState(initialForm);
  const [submissionState, setSubmissionState] = useState("idle");
  const [submittedIncident, setSubmittedIncident] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  function updateField(event) {
    const { name, value } = event.target;

    setFormData((currentForm) => ({
      ...currentForm,
      [name]: value,
    }));
  }

  async function submitIncident(event) {
    event.preventDefault();

    setSubmissionState("submitting");
    setSubmittedIncident(null);
    setErrorMessage("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/incidents`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...formData,
            severity: "unknown",
            status: "open",
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          "We could not submit your incident. Please try again.",
        );
      }

      const incident = await response.json();

      setSubmittedIncident(incident);
      setFormData(initialForm);
      setSubmissionState("success");
    } catch (error) {
      setErrorMessage(error.message);
      setSubmissionState("error");
    }
  }

  const isSubmitting = submissionState === "submitting";

  return (
    <main className="app-shell">
      <section className="intro">
        <p className="product-name">
          AI Incident Triage Copilot
        </p>
        <h1>Report an issue</h1>
        <p className="intro-copy">
          Tell us what is not working. The incident will be
          analyzed and sent to the engineering team when needed.
        </p>
      </section>

      <section className="report-layout">
        <form
          className="report-form"
          onSubmit={submitIncident}
        >
          <div className="form-heading">
            <h2>Issue details</h2>
            <p>
              Include the affected service and what you observed.
            </p>
          </div>

          <label htmlFor="title">
            Issue title
          </label>
          <input
            id="title"
            name="title"
            type="text"
            value={formData.title}
            onChange={updateField}
            placeholder="Example: Unable to complete checkout"
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
            value={formData.service_name}
            onChange={updateField}
            placeholder="Example: payment-api"
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
            value={formData.description}
            onChange={updateField}
            placeholder={
              "Describe what you were doing, what you expected, "
              + "and what happened instead."
            }
            minLength="10"
            required
          />

          <button
            className="submit-button"
            type="submit"
            disabled={isSubmitting}
          >
            {isSubmitting
              ? "Submitting..."
              : "Submit incident"}
          </button>

          {submissionState === "error" && (
            <p className="form-message error-message">
              {errorMessage}
            </p>
          )}
        </form>

        <aside className="help-panel">
          <h2>What happens next</h2>
          <ol>
            <li>Your report is recorded as an incident.</li>
            <li>The AI predicts its category and severity.</li>
            <li>High-risk incidents are sent to engineers.</li>
          </ol>
        </aside>
      </section>

      {submissionState === "success" && submittedIncident && (
        <section className="success-panel">
          <p className="success-label">Incident submitted</p>
          <h2>{submittedIncident.title}</h2>
          <p>
            Reference ID: <code>{submittedIncident.id}</code>
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
        </section>
      )}
    </main>
  );
}

export default App;