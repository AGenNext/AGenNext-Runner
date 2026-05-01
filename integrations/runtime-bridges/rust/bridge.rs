use std::collections::HashMap;

pub struct KernelBridge {
    config: HashMap<String, String>,
}

impl KernelBridge {
    pub fn new() -> Self {
        Self { config: HashMap::new() }
    }

    pub fn init(&mut self, config: HashMap<String, String>) {
        self.config = config;
    }

    pub fn invoke(&self, action: HashMap<String, String>) -> HashMap<String, String> {
        let mut out = HashMap::new();
        out.insert("status".into(), "todo".into());
        out.insert("action".into(), format!("{:?}", action));
        out
    }

    pub fn stream(&self) -> HashMap<String, String> {
        let mut out = HashMap::new();
        out.insert("status".into(), "todo".into());
        out.insert("event".into(), "stream-not-implemented".into());
        out
    }

    pub fn close(&self) {}
}
