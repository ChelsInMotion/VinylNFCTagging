# Event Availability — setup guide

A tiny, free scheduler: people open a link, check the dates they can make, and
you see the overlap. Responses are stored in a Google Sheet you own.

There are **three files** that make it work:

| File | What it is |
|------|------------|
| `availability.html` | The form people fill in. |
| `results.html` | The overlap view (for you). |
| `schedule-config.js` | The one file you edit: event name, dates, and the link to your sheet. |
| `Code.gs` | The Google Apps Script that saves answers to your sheet. |

---

## Step 1 — Create the Google Sheet + script (≈5 min, one time)

1. Go to <https://sheets.new> to create a new blank Google Sheet. Name it
   anything (e.g. "Event Availability").
2. In the menu choose **Extensions ▸ Apps Script**. A code editor opens.
3. Delete whatever is in `Code.gs` there, then **paste in the contents of the
   `Code.gs` file from this project**. Click the **💾 Save** icon.
4. Click **Deploy ▸ New deployment**.
   - Click the gear ⚙️ next to "Select type" and pick **Web app**.
   - **Execute as:** `Me`
   - **Who has access:** `Anyone`  ← important, this lets the form reach it.
   - Click **Deploy**. Approve the permissions prompt (it's your own script).
5. Copy the **Web app URL**. It ends in `/exec` and looks like:
   `https://script.google.com/macros/s/AKfy............/exec`

> If you ever edit `Code.gs`, do **Deploy ▸ Manage deployments ▸ ✏️ Edit ▸
> Version: New version ▸ Deploy** so the changes go live. The URL stays the same.

---

## Step 2 — Configure the site

Open **`schedule-config.js`** and edit the values:

```js
window.SCHEDULE_CONFIG = {
  eventName: "Our Get-Together",
  blurb: "Check every date you could make it.",
  dates: [
    "2026-06-26",
    "2026-06-27"
    // ...add the dates you're considering, format YYYY-MM-DD
  ],
  scriptUrl: "https://script.google.com/macros/s/AKfy....../exec"  // ← paste from Step 1
};
```

That's the only file you normally touch.

---

## Step 3 — Publish & share

These are plain static files, so any static host works. Since this repo already
serves pages, the simplest option is **GitHub Pages**:

- Push these files, then in the repo go to **Settings ▸ Pages** and enable it
  for the branch. Your form will be at:
  `https://<user>.github.io/<repo>/availability.html`

Share the **`availability.html`** link with people. Watch the overlap come in on
**`results.html`** (or just open the Google Sheet directly).

---

## How it works (for the curious)

- Submitting does a `POST` to your Apps Script, which appends a row to the sheet.
  It uses `no-cors`, so the browser fires the request without needing the script
  to send CORS headers — the row still gets written.
- `results.html` reads the data back using **JSONP** (`?callback=...`), which
  works from any origin without CORS configuration.
- No accounts, no servers, no cost beyond your Google account.

## Troubleshooting

- **"Not connected yet" warning** → `scriptUrl` in `schedule-config.js` still has
  the placeholder. Paste the real `/exec` URL.
- **Results page can't load** → make sure the deployment's *Who has access* is
  **Anyone**, and that you copied the `/exec` (not `/dev`) URL.
- **Edited Code.gs but nothing changed** → redeploy a **new version** (see note
  in Step 1).
- **Want to wipe responses** → just delete the rows in the Google Sheet (keep the
  header row).
