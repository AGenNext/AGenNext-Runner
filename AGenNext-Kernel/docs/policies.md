# Policies

Kernel uses OPA/Rego for policy enforcement.

## Example: deny writes for basic plan

```rego
package agennext.plan

default allow := false

allow if {
  input.action == "tool.call"
  input.context.method == "GET"
}

allow if {
  input.tenant.plan != "basic"
  input.context.method == "POST"
}
```

## Policy packaging

- Store policies by domain (tooling, data, tenant plan).
- Version bundles and roll out gradually.
- Attach `policy_id` in each decision response.
