/**
 * Event Availability — Google Apps Script backend.
 *
 * This script turns a Google Sheet into a tiny database for the availability
 * form. It does two things:
 *   • doPost  — saves a person's submission as a new row.
 *   • doGet   — returns all submissions as JSON (used by results.html via JSONP).
 *
 * SETUP: see SCHEDULING_SETUP.md. In short:
 *   1. Make a Google Sheet, open Extensions ▸ Apps Script, paste this in.
 *   2. Deploy ▸ New deployment ▸ Web app ▸ Execute as "Me",
 *      Who has access "Anyone".
 *   3. Copy the /exec URL into schedule-config.js (scriptUrl).
 */

var SHEET_NAME = 'Responses';

function getSheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(['Timestamp', 'Name', 'Dates']);
  }
  return sheet;
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(20000); // avoid two submissions writing at once
  try {
    var data = JSON.parse(e.postData.contents);
    var name = (data.name || '').toString();
    var dates = Array.isArray(data.dates) ? data.dates : [];
    getSheet_().appendRow([new Date(), name, dates.join(', ')]);
    return json_({ result: 'success' });
  } catch (err) {
    return json_({ result: 'error', message: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function doGet(e) {
  var sheet = getSheet_();
  var values = sheet.getDataRange().getValues();
  var responses = [];
  for (var i = 1; i < values.length; i++) { // skip header row
    var row = values[i];
    if (!row[1] && !row[2]) continue; // skip blank rows
    responses.push({
      timestamp: row[0] ? new Date(row[0]).toISOString() : '',
      name: row[1] ? String(row[1]) : '',
      dates: String(row[2] || '')
        .split(',')
        .map(function (s) { return s.trim(); })
        .filter(function (s) { return s.length; })
    });
  }

  var payload = { responses: responses };
  var callback = e && e.parameter && e.parameter.callback;
  if (callback) {
    // JSONP: wrap JSON in the callback so results.html can read it cross-origin.
    return ContentService
      .createTextOutput(callback + '(' + JSON.stringify(payload) + ')')
      .setMimeType(ContentService.MimeType.JAVASCRIPT);
  }
  return json_(payload);
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
