import { PageHeader } from "@/components/page-header";

export default function NewWorkflowPage() {
  return (
    <>
      <PageHeader
        eyebrow="New workflow"
        title="Prepare a candidate review."
        description="The form is present for product development; submission stays disabled until workflow persistence and uploads are connected."
      />
      <form className="workflow-form">
        <label>
          Workflow template
          <select defaultValue="hr-candidate-screening">
            <option value="hr-candidate-screening">
              HR Candidate Screening
            </option>
            <option disabled>Sales Lead Qualification (planned)</option>
            <option disabled>Engineering Change Review (planned)</option>
          </select>
        </label>
        <label>
          Workflow title
          <input
            name="title"
            placeholder="Candidate screening: Jane Doe"
            type="text"
          />
        </label>
        <label>
          Review goal
          <textarea
            name="user_request"
            placeholder="Assess role fit against the supplied job description and hiring policy."
            rows={5}
          />
        </label>
        <fieldset>
          <legend>Required artifacts</legend>
          <div className="artifact-grid">
            {["Resume", "Job description", "Hiring policy"].map((item) => (
              <div className="artifact-slot" key={item}>
                <strong>{item}</strong>
                <span>Upload wiring comes next</span>
              </div>
            ))}
          </div>
        </fieldset>
        <button className="button primary" disabled type="submit">
          Create workflow
        </button>
      </form>
    </>
  );
}

