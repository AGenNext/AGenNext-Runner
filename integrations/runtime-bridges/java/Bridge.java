package runtimebridges;

import java.util.Map;

public class Bridge {
    private Map<String, Object> config;

    public void init(Map<String, Object> config) {
        this.config = config;
    }

    public Map<String, Object> invoke(Map<String, Object> action) {
        return Map.of("status", "todo", "action", action);
    }

    public Map<String, Object> stream() {
        return Map.of("status", "todo", "event", "stream-not-implemented");
    }

    public void close() {
        // no-op
    }
}
