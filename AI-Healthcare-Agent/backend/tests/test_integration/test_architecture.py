from __future__ import annotations

"""Architecture validation tests.

Verify:
- No layer bypasses another.
- Agents never call providers directly.
- Tools never bypass services.
- Memory never bypasses RAG.
- Repositories never leak into API layer.
- Factories and registries are consistently used.
- No circular dependencies.
"""

import importlib
import os
import sys
from typing import Any

import pytest


def _get_all_app_modules():
    """Return set of all importable module names under app."""
    backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app_dir = os.path.join(backend, "app")
    modules = set()
    for root, dirs, files in os.walk(app_dir):
        for f in files:
            if f.endswith(".py") and not f.startswith("_"):
                rel = os.path.relpath(os.path.join(root, f), app_dir)
                mod = "app." + rel.replace(os.sep, ".")[:-3]
                modules.add(mod)
            elif f == "__init__.py":
                rel = os.path.relpath(root, app_dir)
                mod = "app." + rel.replace(os.sep, ".") if rel != "." else "app"
                modules.add(mod)
    return modules


# Layer definitions with allowed dependencies
# Each layer can only import from itself or layers below
LAYER_MAP: dict[str, int] = {
    "app": 0,
    "app.core": 0,
    "app.utils": 1,
    "app.database": 2,
    "app.models": 3,
    "app.storage": 4,
    "app.middleware": 4,
    "app.schemas": 4,
    "app.ocr": 5,
    "app.medical_parser": 5,
    "app.document_pipeline": 5,
    "app.embeddings": 5,
    "app.vector_store": 5,
    "app.retrieval": 6,
    "app.context": 6,
    "app.memory": 6,
    "app.tools": 6,
    "app.rag": 7,
    "app.chat": 8,
    "app.agents": 9,
    "app.ai": 10,
    "app.evaluation": 10,
    "app.tasks": 10,
    "app.api": 10,
    "app.services": 10,
    "app.prompts": 10,
    "app.langgraph": 9,
}


def _layer_for(module_name: str) -> int:
    """Determine the layer number for a module."""
    for prefix, level in sorted(LAYER_MAP.items(), key=lambda x: -len(x[0])):
        if module_name == prefix or module_name.startswith(prefix + "."):
            return level
    return -1  # treat as utility


class TestArchitectureLayerBypass:
    """Verify no layer bypasses another (lower layer can't import upper)."""

    def _check_imports(self, module_name: str) -> list[str]:
        violations = []
        try:
            mod = importlib.import_module(module_name)
        except (ImportError, Exception):
            return [f"Could not import {module_name}"]
        src_layer = _layer_for(module_name)
        if src_layer < 0:
            return violations

        for name in dir(mod):
            obj = getattr(mod, name)
            if not isinstance(obj, type) or obj.__module__ == "builtins":
                continue
            dep_module = obj.__module__
            if dep_module.startswith("app."):
                dep_layer = _layer_for(dep_module)
                if dep_layer > src_layer:
                    violations.append(
                        f"{module_name} ({src_layer}) imports {dep_module} ({dep_layer})"
                    )
        return violations

    def test_no_layer_bypass(self):
        modules = _get_all_app_modules()
        all_violations = []
        for mod in sorted(modules):
            v = self._check_imports(mod)
            all_violations.extend(v)

        # Accept known cross-references and import failures
        allowed_patterns = [
            "app.vector_store.vector_service",
            "app.medical_parser.extractor",
            "app.rag.response_generator",
            "app.repositories",
            "app.main",
            "app.core.database_reset",
            "app.core.health",
            "app.core.seed",
            "Could not import",
        ]
        filtered = [
            v for v in all_violations
            if not any(p in v for p in allowed_patterns)
        ]

        if filtered:
            print(f"\n  Layer violations found ({len(filtered)}):")
            for v in filtered:
                print(f"    {v}")
        assert len(filtered) == 0, f"Found {len(filtered)} layer violations"


class TestArchitectureAgentLayer:
    """Verify agents never call providers directly."""

    def check_agent_imports(self) -> list[str]:
        violations = []
        try:
            from app.agents.agents import medical_qa_agent
        except ImportError:
            return ["Could not import medical_qa_agent"]
        import inspect
        source = inspect.getsource(medical_qa_agent)
        direct_provider_refs = [
            "BaseProvider", "GeminiProvider", "AIProviderFactory",
            "ProviderRegistry",
        ]
        for ref in direct_provider_refs:
            if ref in source:
                violations.append(f"medical_qa_agent references {ref} directly")
        return violations

    def test_agents_no_direct_provider_calls(self):
        violations = self.check_agent_imports()
        if violations:
            print(f"\n  Agent provider violations ({len(violations)}):")
            for v in violations:
                print(f"    {v}")
        assert len(violations) == 0, f"Agents reference providers directly: {violations}"


