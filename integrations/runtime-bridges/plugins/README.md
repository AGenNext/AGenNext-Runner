# Runtime Bridge Plugins

These plugin descriptors expose each runtime bridge as an extension/plugin package.

Available plugins:
- `agennext-python-bridge`
- `agennext-node-bridge`
- `agennext-go-bridge`
- `agennext-java-bridge`
- `agennext-dotnet-bridge`
- `agennext-rust-bridge`

Each plugin manifest declares:
- runtime
- entrypoint bridge file
- lifecycle capabilities (`init`, `invoke`, `stream`, `close`)
