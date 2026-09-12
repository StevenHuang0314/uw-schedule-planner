export type Day = "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";
export type PackageStatus = "OPEN" | "WAITLISTED" | "CLOSED";

export interface CourseSummary {
  courseId: string;
  designation: string;
  subjectCode: string;
  subjectShort: string;
  catalogNumber: string;
  title: string;
  minCredits: number;
  maxCredits: number;
}

export interface Preferences {
  earliest?: string;
  latest?: string;
  avoidDays: Day[];
  allowWaitlisted: boolean;
  minimizeGaps: boolean;
  maxResults: number;
}

export const defaultPreferences: Preferences = {
  avoidDays: [],
  allowWaitlisted: true,
  minimizeGaps: true,
  maxResults: 5,
};

export interface ScheduledMeeting {
  designation: string;
  title: string;
  sectionType: string;
  sectionNum: string;
  instructor: string | null;
  days: Day[];
  start: number;
  end: number;
  bldg: string | null;
  room: string | null;
}

export interface SectionInfo {
  type: string;
  num: string;
  instructor: string | null;
}

export interface ScheduledCourse {
  designation: string;
  title: string;
  credits: number;
  packageId: string;
  status: PackageStatus;
  seats: number;
  waitlist: number;
  sections: SectionInfo[];
  isAsynchronous: boolean;
}

export interface ScheduleOption {
  courses: ScheduledCourse[];
  meetings: ScheduledMeeting[];
  totalCredits: number;
  score: number;
  gapMinutes: number;
  daysWithClasses: number;
}

export interface ScheduleResponse {
  requested: string[];
  unresolved: string[];
  infeasibleCourses: string[];
  schedules: ScheduleOption[];
}
