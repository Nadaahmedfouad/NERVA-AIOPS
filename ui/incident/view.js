import {element, panel, fields, empty} from '../components/render.js';

const LABELS = {rca:'Root cause analysis', anomaly:'Linked anomaly', evidence:'Captured evidence', decision:'Proposal',
  action_result:'Actuator result', recovery_result:'Measured recovery'};

export function approvalBlocked(bundle, config) {
  if (!config.approval_enabled) return config.operator_auth === 'disabled'
    ? 'Decisions are disabled: the operator boundary is not configured (M5_UI_OPERATOR_TOKEN or M5_UI_TRUSTED_NETWORK).'
    : 'Approval requires the connected operator configuration.';
  if (bundle.incident?.status !== 'AWAITING_APPROVAL') return 'No proposal is awaiting approval.';
  if (!bundle.decision) return 'No proposal is recorded.';
  if (bundle.action_result || bundle.workflow?.execution_intent) return 'An action was already started for this proposal.';
  if (bundle.proposal_state?.expired) return 'This proposal has expired. M4 will re-diagnose before anything can be approved.';
  if (!bundle.proposal_digest) return 'The proposal digest is missing; reload before approving.';
  return null;
}

export function renderIncident(bundle, config, onApproval, onStore) {
  const root=document.querySelector('#incident-body');root.replaceChildren();
  const prov=bundle.provenance||{};
  const provenance=panel('Evidence source');
  provenance.append(fields({workflow_source:bundle.source||'not recorded',providers_used:prov.used||bundle.provider_modes,
    roles_not_used:prov.unused,configured_now:prov.configured_now,actuator:bundle.remediation_backend}));
  if(bundle.source!=='real')provenance.append(element('p',bundle.source==='mixed'
    ?'Mixed provenance: at least one mock input or effect was used. This incident is never stored as real history.'
    :'Mock or unverified provenance: not evidence of real remediation.','muted'));
  root.append(provenance);
  const missing=(bundle.missing||[]).map(key=>LABELS[key]||key);
  if(missing.length){const gaps=panel('Missing information');const list=element('ul',undefined,'evidence');for(const item of missing)list.append(element('li',`${item}: not recorded`));gaps.append(list);root.append(gaps);}
  const timeline=panel('Incident timeline'),list=element('ol',undefined,'timeline');
  const events=[[bundle.deployment_event?.timestamp,'Deployment recorded'],[bundle.incident?.started_at,'Incident started'],[bundle.action_result?.started_at,'Action started'],[bundle.action_result?.completed_at,'Action completed'],...(bundle.audit||[]).map(item=>[item.timestamp,item.event||item.event_type||'Recorded workflow event'])];
  for(const [time,title] of events.filter(item=>item[0]).sort((a,b)=>Date.parse(a[0])-Date.parse(b[0]))){const li=element('li');li.append(element('time',time),element('span',title));list.append(li);}
  timeline.append(list.childNodes.length?list:empty('No timeline timestamps recorded.'));root.append(timeline);
  const incident=panel('Incident');incident.append(fields(bundle.incident));root.append(incident);
  const anomaly=panel('Linked anomaly');anomaly.append(fields(bundle.anomaly?{anomaly_id:bundle.anomaly.anomaly_id,timestamp:bundle.anomaly.timestamp,score:bundle.anomaly.score,model:bundle.anomaly.model,features:bundle.anomaly.features}:null));root.append(anomaly);
  const rca=panel('Root cause and evidence');rca.append(fields(bundle.rca ? {root_cause:bundle.rca.root_cause,affected_component:bundle.rca.affected_component,confidence:bundle.rca.confidence}:null));
  if(bundle.rca?.evidence?.length){const evidence=element('ul',undefined,'evidence');for(const item of bundle.rca.evidence)evidence.append(element('li',item));rca.append(evidence);}
  const before=bundle.evidence?.before;if(before)rca.append(fields({captured_version:before.version,captured_at:bundle.evidence.captured_at,captured_metrics:before.metrics}));
  root.append(rca);
  const decision=panel('Recommended action');decision.append(fields(bundle.decision));
  if(bundle.proposal_state)decision.append(fields({proposal_created:bundle.proposal_state.created_at,expires:bundle.proposal_state.expires_at,expired:bundle.proposal_state.expired,proposal_digest:bundle.proposal_digest}));
  const blocked=approvalBlocked(bundle,config);
  let token;
  if(config.operator_auth==='token'){token=element('input');token.type='password';token.placeholder='Operator token';token.autocomplete='off';token.setAttribute('aria-label','Operator token');decision.append(token);}
  // Reject needs only a pending proposal; approve also needs a fresh proposal and its digest.
  const canDecide=Boolean(config.approval_enabled&&bundle.incident?.status==='AWAITING_APPROVAL'&&bundle.decision&&!bundle.action_result&&!bundle.workflow?.execution_intent);
  const actions=element('div',undefined,'actions');
  for(const action of ['approve','reject']){
    const button=element('button',action==='approve'?'Approve':'Reject');
    button.disabled=action==='approve'?Boolean(blocked):!canDecide;
    button.addEventListener('click',()=>{for(const choice of actions.childNodes)choice.disabled=true;onApproval(action,button,{digest:bundle.proposal_digest,token:token?.value});});
    actions.append(button);
  }
  decision.append(actions);if(blocked)decision.append(element('p',blocked,'muted'));root.append(decision);
  const execution=panel('Execution');
  execution.append(fields({actuator_result:bundle.action_result,durable_intent:bundle.workflow?.execution_intent,outcome_unknown:bundle.workflow?.execution_ambiguous}));
  if(bundle.workflow?.reconciliation){execution.append(element('p','Operator observation (not an actuator result):','muted'),fields(bundle.workflow.reconciliation));}
  else if(bundle.workflow?.execution_ambiguous)execution.append(element('p','The action outcome is unknown. It will not be repeated; an operator must reconcile it with evidence.','muted'));
  root.append(execution);
  const recovery=panel('Recovery validation');
  recovery.append(fields(bundle.recovery_result),fields(bundle.recovery_validation),fields({deadline:bundle.workflow?.recovery_deadline,last_error:bundle.workflow?.recovery_error}));
  if(!bundle.recovery_result)recovery.append(element('p','No measured M1 recovery is recorded. Recovery is never inferred from the action.','muted'));
  root.append(recovery);
  const workflow=panel('Workflow status');workflow.append(fields(bundle.workflow));root.append(workflow);
  const memory=panel('Incident memory');memory.append(fields(bundle.memory),fields(bundle.archive||bundle.memory_archive||{archive_status:bundle.workflow?.archive_status,attempts:bundle.workflow?.archive_attempts,error:bundle.workflow?.archive_error}));
  if(config.source==='mock'){const button=element('button','Store terminal demo incident');button.disabled=!['RESOLVED','ESCALATED'].includes(bundle.incident?.status)||!bundle.memory||Boolean(bundle.archive);button.addEventListener('click',()=>onStore(button));memory.append(button);}
  else memory.append(element('p','M4 archives terminal incidents automatically. Refresh to check the archive status.','muted'));
  root.append(memory);
  if(bundle.status==='degraded'||bundle.reason||bundle.errors?.length){const state=panel('Unavailable evidence');state.append(fields({reason:bundle.reason,errors:bundle.errors}));root.append(state);}
}
export function renderFinops(bundle) {
  const root=document.querySelector('#finops-body');root.replaceChildren();
  const observed=panel('Resource context');observed.append(fields(bundle.finops_context));root.append(observed);
  const impact=panel('Cost / SLO impact');impact.append(fields({cost_impact:bundle.cost_impact,slo_impact:bundle.slo_impact}));impact.append(element('p','Estimated cost options are not measured financial savings.','muted'));root.append(impact);
}
