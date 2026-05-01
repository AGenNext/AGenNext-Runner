/**
 * React Flow Node Definitions for Kernel Theories
 */

export const KERNEL_NODE_TYPES = {
  COGNITIVE_AGENT: 'cognitive_agent',
  EPISTEMIC_TRUST: 'epistemic_trust',
  ACTIVE_INFERENCE: 'active_inference',
  DEONTIC_GUARD: 'deontic_guard',
  TOOL_GATEKEEPER: 'tool_gatekeeper'
};

export const INITIAL_NODES = [
  {
    id: 'kernel-core',
    type: KERNEL_NODE_TYPES.COGNITIVE_AGENT,
    data: { label: 'Kernel Orchestrator' },
    position: { x: 250, y: 5 },
  },
  {
    id: 'trust-ledger',
    type: KERNEL_NODE_TYPES.EPISTEMIC_TRUST,
    data: { label: 'Trust Ledger' },
    position: { x: 100, y: 100 },
  },
  {
    id: 'github-gatekeeper',
    type: KERNEL_NODE_TYPES.TOOL_GATEKEEPER,
    data: { label: 'GitHub Copilot Proxy' },
    position: { x: 400, y: 100 },
  }
];
