/** Formatea el texto de una respuesta del asistente (que usa **negrita** para las secciones
 * "Resumen / Normas / Pasos / Aviso legal") a HTML seguro: escapa el contenido primero y solo
 * después inserta las etiquetas <strong>/<br> propias, nunca HTML proveniente del modelo. */
export function formatMessageHtml(text: string): string {
  const escaped = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  return escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>')
}
