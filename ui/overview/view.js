import {element, empty, statusPill, formatTime} from '../components/render.js';
// Incidents needing a decision come first, then other open incidents, then resolved; newest first within each group.
const RANK = status => status === 'AWAITING_APPROVAL' ? 0 : status !== 'RESOLVED' ? 1 : 2;
export function sortIncidents(records) {
  return [...records].sort((a, b) => RANK(a.status) - RANK(b.status) || (Date.parse(b.started_at) || 0) - (Date.parse(a.started_at) || 0));
}
export function renderOverview(data, onSelect) {
  const records = sortIncidents(data.incidents);
  const summary = document.querySelector('#summary'); summary.replaceChildren();
  const awaiting = records.filter(r => r.status === 'AWAITING_APPROVAL');
  for (const [label,count,tone] of [['Recorded incidents',records.length],['Open incidents',records.filter(r=>r.status!=='RESOLVED').length],['Awaiting your decision',awaiting.length,awaiting.length?'action':''],['Resolved incidents',records.filter(r=>r.status==='RESOLVED').length]]) {
    const card=element('div',undefined,`card ${tone||''}`); card.append(element('span',label,'muted'),element('strong',String(count)));
    if(tone){const go=element('button','Review next','primary');go.addEventListener('click',()=>onSelect(awaiting[0].incident_id));card.append(go);}
    summary.append(card);
  }
  const container=document.querySelector('#incidents'); container.replaceChildren();
  if (!records.length) {container.append(empty('No incidents returned. This does not establish service health.'));return;}
  const table=element('table',undefined,'incident-table'),head=element('tr');
  for(const label of ['Incident','Severity','Services','Started','Status',''])head.append(element('th',label));table.append(head);
  for(const record of records){
    const row=element('tr',undefined,'clickable'),cell=element('td'),button=element('button','Open');
    button.addEventListener('click',event=>{event.stopPropagation();onSelect(record.incident_id);});row.addEventListener('click',()=>onSelect(record.incident_id));
    const status=element('td');status.append(statusPill(record.status));cell.append(button);
    row.append(element('td',record.incident_id,'strong'),element('td',record.severity||'—'),element('td',(record.affected_services||[]).join(', ')),element('td',record.started_at?formatTime(record.started_at):'—','nowrap'),status,cell);table.append(row);
  }
  container.append(table);
}
