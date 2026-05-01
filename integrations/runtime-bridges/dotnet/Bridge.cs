using System.Collections.Generic;

namespace RuntimeBridges;

public class Bridge
{
    private Dictionary<string, object> _config = new();

    public void Init(Dictionary<string, object> config) => _config = config;

    public Dictionary<string, object> Invoke(Dictionary<string, object> action) => new()
    {
        ["status"] = "todo",
        ["action"] = action
    };

    public Dictionary<string, object> Stream() => new()
    {
        ["status"] = "todo",
        ["event"] = "stream-not-implemented"
    };

    public void Close() { }
}
