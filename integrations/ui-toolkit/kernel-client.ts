/**
 * Agent Kernel TypeScript Client
 * Maps to Schema.org + Universal Semantic Extension
 */

export interface SemanticExtension {
  lineage?: {
    source_artifacts: string[];
    transformation_logic: string;
  };
  taxonomy?: {
    labels: string[];
  };
  attributes?: Record<string, any>;
  audit_tracking?: {
    created_by: string;
    created_at: string;
  };
}

export interface KernelAction {
  "@context": "https://schema.org";
  "@type": string;
  name: string;
  agent: { "@type": string; name: string };
  object?: any;
  payload?: any;
  semantic_extension: SemanticExtension;
}

export class KernelClient {
  constructor(private baseUrl: string) {}

  async processAction(action: KernelAction) {
    const response = await fetch(`${this.baseUrl}/api/v1/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(action),
    });
    return response.json();
  }

  async getIdentity(agentId: string) {
    const response = await fetch(`${this.baseUrl}/api/v1/identity/${agentId}`);
    return response.json();
  }
}
