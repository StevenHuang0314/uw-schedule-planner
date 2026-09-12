import type { CourseSummary, Preferences, ScheduleResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function searchCourses(query: string): Promise<CourseSummary[]> {
  if (!query.trim()) return [];
  const res = await fetch(`${BASE_URL}/api/courses/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getSchedules(
  courses: string[],
  preferences: Preferences
): Promise<ScheduleResponse> {
  const res = await fetch(`${BASE_URL}/api/schedule`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ courses, preferences }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Schedule request failed: ${res.status} ${text}`);
  }
  return res.json();
}

export async function getTerm(): Promise<{ code: string; name: string }> {
  const res = await fetch(`${BASE_URL}/api/courses/term`);
  if (!res.ok) throw new Error(`Failed to load term: ${res.status}`);
  return res.json();
}
