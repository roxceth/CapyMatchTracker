/*
 * Configuración de la página publicada.
 *
 * apiUrl: el link /exec del Apps Script (Deploy → Manage deployments).
 *   Vacío = modo demo con datos falsos. Este link no es secreto: está en el
 *   código que baja cualquier teléfono. Lo que protege los datos es el PIN.
 *
 * qaApiUrl: el /exec de la copia de prueba ("Union Arena Tracker - QA").
 *   Se usa solo abriendo la página con ?qa al final del link.
 */
window.UAT_CONFIG = {
  apiUrl: '',
  qaApiUrl: 'https://script.google.com/macros/s/AKfycbybJybG3MsLTQXF7bDs4Z77eHKWymEb5O5wudX9OcxRilmQCtK6H6PDaZCoFZVtUlAhyg/exec'
};
