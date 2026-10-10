export function element(tag, text, cls) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  return node;
}
export function empty(text = 'No recorded data is available.') { return element('div', text, 'empty'); }
export function panel(title) {
  const node = element('article', undefined, 'panel');
  node.append(element('h3', title)); return node;
}
export function value(data) {
  if (data === null || data === undefined) return 'Not recorded';
  if (Array.isArray(data)) return data.map(value).join(', ');
  if (typeof data === 'object') return Object.entries(data).map(([k,v]) => `${k.replaceAll('_',' ')}: ${value(v)}`).join('; ');
  return String(data);
}
export function fields(data, labels = {}) {
  if (!data || !Object.keys(data).length) return empty();
  const table = element('table');
  for (const [key, item] of Object.entries(data)) {
    const row = element('tr'); row.append(element('th', labels[key] || key.replaceAll('_', ' ')), element('td', value(item))); table.append(row);
  }
  return table;
}
export function errorText(data, status) {
  const detail = data?.detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail.message === 'string') return detail.category ? `${detail.category}: ${detail.message}` : detail.message;
  return `Request failed (${status})`;
}
export async function api(path, payload, timeout=10000, headers={}) {
  const response = await fetch(path, {method: payload ? 'POST' : 'GET', headers: {...(payload ? {'Content-Type':'application/json'} : {}), ...headers}, body: payload ? JSON.stringify(payload) : undefined, signal: AbortSignal.timeout(timeout)});
  let data;
  try {data = await response.json();} catch {throw new Error(`API returned an invalid response (${response.status})`);}
  if (!response.ok) throw new Error(errorText(data, response.status));
  return data;
}
