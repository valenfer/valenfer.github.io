function doPost(e) {
  try {
    const sheet = SpreadsheetApp.openById('TU_SPREADSHEET_ID_AQUI').getActiveSheet();
    const data = JSON.parse(e.postData.contents);

    sheet.appendRow([
      new Date(),
      data.pregunta || '',
      data.respuesta || '',
      data.modelo || '',
      data.url || ''
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet() {
  return ContentService
    .createTextOutput('AIDA Logger activo')
    .setMimeType(ContentService.MimeType.TEXT);
}