import { useEffect, useRef, useState } from "react";
import { searchCourses } from "../api";
import type { CourseSummary } from "../types";

interface Props {
  selected: CourseSummary[];
  onAdd: (course: CourseSummary) => void;
  onRemove: (courseId: string) => void;
}

export default function CourseInput({ selected, onAdd, onRemove }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CourseSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(async () => {
      setLoading(true);
      try {
        const r = await searchCourses(query);
        setResults(r.filter((c) => !selected.some((s) => s.courseId === c.courseId)));
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => window.clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  return (
    <div className="course-input">
      <label htmlFor="course-search">Add a course</label>
      <input
        id="course-search"
        type="text"
        placeholder="e.g. COMP SCI 300, MATH 222, STAT..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      {loading && <div className="hint">Searching…</div>}
      {results.length > 0 && (
        <ul className="autocomplete">
          {results.map((c) => (
            <li key={c.courseId}>
              <button
                type="button"
                onClick={() => {
                  onAdd(c);
                  setQuery("");
                  setResults([]);
                }}
              >
                <strong>{c.designation}</strong> — {c.title}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="selected-courses">
        {selected.length === 0 && <p className="hint">No courses added yet.</p>}
        {selected.map((c) => (
          <span className="chip" key={c.courseId}>
            {c.designation}
            <button type="button" aria-label={`Remove ${c.designation}`} onClick={() => onRemove(c.courseId)}>
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}
