import { useParams } from "react-router-dom";
import { getSalarySteps, getJobTitles } from "../services/salaryService";
export default function SalaryDetailPage() {
  const { classification, level } = useParams();
  const steps = getSalarySteps(classification, level);
  const jobs = getJobTitles(classification);
  const minSalary = steps[0]?.salary || 0;
  const maxSalary = steps[steps.length - 1]?.salary || 0;
  const minBiweekly = Math.round(minSalary / 26);
  const maxBiweekly = Math.round(maxSalary / 26);
  return (
    <div className="container">
      <h1>{classification.toUpperCase()}-{level}</h1>
      <div className="card-grid">
        <div className="card">
          <h3>Salary Range</h3>
          <div className="salary-number">${minSalary.toLocaleString()} - ${maxSalary.toLocaleString()}</div>
        </div>
        <div className="card">
          <h3>Biweekly Pay</h3>
          <div className="salary-number">${minBiweekly.toLocaleString()} - ${maxBiweekly.toLocaleString()}</div>
        </div>
      </div>
      <div className="section">
        <h2>Salary Steps</h2>
        {steps.map(step => (
          <div key={step.step} className="step-row">
            <span>Step {step.step}</span>
            <span>${step.salary.toLocaleString()}</span>
          </div>
        ))}
      </div>
      <div className="section">
        <h2>Common Job Titles</h2>
        <ul>{jobs.map(job => <li key={job.title}>{job.title}</li>)}</ul>
      </div>
    </div>
  );
}