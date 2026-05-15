"""
services/registry_checker_v2.py
Parallel registry validation using asyncio.gather().
Drop-in replacement for the sequential registry_checker.py.

Improvement: was sequential (each package awaited one by one)
             now parallel (all packages checked simultaneously)
5 packages: was ~5s, now ~1s.
"""
import asyncio
import re
from typing import Dict, Literal

import httpx

RegistryStatus = Literal["valid", "deprecated", "hallucinated"]

REGISTRY_URLS = {
    "pypi":  "https://pypi.org/pypi/{package}/json",
    "npm":   "https://registry.npmjs.org/{package}",
    "maven": "https://search.maven.org/solrsearch/select?q=a:{package}&rows=1&wt=json",
    "nuget": "https://api.nuget.org/v3/registration5/{package}/index.json",
}

# Shared async client — single connection pool for all requests
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        timeout = httpx.Timeout(5.0, connect=2.0, read=3.0, write=3.0, pool=1.0)
        _client = httpx.AsyncClient(timeout=timeout, trust_env=False)
    return _client


async def _check_one(package: str, registry: str) -> tuple[str, RegistryStatus]:
    """Check a single package. Returns (package, status)."""
    url = REGISTRY_URLS.get(registry, REGISTRY_URLS["pypi"]).format(
        package=package.lower()
    )
    try:
        client = _get_client()
        resp   = await asyncio.wait_for(client.get(url), timeout=5.0)

        if resp.status_code == 404:
            return package, "hallucinated"

        if resp.status_code == 200:
            if registry == "pypi":
                data        = resp.json()
                classifiers = data.get("info", {}).get("classifiers", [])
                if any("Development Status :: 7 - Inactive" in c for c in classifiers):
                    return package, "deprecated"
            return package, "valid"

    except Exception:
        pass

    return package, "hallucinated"


async def validate_imports_parallel(
    packages: list[str],
    registry: str = "pypi",
) -> Dict[str, RegistryStatus]:
    """
    Check all packages IN PARALLEL via asyncio.gather().
    Was sequential O(n*latency), now O(max_latency).
    """
    if not packages:
        return {}

    # Fire all requests simultaneously
    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                *[_check_one(pkg, registry) for pkg in packages],
                return_exceptions=True,
            ),
            timeout=6.0,
        )
    except asyncio.TimeoutError:
        return {pkg: "hallucinated" for pkg in packages}

    output: Dict[str, RegistryStatus] = {}
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            output[packages[i]] = "hallucinated"
        else:
            pkg, status = result
            output[pkg] = status

    return output


STDLIB_PYTHON = {
    "os","sys","re","json","io","math","time","datetime","typing","collections",
    "pathlib","logging","abc","enum","dataclasses","asyncio","functools","itertools",
    "threading","subprocess","socket","hashlib","base64","urllib","http","unittest",
    "string","struct","copy","gc","inspect","importlib","traceback","contextlib",
    "warnings","weakref","queue","signal","platform","shutil","tempfile","glob",
    "fnmatch","csv","xml","html","email","mimetypes","uuid","random","secrets",
}

IMPORT_EXTRACTORS = {
    "python": re.compile(r"^\s*(?:import|from)\s+([\w\.]+)", re.MULTILINE),
    "javascript": re.compile(r'require\([\'"]([^"\']+)[\'"]\)|from\s+[\'"]([^"\']+)[\'"]', re.MULTILINE),
    "typescript": re.compile(r'require\([\'"]([^"\']+)[\'"]\)|from\s+[\'"]([^"\']+)[\'"]', re.MULTILINE),
    "csharp": re.compile(r"using\s+([\w\.]+)\s*;", re.MULTILINE),
}

REGISTRY_MAP = {
    "python":     "pypi",
    "javascript": "npm",
    "typescript": "npm",
    "csharp":     "nuget",
}


def extract_packages(code: str, lang: str) -> list[str]:
    """Extract package names from import statements."""
    pattern = IMPORT_EXTRACTORS.get(lang)
    if not pattern:
        return []

    pkgs = set()
    for m in pattern.finditer(code):
        pkg = next((g for g in m.groups() if g), None)
        if pkg:
            root = pkg.split(".")[0].split("/")[0]
            if root and not root.startswith("_"):
                pkgs.add(root)

    # Filter stdlib
    if lang == "python":
        pkgs -= STDLIB_PYTHON

    return list(pkgs)


async def check_imports(code: str, language: str) -> Dict[str, RegistryStatus]:
    """Full pipeline: extract → parallel check → return statuses."""
    registry = REGISTRY_MAP.get(language, "pypi")
    packages = extract_packages(code, language)
    if not packages:
        return {}
    return await validate_imports_parallel(packages, registry)
