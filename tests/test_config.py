"""
tests/test_config.py
Validate config.yaml and docker-compose.yml structure.
No external dependencies — just file parsing.
"""

import pytest
import yaml
import os

ROOT = os.path.dirname(os.path.dirname(__file__))


class TestConfigYaml:

    def setup_method(self):
        with open(os.path.join(ROOT, "config.yaml")) as f:
            self.config = yaml.safe_load(f)

    def test_model_list_exists(self):
        assert "model_list" in self.config
        assert len(self.config["model_list"]) > 0

    def test_all_models_have_required_fields(self):
        for model in self.config["model_list"]:
            assert "model_name" in model, f"Missing model_name: {model}"
            assert "litellm_params" in model, f"Missing litellm_params: {model}"
            assert "model" in model["litellm_params"], f"Missing model in litellm_params: {model}"

    def test_local_ollama_models_present(self):
        aliases = [m["model_name"] for m in self.config["model_list"]]
        assert any("qwen3" in a for a in aliases), "Qwen3-30B-A3B missing"
        assert any("coder" in a for a in aliases), "Qwen2.5-Coder missing"
        assert any("qwen2.5:14b" in a or "qwen2.5-14b" in a.lower() for a in aliases), "Qwen2.5-14B missing"

    def test_cloud_fallback_models_present(self):
        aliases = [m["model_name"] for m in self.config["model_list"]]
        assert any("groq" in a for a in aliases), "Groq fallback missing"

    def test_no_hardcoded_api_keys(self):
        """API keys must use os.environ/ references, never hardcoded."""
        for model in self.config["model_list"]:
            params = model.get("litellm_params", {})
            api_key = params.get("api_key", "")
            if api_key:
                assert api_key.startswith("os.environ/"), \
                    f"Hardcoded API key in {model['model_name']}: {api_key}"

    def test_router_settings_present(self):
        assert "router_settings" in self.config
        rs = self.config["router_settings"]
        assert rs.get("routing_strategy") == "usage-based-routing"
        assert "fallbacks" in rs
        assert len(rs["fallbacks"]) > 0

    def test_litellm_settings_present(self):
        assert "litellm_settings" in self.config

    def test_general_settings_has_master_key(self):
        gs = self.config.get("general_settings", {})
        assert gs.get("master_key") == "os.environ/LITELLM_MASTER_KEY"

    def test_vertex_models_have_project(self):
        vertex_models = [
            m for m in self.config["model_list"]
            if "vertex" in m["model_name"]
        ]
        for m in vertex_models:
            params = m["litellm_params"]
            assert "vertex_project" in params, f"Missing vertex_project: {m['model_name']}"

    def test_no_nllb_or_seamless(self):
        """NLLB and SeamlessM4T are CC-BY-NC — must never appear."""
        config_str = yaml.dump(self.config).lower()
        assert "nllb" not in config_str, "NLLB-200 (CC-BY-NC) detected in config"
        assert "seamless" not in config_str, "SeamlessM4T (CC-BY-NC) detected in config"


class TestDockerCompose:

    def setup_method(self):
        with open(os.path.join(ROOT, "docker-compose.yml")) as f:
            self.compose = yaml.safe_load(f)

    def test_required_services_present(self):
        services = self.compose.get("services", {})
        required = ["litellm", "postgres", "ollama", "prometheus", "grafana", "langflow"]
        for svc in required:
            assert svc in services, f"Required service missing: {svc}"

    def test_all_services_have_container_names(self):
        services = self.compose.get("services", {})
        for name, svc in services.items():
            assert "container_name" in svc, f"Missing container_name: {name}"

    def test_all_services_have_restart_policy(self):
        services = self.compose.get("services", {})
        for name, svc in services.items():
            assert "restart" in svc, f"Missing restart policy: {name}"

    def test_litellm_has_traefik_labels(self):
        litellm = self.compose["services"]["litellm"]
        labels = litellm.get("labels", [])
        label_str = " ".join(str(l) for l in labels)
        assert "llm.openautonomyx.com" in label_str

    def test_no_version_attribute(self):
        """version attribute is obsolete — should not be present."""
        assert "version" not in self.compose, \
            "Remove 'version:' attribute — it is obsolete in Docker Compose v2+"

    def test_coolify_network_external(self):
        networks = self.compose.get("networks", {})
        assert "coolify" in networks
        assert networks["coolify"].get("external") is True

    def test_volumes_defined(self):
        volumes = self.compose.get("volumes", {})
        assert "ollama-data" in volumes
        assert "postgres-data" in volumes
        assert "langflow-data" in volumes


class TestEnvExample:

    def test_env_example_exists(self):
        path = os.path.join(ROOT, ".env.example")
        assert os.path.exists(path), ".env.example missing"

    def test_required_vars_present(self):
        path = os.path.join(ROOT, ".env.example")
        with open(path) as f:
            content = f.read()
        required = [
            "LITELLM_MASTER_KEY",
            "POSTGRES_PASSWORD",
            "GROQ_API_KEY",
            "LANGFLOW_SECRET_KEY",
            "VERTEX_PROJECT",
        ]
        for var in required:
            assert var in content, f"Required var missing from .env.example: {var}"

    def test_no_real_secrets_in_example(self):
        """Ensure .env.example never contains real secrets."""
        path = os.path.join(ROOT, ".env.example")
        with open(path) as f:
            content = f.read()
        # Should never contain real-looking keys
        assert "sk-" not in content or "YOUR" in content, \
            "Possible real API key in .env.example"


