"""Build the tool list from skill folders. Does not run the programs."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

EXCLUDED_SCRIPTS = {"build_table.py", "check_formulas.py"}
EXCLUDED_FLAGS = {"--check", "--open"}


def is_output_option(option: str) -> bool:
    """File outputs are --out and --out-coeff. --outer is a radius."""
    return option == "--out" or option.startswith("--out-")


FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
RUN_PATH = re.compile(r'python\s+"([^"]+\.py)"')
FLAG_ROW = re.compile(
    r"^\|\s*`(--[a-zA-Z0-9-]+)`\s*\|.*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
WHEN = re.compile(r"^## When to run\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class Flag:
    option: str
    dest: str
    type_name: str
    required: bool
    help: str
    repeat: bool = False

    @property
    def schema_type(self) -> str:
        if self.repeat:
            return "array"
        if self.type_name == "bool":
            return "boolean"
        if self.type_name == "int":
            return "integer"
        if self.type_name == "float":
            return "number"
        return "string"

    @property
    def cli_name(self) -> str:
        """JSON / CLI key from the flag, even when dest is a Python-safe alias."""
        return self.option[2:].replace("-", "_")


@dataclass
class Tool:
    name: str
    skill: str
    description: str
    script: Path
    flags: list[Flag] = field(default_factory=list)

    def required_options(self) -> list[str]:
        return [flag.option for flag in self.flags if flag.required]


def repo_root_from(start: Path | None = None) -> Path:
    here = start or Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "skills").is_dir() and (candidate / "app").is_dir():
            return candidate
    raise RuntimeError("repository root not found")


def _frontmatter_description(text: str) -> str:
    match = FRONTMATTER.match(text)
    if not match:
        return ""
    body = match.group(1)
    desc = re.search(r"^description:\s*>-\s*\n((?:[ \t].*\n)*)", body, re.MULTILINE)
    if desc:
        lines = [line.strip() for line in desc.group(1).splitlines()]
        return " ".join(line for line in lines if line)
    plain = re.search(r'^description:\s*"(.*)"\s*$', body, re.MULTILINE)
    if plain:
        return plain.group(1).strip()
    one = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
    return one.group(1).strip() if one else ""


def _when_to_run(text: str) -> str:
    match = WHEN.search(text)
    if not match:
        return ""
    return re.sub(r"\n{3,}", "\n\n", match.group(1)).strip()


def _required_flags(text: str) -> set[str]:
    """Schema-required flags are unconditional Required cells only.

    "Required when…", "Required with…", and "Optional; required with…" stay
    optional in MCP so alternate CLI paths remain usable.
    """
    required: set[str] = set()
    for option, cell in FLAG_ROW.findall(text):
        label = cell.strip().lower()
        if label == "required" or label.startswith("required;") or label.startswith("required."):
            required.add(option)
    return required


def _literal(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    raise ValueError("not a string")


def _type_name(keywords: dict[str, ast.AST]) -> tuple[str, bool]:
    action = keywords.get("action")
    if isinstance(action, ast.Constant) and action.value == "store_true":
        return "bool", False
    kind = keywords.get("type")
    type_name = "string"
    if isinstance(kind, ast.Name) and kind.id in {"float", "int", "str"}:
        type_name = {"float": "float", "int": "int", "str": "string"}[kind.id]
    if isinstance(action, ast.Constant) and action.value == "append":
        return type_name, True
    return type_name, False


def _help_text(keywords: dict[str, ast.AST]) -> str:
    node = keywords.get("help")
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def flags_from_script(script: Path, required: set[str]) -> list[Flag]:
    tree = ast.parse(script.read_text(encoding="utf-8"))
    found: list[Flag] = []
    seen: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue
        if not node.args:
            continue
        try:
            option = _literal(node.args[0])
        except ValueError:
            continue
        if not option.startswith("--"):
            continue
        if option in EXCLUDED_FLAGS or is_output_option(option):
            continue
        if option in seen:
            continue
        seen.add(option)
        keywords = {kw.arg: kw.value for kw in node.keywords if kw.arg}
        type_name, repeat = _type_name(keywords)
        dest_node = keywords.get("dest")
        if isinstance(dest_node, ast.Constant) and isinstance(dest_node.value, str):
            dest = dest_node.value
        else:
            dest = option[2:].replace("-", "_")
        found.append(
            Flag(
                option=option,
                dest=dest,
                type_name=type_name,
                required=option in required,
                help=_help_text(keywords),
                repeat=repeat,
            )
        )
    return found


def _script_from_skill(text: str, root: Path) -> Path | None:
    for relative in RUN_PATH.findall(text):
        path = root / relative
        if path.name in EXCLUDED_SCRIPTS:
            continue
        if path.is_file():
            return path
    return None


def load_catalog(root: Path | None = None) -> list[Tool]:
    root = root or repo_root_from()
    tools: list[Tool] = []
    names: set[str] = set()
    for skill_md in sorted((root / "skills").glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        script = _script_from_skill(text, root)
        if script is None:
            continue
        name = script.stem
        if name in names:
            name = f"{name}_{len(names)}"
        names.add(name)
        description = _frontmatter_description(text)
        when = _when_to_run(text)
        parts = [f"Skill: {skill_md.parent.name}."]
        if description:
            parts.append(description)
        if when:
            parts.append(when)
        parts.append(
            "Pass only values the user gave, in the units named on each input. "
            "If the program returns an error about a missing or illegal input, "
            "ask for that input. Do not invent values. Quote the key: value lines."
        )
        tools.append(
            Tool(
                name=name,
                skill=skill_md.parent.name,
                description="\n\n".join(parts),
                script=script,
                flags=flags_from_script(script, _required_flags(text)),
            )
        )
    return tools


def tool_by_name(tools: list[Tool], name: str) -> Tool | None:
    for tool in tools:
        if tool.name == name:
            return tool
    return None