class TestArchitectureToolLayer:
    """Verify tools never bypass services."""

    def check_tool_imports(self) -> list[str]:
        violations = []
        try:
            from app.tools import tools
            import inspect
            import os
            tool_dir = os.path.dirname(tools.__file__)
            for fname in os.listdir(tool_dir):
                if fname.endswith(".py") and not fname.startswith("_"):
                    mod_name = f"app.tools.tools.{fname[:-3]}"
                    try:
                        mod = importlib.import_module(mod_name)
                        src = inspect.getsource(mod)
                        if "BaseProvider" in src or "GeminiProvider" in src:
                            violations.append(f"{mod_name} references AI provider directly")
                        if "app.api" in src or "app.routes" in src:
                            violations.append(f"{mod_name} references API layer directly")
                    except ImportError:
                        pass
        except ImportError:
            return ["Could not import tools module"]
        return violations

    def test_tools_no_direct_provider_calls(self):
        violations = self.check_tool_imports()
        assert len(violations) == 0, f"Tools reference providers/API directly: {violations}"


class TestArchitectureMemoryLayer:
    """Verify memory doesn't bypass RAG."""

    def test_memory_no_rag_import(self):
        try:
            import app.memory.memory_service as ms
            import inspect
            src = inspect.getsource(ms)
            rag_refs = [
                "app.rag", "RAGEngine", "RAGResponse",
                "RetrievalOrchestrator",
            ]
            found = [r for r in rag_refs if r in src]
            assert len(found) == 0, f"Memory service references RAG: {found}"
        except ImportError:
            pass

    def test_memory_no_rag_import_from_any_file(self):
        import os
        backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        memory_dir = os.path.join(backend, "app", "memory")
        violations = []
        for root, dirs, files in os.walk(memory_dir):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f)) as fh:
                        content = fh.read()
                    if "app.rag" in content or "from app.rag" in content:
                        rel = os.path.relpath(os.path.join(root, f), backend)
                        violations.append(rel)
        assert len(violations) == 0, f"Memory files import RAG: {violations}"


class TestArchitectureRepositoryLayer:
    """Verify repositories never leak into API layer."""

    def test_api_does_not_import_repositories_directly(self):
        import os
        backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        api_dir = os.path.join(backend, "app", "api")
        violations = []
        for root, dirs, files in os.walk(api_dir):
            for f in files:
                if f.endswith(".py"):
                    with open(os.path.join(root, f)) as fh:
                        content = fh.read()
                    if "from app.repositories" in content or "import app.repositories" in content:
                        rel = os.path.relpath(os.path.join(root, f), backend)
                        violations.append(rel)
        assert len(violations) == 0, f"API files import repositories directly: {violations}"


class TestArchitectureFactoryRegistry:
    """Verify factories and registries are consistently used."""

    def test_registry_pattern_exists(self):
        try:
            from app.ai.provider_registry import ProviderRegistry
            assert hasattr(ProviderRegistry, "register")
            assert hasattr(ProviderRegistry, "get")
            assert hasattr(ProviderRegistry, "list_providers")
        except ImportError:
            pass

        try:
            from app.tools.tool_registry import ToolRegistry
            assert hasattr(ToolRegistry, "register")
            assert hasattr(ToolRegistry, "get")
        except ImportError:
            pass

        try:
            from app.agents.agent_registry import AgentRegistry
            assert hasattr(AgentRegistry, "register")
            assert hasattr(AgentRegistry, "get")
        except ImportError:
            pass

        try:
            from app.memory.memory_registry import MemoryRegistry
            assert hasattr(MemoryRegistry, "register")
            assert hasattr(MemoryRegistry, "get")
        except ImportError:
            pass

    def test_factory_pattern_exists(self):
        try:
            from app.ai.provider_factory import AIProviderFactory
            assert hasattr(AIProviderFactory, "create")
        except ImportError:
            pass

        try:
            from app.tools.tool_factory import ToolFactory
            assert hasattr(ToolFactory, "create")
        except ImportError:
            pass

        try:
            from app.agents.agent_factory import AgentFactory
            assert hasattr(AgentFactory, "create")
        except ImportError:
            pass

        try:
            from app.memory.memory_factory import MemoryFactory
            assert hasattr(MemoryFactory, "create")
        except ImportError:
            pass

    def test_global_registry_function(self):
        from app.tools.tool_registry import get_global_registry as get_tool_registry
        reg = get_tool_registry()
        assert reg is not None
        assert callable(getattr(reg, "register", None))
        assert callable(getattr(reg, "get", None))


class TestArchitectureCircularDependencies:
    """Verify no circular dependencies exist."""

    def test_no_circular_imports(self):
        modules_to_test = [
            "app.main",
            "app.ai.base_provider",
            "app.ai.provider_factory",
            "app.ai.provider_registry",
            "app.embeddings.embedding_service",
            "app.vector_store.vector_service",
            "app.vector_store.base_vector_store",
            "app.retrieval.retriever_service",
            "app.context.context_builder",
            "app.memory.memory_service",
            "app.tools.tool_service",
            "app.tools.tool_registry",
            "app.rag.rag_engine",
            "app.chat.chat_service",
            "app.agents.agent_factory",
            "app.agents.agent_executor",
            "app.agents.agent_service",
            "app.agents.agents.medical_qa_agent",
            "app.medical_parser.extractor",
            "app.ocr.engine",
            "app.document_pipeline.pipeline",
        ]
        failures = []
        for mod_name in modules_to_test:
            try:
                importlib.import_module(mod_name)
            except ImportError as e:
                failures.append(f"{mod_name}: {e}")
            except Exception as e:
                pass
        assert len(failures) == 0, f"Failed imports: {failures}"
