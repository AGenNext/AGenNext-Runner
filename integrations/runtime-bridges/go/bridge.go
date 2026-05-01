package runtimebridges

type KernelBridge struct {
	Config map[string]any
}

func (k *KernelBridge) Init(config map[string]any) {
	k.Config = config
}

func (k *KernelBridge) Invoke(action map[string]any) map[string]any {
	return map[string]any{"status": "todo", "action": action}
}

func (k *KernelBridge) Stream() <-chan map[string]any {
	ch := make(chan map[string]any, 1)
	ch <- map[string]any{"status": "todo", "event": "stream-not-implemented"}
	close(ch)
	return ch
}

func (k *KernelBridge) Close() {}
