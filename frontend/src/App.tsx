import { useEffect, useState } from "react";
import CourseInput from "./components/CourseInput";
import PreferencesPanel from "./components/PreferencesPanel";
import ScheduleResults from "./components/ScheduleResults";
import { getSchedules, getTerm } from "./api";
import { defaultPreferences } from "./types";
import type { CourseSummary, Preferences, ScheduleResponse } from "./types";

export default function App() {
  const [selected, setSelected] = useState<CourseSummary[]>([]);
  const [preferences, setPreferences] = useState<Preferences>(defaultPreferences);
  const [response, setResponse] = useState<ScheduleResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [term, setTerm] = useState<string>("");

  useEffect(() => {
    getTerm()
      .then((t) => setTerm(t.name))
      .catch(() => setTerm(""));
  }, []);

  async function handleGenerate() {
    if (selected.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await getSchedules(
        selected.map((c) => c.designation),
        preferences
      );
      setResponse(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>UW-Madison Schedule Planner</h1>
        <p className="hint">{term ? `Planning for ${term}` : "Suggests conflict-free schedules from real course data."}</p>
      </header>

      <div className="layout">
        <div className="sidebar">
          <CourseInput
            selected={selected}
            onAdd={(c) => setSelected((prev) => [...prev, c])}
            onRemove={(id) => setSelected((prev) => prev.filter((c) => c.courseId !== id))}
          />
          <PreferencesPanel preferences={preferences} onChange={setPreferences} />
          <button className="generate-btn" onClick={handleGenerate} disabled={selected.length === 0 || loading}>
            {loading ? "Generating…" : "Generate schedules"}
          </button>
        </div>

        <main>
          <ScheduleResults response={response} loading={loading} error={error} />
        </main>
      </div>
    </div>
  );
}
