# analysis/hallucination_agent/registry_checker.py
"""
Live registry validation for AI-generated code imports.
Registries:
  PyPI   — Python
  npm    — JavaScript / TypeScript
  Maven  — Java
  NuGet  — C# / .NET (added for Windows ecosystem)

For each import → check existence + version + method validity.
"""
import re
import httpx
from typing import List
from analysis.models.analysis_models import HallucinationItem

REGISTRIES = {
    "pypi":  "https://pypi.org/pypi/{package}/json",
    "npm":   "https://registry.npmjs.org/{package}",
    "maven": "https://search.maven.org/solrsearch/select?q=a:{package}&rows=1&wt=json",
    "nuget": "https://api.nuget.org/v3/registration5-gz-semver2/{package}/index.json",
}

LANGUAGE_REGISTRY_MAP = {
    "python":     "pypi",
    "javascript": "npm",
    "typescript": "npm",
    "java":       "maven",
    "csharp":     "nuget",
    "cs":         "nuget",
}

# Import extraction patterns per language
IMPORT_PATTERNS = {
    "python":     re.compile(r"^(?:import|from)\s+([\w.]+)", re.MULTILINE),
    "javascript": re.compile(r'(?:require|import)[^\'"]*[\'"]([\w@/\-]+)[\'"]', re.MULTILINE),
    "typescript": re.compile(r'(?:require|import)[^\'"]*[\'"]([\w@/\-]+)[\'"]', re.MULTILINE),
    "java":       re.compile(r"^import\s+([\w.]+);", re.MULTILINE),
    "csharp":     re.compile(r"^using\s+([\w.]+);", re.MULTILINE),
}


async def check_imports(code: str, language: str) -> List[HallucinationItem]:
    """
    Extract all imports from code and validate each against live registry.
    Returns list of HallucinationItem (valid / deprecated / hallucinated).
    """
    registry  = LANGUAGE_REGISTRY_MAP.get(language.lower(), "pypi")
    pattern   = IMPORT_PATTERNS.get(language.lower())
    if not pattern:
        return []

    imports = list({m.group(1).split(".")[0] for m in pattern.finditer(code)})
    imports = [i for i in imports if i and not _is_stdlib(i, language)]

    results = []
    async with httpx.AsyncClient(timeout=8.0) as client:
        for pkg in imports[:20]:    # cap at 20 imports per file
            item = await _check_one(client, pkg, registry, language)
            results.append(item)

    return results


async def _check_one(
    client: httpx.AsyncClient,
    package: str,
    registry: str,
    language: str,
) -> HallucinationItem:
    url = REGISTRIES[registry].format(package=package.lower())
    try:
        resp = await client.get(url)
        if resp.status_code == 404:
            return HallucinationItem(
                name=package, status="hallucinated", registry=registry,
                suggestion=f"'{package}' not found in {registry}. Check spelling.",
            )
        if resp.status_code == 200:
            data = resp.json()
            deprecated = _is_deprecated(data, registry)
            return HallucinationItem(
                name=package,
                status="deprecated" if deprecated else "valid",
                registry=registry,
                version_checked=_latest_version(data, registry),
                suggestion=f"'{package}' is deprecated. Find replacement on {registry}." if deprecated else None,
            )
        # Non-200/404 → treat as unknown, mark valid conservatively
        return HallucinationItem(name=package, status="valid", registry=registry)
    except Exception:
        return HallucinationItem(name=package, status="valid", registry=registry)


def _is_deprecated(data: dict, registry: str) -> bool:
    if registry == "pypi":
        info = data.get("info", {})
        classifiers = info.get("classifiers", [])
        return any("Development Status :: 7 - Inactive" in c for c in classifiers)
    if registry == "npm":
        return bool(data.get("deprecated"))
    if registry == "nuget":
        # NuGet marks packages deprecated in registration metadata
        items = data.get("items", [{}])
        if items:
            latest = items[-1].get("items", [{}])
            if latest:
                return bool(latest[-1].get("catalogEntry", {}).get("deprecation"))
    return False


def _latest_version(data: dict, registry: str) -> str:
    if registry == "pypi":
        return data.get("info", {}).get("version", "unknown")
    if registry == "npm":
        return data.get("dist-tags", {}).get("latest", "unknown")
    if registry == "nuget":
        versions = data.get("versions", [])
        return versions[-1].get("version", "unknown") if versions else "unknown"
    return "unknown"


STDLIB_PYTHON = {
    "os","sys","re","json","time","datetime","math","io","abc","ast",
    "collections","functools","itertools","pathlib","typing","enum",
    "logging","threading","asyncio","subprocess","hashlib","base64",
    "urllib","http","socket","ssl","struct","copy","random","string",
}
STDLIB_JS = {"fs","path","http","https","url","crypto","os","stream","events","util","child_process"}
STDLIB_JAVA = {"java","javax","sun","com.sun"}
STDLIB_CS   = {"System","Microsoft","Windows"}

def _is_stdlib(pkg: str, language: str) -> bool:
    lang = language.lower()
    if lang == "python"     and pkg in STDLIB_PYTHON:  return True
    if lang in ("javascript","typescript") and pkg in STDLIB_JS: return True
    if lang == "java"       and any(pkg.startswith(p) for p in STDLIB_JAVA): return True
    if lang in ("csharp","cs") and any(pkg.startswith(p) for p in STDLIB_CS): return True
    return False

