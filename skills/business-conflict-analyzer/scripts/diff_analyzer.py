#!/usr/bin/env python3
"""
diff_analyzer.py (Step 1) — Parse git diff into structured changes.

Usage:
    python diff_analyzer.py                          # Uncommitted changes
    python diff_analyzer.py --cached                 # Staged changes
    python diff_analyzer.py --since HEAD~1
    python diff_analyzer.py --lang zh
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from __future__ import annotations

from lang import Translator

@dataclass
class Change:
    type: str          # ADD / MODIFY / DELETE / RENAME
    file: str
    extension: str
    risk_level: str    # P0 / P1 / P2
    symbols: list = field(default_factory=list)
    details: str = ""

@dataclass
class DiffManifest:
    changes: list = field(default_factory=list)
    summary: str = ""
    risk_level: str = "P2"
    counts: dict = field(default_factory=lambda: {"p0": 0, "p1": 0, "p2": 0})
    generated_at: str = ""
    lang: str = "en"

    # Structured summary fields (translated at output time)
    summary_key: str = "diff.summary.no_changes"
    summary_params: dict = field(default_factory=dict)

def run_git_diff(*args: str) -> str:
    
    cmd = ["git", "diff"] + list(args)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        t = Translator()
        print(t.t("error.git_diff_failed", stderr=e.stderr), file=sys.stderr)
        sys.exit(1)

def get_changed_files(target: str = "HEAD") -> list[tuple[str, str]]:
    
    if target == "--cached":
        args = ["--cached", "--name-status"]
    else:
        args = ["--name-status", target]
    raw = run_git_diff(*args).strip()
    if not raw:
        return []
    files = []
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            files.append((parts[0], parts[1]))
    return files

JAVA_SIG_PATTERN = re.compile(
    r'^\s*(public|private|protected|static|final|abstract|synchronized|default)\s+.*'
    r'(class|interface|enum|@interface)\s+\w+|'
    r'(public|private|protected|static|final|abstract|synchronized|default)\s+.*'
    r'(\w+)\s*\(.*\)\s*(\{|throws|$)'
)
FIELD_PATTERN = re.compile(
    r'^\s*(private|public|protected|static|final|transient|volatile)\s+[\w<>,?\[\]]+\s+\w+'
)
ANNOTATION_PATTERN = re.compile(r'^\s*@\w+')
SQL_DDL_PATTERN = re.compile(
    r'(ALTER\s+TABLE|DROP\s+(TABLE|COLUMN|INDEX)|CREATE\s+TABLE|'
    r'MODIFY\s+COLUMN|CHANGE\s+COLUMN|RENAME\s+(TO|COLUMN))',
    re.IGNORECASE
)
YAML_KEY_PATTERN = re.compile(r'^[+-]\s*[\w.-]+:')

_SYM_ADD  = "field_add"   # field_add:name
_SYM_DEL  = "field_del"   # field_del:name
_SYM_MADD = "method_add"
_SYM_MDEL = "method_del"
_SYM_CADD = "class_add"
_SYM_CDEL = "class_del"
_SYM_AADD = "annotation_add"
_SYM_ADEL = "annotation_del"
_SYM_DADD = "decorator_add"
_SYM_DDEL = "decorator_del"
_SYM_IADD = "interface_add"
_SYM_IDEL = "interface_del"
_SYM_TADD = "type_add"
_SYM_EADD = "enum_add"
_SYM_EDEL = "enum_del"
_SYM_CADD2 = "config_add"
_SYM_CDEL2 = "config_del"
_SYM_PADD = "prop_add"
_SYM_PDEL = "prop_del"

def _sym(prefix_add: str, prefix_del: str, is_addition: bool, name: str) -> str:
    
    prefix = prefix_add if is_addition else prefix_del
    return f"{prefix}:{name}"

def _detail_java(added: int, removed: int) -> str:
    return f"java:+{added}/-{removed}"

def _detail_python(added: int, removed: int) -> str:
    return f"python:+{added}/-{removed}"

def _detail_typescript(added: int, removed: int) -> str:
    return f"typescript:+{added}/-{removed}"

def _detail_sql(count: int) -> str:
    return f"sql:{count} DDL"

def _detail_config(count: int) -> str:
    return f"config:{count} changes"

def extract_java_diff(diff_text: str) -> tuple[list[str], str]:
    
    symbols = []
    added = 0
    removed = 0

    for line in diff_text.splitlines():
        stripped = line[1:].strip() if line.startswith(("+", "-")) else ""
        if not stripped or stripped.startswith(("import ", "package ")):
            continue
        is_addition = line.startswith("+")

        if JAVA_SIG_PATTERN.match(stripped):
            match = re.search(r'(class|interface|enum)\s+(\w+)', stripped) or \
                    re.search(r'(?:public|private|protected|static|final|\s)*\s+(\w+)\s*\(', stripped)
            if match:
                name = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                symbols.append(_sym(_SYM_CADD, _SYM_CDEL, is_addition, name))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif FIELD_PATTERN.match(stripped):
            field_match = re.search(r'[\w<>,?\[\]]+\s+(\w+)\s*[;=]', stripped)
            if field_match:
                symbols.append(_sym(_SYM_ADD, _SYM_DEL, is_addition, field_match.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif ANNOTATION_PATTERN.match(stripped):
            symbols.append(_sym(_SYM_AADD, _SYM_ADEL, is_addition, stripped))
            if is_addition:
                added += 1
            else:
                removed += 1

    return symbols, _detail_java(added, removed)

def extract_sql_diff(diff_text: str) -> tuple[list[str], str]:
    
    symbols = []
    for line in diff_text.splitlines():
        stripped = line[1:].strip() if line.startswith(("+", "-")) else ""
        if SQL_DDL_PATTERN.match(stripped):
            symbols.append(f"ddl:{stripped}")
    return symbols, _detail_sql(len(symbols))

def extract_yaml_diff(diff_text: str) -> tuple[list[str], str]:
    
    symbols = []
    for line in diff_text.splitlines():
        if line.startswith("+") and YAML_KEY_PATTERN.match(line):
            key = line[1:].strip().rstrip(":")
            symbols.append(f"config_add:{key}")
        elif line.startswith("-") and YAML_KEY_PATTERN.match(line):
            key = line[1:].strip().rstrip(":")
            symbols.append(f"config_del:{key}")
    return symbols, _detail_config(len(symbols))

def extract_python_diff(diff_text: str) -> tuple[list[str], str]:
    
    symbols = []
    added = 0
    removed = 0

    for line in diff_text.splitlines():
        stripped = line[1:].strip() if line.startswith(("+", "-")) else ""
        if not stripped or stripped.startswith(("import ", "from ", "# ", "\"\"\"")):
            continue
        is_addition = line.startswith("+")

        if re.match(r'^\s*def\s+\w+\s*\(', stripped):
            match = re.search(r'def\s+(\w+)', stripped)
            if match:
                symbols.append(_sym(_SYM_MADD, _SYM_MDEL, is_addition, match.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif re.match(r'^\s*class\s+\w+', stripped):
            match = re.search(r'class\s+(\w+)', stripped)
            if match:
                symbols.append(_sym(_SYM_CADD, _SYM_CDEL, is_addition, match.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif re.match(r'^\s*@\w+', stripped):
            symbols.append(_sym(_SYM_DADD, _SYM_DDEL, is_addition, stripped))
            if is_addition:
                added += 1
            else:
                removed += 1
        elif re.match(r'^\s*self\.\w+\s*[=:]', stripped) or \
             re.match(r'^\s*\w+\s*[=:]\s*(?!.*(?:return|pass|if|for|while|def|class))', stripped):
            match_field = re.search(r'(\w+)\s*[=:]', stripped)
            if match_field and match_field.group(1) not in ("self", "cls", "return", "pass", "if", "else", "for"):
                symbols.append(_sym(_SYM_PADD, _SYM_PDEL, is_addition, match_field.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1

    return symbols, _detail_python(added, removed)

def extract_typescript_diff(diff_text: str) -> tuple[list[str], str]:
    
    symbols = []
    added = 0
    removed = 0

    for line in diff_text.splitlines():
        stripped = line[1:].strip() if line.startswith(("+", "-")) else ""
        if not stripped or stripped.startswith(("import ", "export type", "//", "/*")):
            continue
        is_addition = line.startswith("+")

        if re.match(r'^\s*\w+\??\s*[?:]\s*[\w\[\]|&<>]', stripped) and \
           not stripped.startswith(("interface", "type", "class", "function", "const", "let", "var")):
            match = re.search(r'(\w+)\s*[?:]', stripped)
            if match:
                symbols.append(_sym(_SYM_ADD, _SYM_DEL, is_addition, match.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif re.match(r'^\s*(export\s+)?(interface|type|class|enum|abstract class)\s+', stripped):
            match = re.search(r'(interface|type|class|enum)\s+(\w+)', stripped)
            if match:
                kind = match.group(1)
                name = match.group(2)
                if kind == "interface":
                    symbols.append(_sym(_SYM_IADD, _SYM_IDEL, is_addition, name))
                elif kind == "type":
                    symbols.append(_sym(_SYM_TADD, _SYM_TADD, is_addition, name))  # no "type_del"
                elif kind == "enum":
                    symbols.append(_sym(_SYM_EADD, _SYM_EDEL, is_addition, name))
                else:
                    symbols.append(_sym(_SYM_CADD, _SYM_CDEL, is_addition, name))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif re.match(r'^\s*(public|private|protected|static|async|abstract|readonly|\s)*\w+\s*\(', stripped) or \
             re.match(r'^\s*\w+\s*\(.*\)\s*[:\{]', stripped):
            match = re.search(r'(\w+)\s*\(', stripped)
            if match and match.group(1) not in ("if", "for", "while", "switch", "catch"):
                symbols.append(_sym(_SYM_MADD, _SYM_MDEL, is_addition, match.group(1)))
                if is_addition:
                    added += 1
                else:
                    removed += 1
        elif re.match(r'^\s*@\w+', stripped):
            symbols.append(_sym(_SYM_DADD, _SYM_DDEL, is_addition, stripped))
            if is_addition:
                added += 1
            else:
                removed += 1

    return symbols, _detail_typescript(added, removed)

DELETION_PREFIXES = (
    "field_del:", "method_del:", "class_del:", "annotation_del:",
    "decorator_del:", "interface_del:", "enum_del:", "config_del:",
    "prop_del:", "file_del:",
)

def classify_risk(status: str, extension: str, symbols: list, is_breaking: bool) -> tuple[str, str]:
    
    if status == "D":
        return "P0", "diff.reason.file_deleted"
    if is_breaking:
        return "P0", "diff.reason.breaking"

    p0_exts = {".java", ".kt", ".kts", ".sql", ".ddl"}
    p1_exts = {".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".go",
               ".yml", ".yaml", ".properties", ".xml", ".conf"}

    ext = f".{extension}"
    if ext in p0_exts:
        if extension in ("sql", "ddl") and any("DROP" in s.upper() for s in symbols):
            return "P0", "diff.reason.ddl"
        return "P1", "diff.reason.file_change"
    if ext in p1_exts:
        return "P1", "diff.reason.config_change"
    return "P2", "diff.reason.internal_refactor"

def _has_deletion(symbols: list[str]) -> bool:
    
    return any(s.startswith(DELETION_PREFIXES) for s in symbols)

def _detail_fallback(status: str, filepath: str) -> str:
    
    return f"file_change:{status} {filepath}"

def analyze(target: str = "HEAD", lang: str | None = None) -> DiffManifest:
    """Run analysis and return a DiffManifest.

    Args:
        target: Git diff target ('HEAD', '--cached', or a commit range)
        lang: Language hint for summary generation
    """
    t = Translator(lang)
    manifest = DiffManifest(generated_at=datetime.now().isoformat(), lang=t.lang_for_pipe())

    files = get_changed_files(target)
    if not files:
        manifest.summary_key = "diff.summary.no_changes"
        manifest.summary = t.t("diff.summary.no_changes")
        return manifest

    for status, filepath in files:
        ext = Path(filepath).suffix.lstrip(".") or "unknown"
        diff_text = ""
        if status != "D":
            diff_args = ["--cached"] if target == "--cached" else [target]
            diff_text = run_git_diff(*diff_args, "--", filepath)

        symbols = []
        detail = ""
        is_breaking = False

        if ext == "java":
            symbols, detail = extract_java_diff(diff_text)
            path_lower = filepath.lower()
            if any(kw in path_lower for kw in ["controller", "dto", "vo", "feign", "client", "api"]):
                is_breaking = True
            if _has_deletion(symbols):
                is_breaking = True

        elif ext in ("py", "pyi"):
            symbols, detail = extract_python_diff(diff_text)
            path_lower = filepath.lower()
            if any(kw in path_lower for kw in ["views", "serializers", "routers", "api", "urls", "schemas"]):
                is_breaking = True
            if _has_deletion(symbols):
                is_breaking = True

        elif ext in ("ts", "tsx", "js", "jsx"):
            symbols, detail = extract_typescript_diff(diff_text)
            path_lower = filepath.lower()
            if any(kw in path_lower for kw in ["interfaces", "types", "api", "controllers", "services"]):
                is_breaking = True
            if _has_deletion(symbols):
                is_breaking = True

        elif ext in ("kt", "kts"):
            symbols, detail = extract_java_diff(diff_text)
            path_lower = filepath.lower()
            if any(kw in path_lower for kw in ["controller", "dto", "vo", "feign", "client", "api", "ktor"]):
                is_breaking = True

        elif ext == "go":
            symbols, detail = extract_typescript_diff(diff_text)
            path_lower = filepath.lower()
            if any(kw in path_lower for kw in ["handler", "api", "transport", "endpoint", "delivery"]):
                is_breaking = True

        elif ext in ("sql", "ddl"):
            symbols, detail = extract_sql_diff(diff_text)
            if symbols and any("DROP" in s.upper() for s in symbols):
                is_breaking = True

        elif ext in ("yml", "yaml", "properties", "conf"):
            symbols, detail = extract_yaml_diff(diff_text)

        if not detail:
            detail = _detail_fallback(status, filepath)

        risk_level, risk_reason_key = classify_risk(status, ext, symbols, is_breaking)
        change = Change(
            type=status,
            file=filepath,
            extension=ext,
            risk_level=risk_level,
            symbols=symbols,
            details=detail,
        )
        manifest.changes.append(change)

    # Risk count
    for ch in manifest.changes:
        if ch.risk_level == "P0":
            manifest.counts["p0"] += 1
        elif ch.risk_level == "P1":
            manifest.counts["p1"] += 1
        else:
            manifest.counts["p2"] += 1

    # Summary (structured)
    total = sum(manifest.counts.values())
    if manifest.counts["p0"] > 0:
        manifest.summary_key = "diff.summary.p0"
        manifest.summary_params = {"count": manifest.counts["p0"]}
        manifest.risk_level = "P0"
    elif manifest.counts["p1"] > 0:
        manifest.summary_key = "diff.summary.p1"
        manifest.summary_params = {"count": manifest.counts["p1"]}
        manifest.risk_level = "P1"
    else:
        manifest.summary_key = "diff.summary.p2"
        manifest.summary_params = {"count": total, "files": t.t("common.files")}
        manifest.risk_level = "P2"

    manifest.summary = t.t(manifest.summary_key, **manifest.summary_params)
    return manifest

def main():
    parser = argparse.ArgumentParser(
        description="Extract structured code changes from git diff"
    )
    parser.add_argument("--cached", action="store_true",
                        help="Analyze staged changes")
    parser.add_argument("--since",
                        help="Analyze changes since a commit, e.g. HEAD~1")
    parser.add_argument("--lang", choices=("en", "zh"), default=None,
                        help="Output language (en/zh, auto-detected by default)")
    args = parser.parse_args()

    target = "HEAD"
    if args.cached:
        target = "--cached"
    elif args.since:
        target = args.since

    manifest = analyze(target, lang=args.lang)
    # Serialise with lang tag
    out = asdict(manifest)
    out["lang"] = manifest.lang
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
