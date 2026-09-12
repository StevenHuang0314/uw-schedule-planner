import { useState } from "react";
import type { ScheduleResponse } from "../types";
import WeekGrid from "./WeekGrid";

interface Props {
  response: ScheduleResponse | null;
  loading: boolean;
  error: string | null;
}

export default function ScheduleResults({ response, loading, error }: Props) {
  const [activeIdx, setActiveIdx] = useState(0);

  if (loading) return <div className="results status">Solving…</div>;
  if (error) return <div className="results status error">{error}</div>;
  if (!response) return null;

  if (response.unresolved.length > 0) {
    return (
      <div className="results status error">
        Couldn't find these in the catalog: {response.unresolved.join(", ")}
      </div>
    );
  }

  if (response.infeasibleCourses.length > 0) {
    return (
      <div className="results status error">
        No sections of {response.infeasibleCourses.join(", ")} satisfy your current preferences. Try
        relaxing the time window or allowing waitlisted sections.
      </div>
    );
  }

  if (response.schedules.length === 0) {
    return (
      <div className="results status error">
        No conflict-free combination exists for this set of courses — every pair of sections overlaps.
        Try different courses or preferences.
      </div>
    );
  }

  const active = response.schedules[Math.min(activeIdx, response.schedules.length - 1)];

  return (
    <div className="results">
      <div className="tabs">
        {response.schedules.map((s, i) => (
          <button
            key={i}
            className={i === activeIdx ? "tab active" : "tab"}
            onClick={() => setActiveIdx(i)}
          >
            Option {i + 1}
          </button>
        ))}
      </div>

      <div className="schedule-summary">
        <span>{active.totalCredits} credits</span>
        <span>{active.daysWithClasses} days on campus</span>
        <span>{Math.round(active.gapMinutes / 60)}h total gap time</span>
      </div>

      <WeekGrid meetings={active.meetings} />

      <table className="course-table">
        <thead>
          <tr>
            <th>Course</th>
            <th>Section</th>
            <th>Instructor</th>
            <th>Status</th>
            <th>Seats</th>
          </tr>
        </thead>
        <tbody>
          {active.courses.map((c) => (
            <tr key={c.packageId}>
              <td>
                <strong>{c.designation}</strong>
                <div className="hint">
                  {c.title} · {c.credits} cr
                </div>
              </td>
              <td>
                {c.isAsynchronous
                  ? "Async / Arranged"
                  : c.sections.map((s) => `${s.type} ${s.num}`).join(", ")}
              </td>
              <td>{c.sections.map((s) => s.instructor).filter(Boolean).join(", ") || "TBA"}</td>
              <td>
                <span className={`status-badge ${c.status.toLowerCase()}`}>{c.status}</span>
              </td>
              <td>{c.status === "WAITLISTED" ? `${c.waitlist} waiting` : `${c.seats} open`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
