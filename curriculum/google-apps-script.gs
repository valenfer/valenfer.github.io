function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    if (data.action === 'chat') {
      return proxyGemini(data);
    }

    return logPregunta(data, e.remoteAddress);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: err.message }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function proxyGemini(data) {
  const API_KEY = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
  if (!API_KEY) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: 'GEMINI_API_KEY no configurada en Script Properties' }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  const modelo = data.model || 'gemini-3.6-flash';
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${modelo}:generateContent?key=${API_KEY}`;

  const payload = {
    contents: data.messages || [],
    systemInstruction: data.systemInstruction || undefined,
    generationConfig: data.generationConfig || { temperature: 0.7, maxOutputTokens: 1024 }
  };

  const response = UrlFetchApp.fetch(url, {
    method: 'POST',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  const result = JSON.parse(response.getContentText());

  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, data: result }))
    .setMimeType(ContentService.MimeType.JSON);
}

function logPregunta(data, ip) {
  try {
    const props = PropertiesService.getScriptProperties();
    const spreadsheetId = props.getProperty('SPREADSHEET_ID');

    if (spreadsheetId) {
      const sheet = SpreadsheetApp.openById(spreadsheetId).getActiveSheet();
      sheet.appendRow([
        new Date(),
        data.pregunta || '',
        data.respuesta || '',
        data.modelo || '',
        data.url || '',
        ip || ''
      ]);
    }

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
    .createTextOutput('AIDA Proxy activo')
    .setMimeType(ContentService.MimeType.TEXT);
}
