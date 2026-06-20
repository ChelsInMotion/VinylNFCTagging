// ─────────────────────────────────────────────────────────────────────────
//  EVENT AVAILABILITY — CONFIG
//  This is the ONLY file you normally need to edit.
//  Both availability.html and results.html read their settings from here.
// ─────────────────────────────────────────────────────────────────────────
window.SCHEDULE_CONFIG = {

  // The name of your event (shown at the top of both pages).
  eventName: "Our Get-Together",

  // Optional one-line note shown under the title on the form.
  blurb: "Check every date you could make it. You can pick as many as you like.",

  // The candidate dates people choose from, as "YYYY-MM-DD" strings.
  // Add or remove lines to match the dates you're considering.
  dates: [
    "2026-06-26",
    "2026-06-27",
    "2026-06-28",
    "2026-07-03",
    "2026-07-04",
    "2026-07-05"
  ],

  // Paste your Google Apps Script Web App URL here after you deploy it.
  // See SCHEDULING_SETUP.md for the 5-minute setup. It looks like:
  //   https://script.google.com/macros/s/AKfy....../exec
  scriptUrl: "PASTE_YOUR_APPS_SCRIPT_URL_HERE"

};
