import type { Day, ScheduledMeeting } from "../types";
import { minutesToLabel } from "../utils";

const DAYS: Day[] = ["MON", "TUE", "WED", "THU", "FRI"];
const DAY_LABELS: Record<Day, string> = {
  MON: "Mon",
  TUE: "Tue",
  WED: "Wed",
  THU: "Thu",
  FRI: "Fri",
  SAT: "Sat",
  SUN: "Sun",
};

const GRID_START = 7 * 60; // 7:00 AM
const GRID_END = 22 * 60; // 10:00 PM
const GRID_SPAN = GRID_END - GRID_START;

const COLORS = [
  "#4f6df5",
  "#e0673f",
  "#2f9e6f",
  "#a755c9",
  "#d3a029",
  "#3c9ac0",
  "#c94f7a",
  "#5f8b3a",
];

interface Props {
  meetings: ScheduledMeeting[];
}

export default function WeekGrid({ meetings }: Props) {
  const designations = Array.from(new Set(meetings.map((m) => m.designation)));
  const colorFor = (designation: string) =>
    COLORS[designations.indexOf(designation) % COLORS.length];

  const activeDays = meetings.length
    ? DAYS.filter((d) => meetings.some((m) => m.days.includes(d)))
    : DAYS.slice(0, 5);
  const displayDays = activeDays.length ? activeDays : DAYS;

  const hourMarks: number[] = [];
  for (let t = GRID_START; t <= GRID_END; t += 60) hourMarks.push(t);

  return (
    <div className="week-grid" style={{ gridTemplateColumns: `60px repeat(${displayDays.length}, 1fr)` }}>
      <div className="grid-corner" />
      {displayDays.map((d) => (
        <div className="grid-day-header" key={d}>
          {DAY_LABELS[d]}
        </div>
      ))}

      <div className="grid-hours">
        {hourMarks.map((t) => (
          <div key={t} className="hour-label" style={{ top: `${((t - GRID_START) / GRID_SPAN) * 100}%` }}>
            {minutesToLabel(t)}
          </div>
        ))}
      </div>

      {displayDays.map((day) => (
        <div className="grid-day-col" key={day}>
          {hourMarks.map((t) => (
            <div key={t} className="hour-line" style={{ top: `${((t - GRID_START) / GRID_SPAN) * 100}%` }} />
          ))}
          {meetings
            .filter((m) => m.days.includes(day))
            .map((m, idx) => {
              const top = ((m.start - GRID_START) / GRID_SPAN) * 100;
              const height = ((m.end - m.start) / GRID_SPAN) * 100;
              return (
                <div
                  key={`${m.designation}-${m.sectionNum}-${day}-${idx}`}
                  className="meeting-block"
                  style={{
                    top: `${top}%`,
                    height: `${height}%`,
                    background: colorFor(m.designation),
                  }}
                  title={`${m.designation} ${m.sectionType} ${m.sectionNum} — ${m.instructor ?? "TBA"}`}
                >
                  <div className="meeting-title">{m.designation}</div>
                  <div className="meeting-sub">
                    {minutesToLabel(m.start)}–{minutesToLabel(m.end)}
                  </div>
                  {m.room && (
                    <div className="meeting-sub">
                      {m.bldg} {m.room}
                    </div>
                  )}
                </div>
              );
            })}
        </div>
      ))}
    </div>
  );
}
