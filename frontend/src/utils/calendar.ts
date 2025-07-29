// weekdayMap
export const weekdayMap = [
  '2025-07-07', '2025-07-08', '2025-07-09', '2025-07-10', '2025-07-11'
];

export const rebuildLesson = (ev: any, src: any) => {
  const jsDate = ev.event.start as Date;
  const endJs = ev.event.end as Date;
  const newDay = jsDate.getDay() === 1 ? 0 : jsDate.getDay() - 1;
  const hh = String(jsDate.getHours()).padStart(2, '0');
  const mm = String(jsDate.getMinutes()).padStart(2, '0');
  return {
    ...src,
    day_of_week: newDay,
    start_time: `${hh}:${mm}`,
    duration_minutes: Math.round((endJs.getTime() - jsDate.getTime()) / 60000),
  };
};
