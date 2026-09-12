import type { Day, Preferences } from "../types";

const ALL_DAYS: Day[] = ["MON", "TUE", "WED", "THU", "FRI"];

interface Props {
  preferences: Preferences;
  onChange: (p: Preferences) => void;
}

export default function PreferencesPanel({ preferences, onChange }: Props) {
  function toggleDay(day: Day) {
    const has = preferences.avoidDays.includes(day);
    onChange({
      ...preferences,
      avoidDays: has ? preferences.avoidDays.filter((d) => d !== day) : [...preferences.avoidDays, day],
    });
  }

  return (
    <div className="preferences-panel">
      <h2>Preferences</h2>

      <div className="field-row">
        <label>
          Earliest start
          <input
            type="time"
            value={preferences.earliest ?? ""}
            onChange={(e) => onChange({ ...preferences, earliest: e.target.value || undefined })}
          />
        </label>
        <label>
          Latest end
          <input
            type="time"
            value={preferences.latest ?? ""}
            onChange={(e) => onChange({ ...preferences, latest: e.target.value || undefined })}
          />
        </label>
      </div>

      <fieldset>
        <legend>Avoid days</legend>
        {ALL_DAYS.map((day) => (
          <label key={day} className="checkbox">
            <input
              type="checkbox"
              checked={preferences.avoidDays.includes(day)}
              onChange={() => toggleDay(day)}
            />
            {day}
          </label>
        ))}
      </fieldset>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={preferences.allowWaitlisted}
          onChange={(e) => onChange({ ...preferences, allowWaitlisted: e.target.checked })}
        />
        Include waitlisted sections
      </label>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={preferences.minimizeGaps}
          onChange={(e) => onChange({ ...preferences, minimizeGaps: e.target.checked })}
        />
        Prefer compact schedules (minimize gaps)
      </label>

      <label>
        Number of options
        <input
          type="number"
          min={1}
          max={10}
          value={preferences.maxResults}
          onChange={(e) => onChange({ ...preferences, maxResults: Number(e.target.value) })}
        />
      </label>
    </div>
  );
}