class TestGlitchTip:

    def setup_method(self):
        with open(os.path.join(ROOT, "docker-compose.yml")) as f:
            self.compose = yaml.safe_load(f)

    def test_glitchtip_services_present(self):
        services = self.compose.get("services", {})
        for svc in ["glitchtip", "glitchtip-worker", "postgres", "glitchtip-redis"]:
            assert svc in services, f"Missing GlitchTip service: {svc}"

    def test_glitchtip_version_pinned(self):
        image = self.compose["services"]["glitchtip"]["image"]
        assert "latest" not in image, "GlitchTip image must be pinned, not :latest"
        assert "6.1.5" in image

    def test_glitchtip_worker_uses_same_version(self):
        web = self.compose["services"]["glitchtip"]["image"]
        worker = self.compose["services"]["glitchtip-worker"]["image"]
        assert web == worker, "glitchtip and glitchtip-worker must use same image version"

    def test_glitchtip_traefik_label(self):
        labels = self.compose["services"]["glitchtip"].get("labels", [])
        label_str = " ".join(str(l) for l in labels)
        assert "errors.openautonomyx.com" in label_str

    def test_glitchtip_db_health_check(self):
        db = self.compose["services"]["postgres"]
        assert "healthcheck" in db

    def test_glitchtip_redis_health_check(self):
        redis = self.compose["services"]["glitchtip-redis"]
        assert "healthcheck" in redis

    def test_glitchtip_volumes_defined(self):
        volumes = self.compose.get("volumes", {})
        assert "postgres-data" in volumes
        assert "glitchtip-uploads" in volumes

    def test_glitchtip_env_vars_in_example(self):
        with open(os.path.join(ROOT, ".env.example")) as f:
            content = f.read()
        assert "GLITCHTIP_SECRET_KEY" in content
        assert "GLITCHTIP_DB_PASSWORD" in content


class TestOCICompliance:
    """Verify all Dockerfiles carry OCI standard annotations."""

    REQUIRED_LABELS = [
        "org.opencontainers.image.title",
        "org.opencontainers.image.description",
        "org.opencontainers.image.source",
        "org.opencontainers.image.vendor",
        "org.opencontainers.image.licenses",
    ]

    DOCKERFILES = [
        "playwright/Dockerfile",
        "classifier/Dockerfile",
        "translator/Dockerfile",
    ]

    def test_all_dockerfiles_have_oci_labels(self):
        for dockerfile in self.DOCKERFILES:
            path = os.path.join(ROOT, dockerfile)
            content = open(path).read()
            for label in self.REQUIRED_LABELS:
                assert label in content, \
                    f"Missing OCI label '{label}' in {dockerfile}"

    def test_source_url_correct(self):
        for dockerfile in self.DOCKERFILES:
            path = os.path.join(ROOT, dockerfile)
            content = open(path).read()
            assert "openautonomyx/autonomyx-model-gateway" in content, \
                f"Wrong or missing source URL in {dockerfile}"

    def test_vendor_is_openautonomyx(self):
        for dockerfile in self.DOCKERFILES:
            path = os.path.join(ROOT, dockerfile)
            content = open(path).read()
            assert "OPENAUTONOMYX" in content, \
                f"Missing vendor label in {dockerfile}"

    def test_license_is_mit(self):
        for dockerfile in self.DOCKERFILES:
            path = os.path.join(ROOT, dockerfile)
            content = open(path).read()
            assert "MIT" in content, \
                f"Missing or wrong license in {dockerfile}"


class TestSurrealDBSelfHosted:

    def test_surrealdb_service_in_compose(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        assert "surrealdb" in c["services"]

    def test_surrealdb_image_pinned(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        image = c["services"]["surrealdb"]["image"]
        assert "latest" not in image
        assert "surrealdb/surrealdb:v" in image

    def test_surrealdb_uses_rocksdb(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        cmd = " ".join(c["services"]["surrealdb"].get("command", []))
        assert "rocksdb" in cmd

    def test_surrealdb_has_volume(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        vols = c["services"]["surrealdb"].get("volumes", [])
        assert any("surrealdb-data" in str(v) for v in vols)

    def test_surrealdb_internal_only(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        labels = c["services"]["surrealdb"].get("labels", [])
        assert any("traefik.enable=false" in str(l) for l in labels)

    def test_surrealdb_has_healthcheck(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        assert "healthcheck" in c["services"]["surrealdb"]

    def test_surrealdb_volume_declared(self):
        import yaml
        c = yaml.safe_load(open("docker-compose.yml"))
        assert "surrealdb-data" in c["volumes"]

    def test_surreal_env_vars_in_example(self):
        content = open(".env.example").read()
        assert "SURREAL_USER" in content
        assert "SURREAL_PASS" in content
        assert "SURREAL_URL" in content

    def test_migration_script_exists(self):
        import os
        assert os.path.exists("scripts/migrate_surrealdb.sh")

    def test_migration_script_has_all_steps(self):
        content = open("scripts/migrate_surrealdb.sh").read()
        assert "Step 1" in content  # health check
        assert "Step 2" in content  # export from cloud
        assert "Step 3" in content  # import to self-hosted
        assert "Step 4" in content  # verify record counts
        assert "Step 5" in content  # update SURREAL_URL
        assert "/export" in content
        assert "/import" in content
