"""Arm C validators: architectural enforcement of role boundaries.

Pure-python validators (no jsonschema dependency -- it is not installed on the
target interpreter).  Each validator implements the JSON-Schema semantics we
actually need:

  * required fields present
  * exact types
  * additionalProperties: false
  * enum constraints
  * "no answer field" / "no final answer leak" constraints

Every failure returns a stable machine-readable ``violated_constraint`` string
so the manipulation check in the paper can be tabulated from the JSONL.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Declarative schema documents.  Kept as data so they are hashed into the
# config/prompt version hash and can be printed in the paper appendix.
# --------------------------------------------------------------------------

PLANNER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "subproblems": {"type": "array", "items": {"type": "string"}},
        "strategy": {"type": "array", "items": {"type": "string"}},
        "dependencies": {"type": "array", "items": {"type": "string"}},
        "required_quantities": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["subproblems", "strategy", "dependencies", "required_quantities"],
    "additionalProperties": False,
    # NOTE: there is deliberately NO answer field.
}

EXECUTOR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "derivation": {"type": "string"},
        "answer": {"type": "string"},
    },
    "required": ["derivation", "answer"],
    "additionalProperties": False,
}

REVIEWER_VERDICTS = ["accept", "revise_plan", "revise_execution"]

REVIEWER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": list(REVIEWER_VERDICTS)},
        "target": {"type": "string"},
        "critique": {"type": "string"},
    },
    "required": ["verdict", "target", "critique"],
    "additionalProperties": False,
    # NOTE: there is deliberately NO answer field.  "accept" promotes the
    # executor's current answer verbatim BY REFERENCE (see runner.py).
}

SCHEMAS: Dict[str, Dict[str, Any]] = {
    "planner": PLANNER_SCHEMA,
    "executor": EXECUTOR_SCHEMA,
    "reviewer": REVIEWER_SCHEMA,
}

# --------------------------------------------------------------------------
# Final-answer leak detection
# --------------------------------------------------------------------------

_BOXED_RE = re.compile(r"\\boxed\s*\{")
_FINAL_ANSWER_RE = re.compile(r"final\s*answer", re.IGNORECASE)
# Loose "the answer is 42" style leak.
_ANSWER_IS_RE = re.compile(r"\b(the\s+)?answer\s+is\b", re.IGNORECASE)


def find_answer_leak(text: str) -> Optional[str]:
    """Return the name of the violated no-answer constraint, or None."""
    if not text:
        return None
    if _BOXED_RE.search(text):
        return "answer_leak:boxed"
    if _FINAL_ANSWER_RE.search(text):
        return "answer_leak:final_answer_phrase"
    if _ANSWER_IS_RE.search(text):
        return "answer_leak:answer_is_phrase"
    return None


@dataclass
class ValidationResult:
    ok: bool
    violated_constraint: Optional[str] = None
    detail: str = ""
    obj: Optional[Dict[str, Any]] = None
    # Every constraint that failed (the first is reported as
    # ``violated_constraint``; the full list is logged for the paper).
    all_violations: List[str] = field(default_factory=list)

    def as_log(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "violated_constraint": self.violated_constraint,
            "detail": self.detail[:500],
            "all_violations": self.all_violations,
        }


# --------------------------------------------------------------------------
# JSON extraction
# --------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def _balanced_object(text: str) -> Optional[str]:
    """Return the first balanced {...} block, respecting strings/escapes."""
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def extract_json_object(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Parse a JSON object out of raw model text.

    Returns (obj, error).  Accepts bare JSON, fenced JSON, or JSON embedded in
    prose.  We are permissive about *delivery* and strict about *content*: the
    schema check below is what enforces the architecture.
    """
    if text is None:
        return None, "empty output"
    stripped = text.strip()
    if not stripped:
        return None, "empty output"

    candidates: List[str] = []
    m = _FENCE_RE.search(stripped)
    if m:
        candidates.append(m.group(1).strip())
    candidates.append(stripped)
    bal = _balanced_object(stripped)
    if bal:
        candidates.append(bal)

    last_err = "no JSON object found"
    for cand in candidates:
        if not cand:
            continue
        try:
            obj = json.loads(cand)
        except Exception as exc:  # noqa: BLE001
            last_err = "{}: {}".format(type(exc).__name__, exc)
            continue
        if isinstance(obj, dict):
            return obj, None
        last_err = "top-level JSON is {}, not an object".format(type(obj).__name__)
    return None, last_err


# --------------------------------------------------------------------------
# Core validator
# --------------------------------------------------------------------------


def _check_schema(obj: Dict[str, Any], schema: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return [(violated_constraint, detail)]; empty means valid."""
    out: List[Tuple[str, str]] = []
    props = schema.get("properties", {})

    for key in schema.get("required", []):
        if key not in obj:
            out.append(("missing_field:{}".format(key), "required field absent"))

    if schema.get("additionalProperties") is False:
        for key in obj:
            if key not in props:
                out.append(
                    ("additional_property:{}".format(key), "additionalProperties is false")
                )

    for key, spec in props.items():
        if key not in obj:
            continue
        val = obj[key]
        want = spec.get("type")
        if want == "string":
            if not isinstance(val, str):
                out.append(
                    ("wrong_type:{}".format(key), "expected string, got {}".format(type(val).__name__))
                )
                continue
            if not val.strip():
                out.append(("empty_string:{}".format(key), "field is blank"))
            enum = spec.get("enum")
            if enum is not None and val not in enum:
                out.append(
                    ("enum_violation:{}".format(key), "{!r} not in {}".format(val, enum))
                )
        elif want == "array":
            if not isinstance(val, list):
                out.append(
                    ("wrong_type:{}".format(key), "expected array, got {}".format(type(val).__name__))
                )
                continue
            item_t = spec.get("items", {}).get("type")
            for idx, item in enumerate(val):
                if item_t == "string" and not isinstance(item, str):
                    out.append(
                        (
                            "wrong_item_type:{}[{}]".format(key, idx),
                            "expected string, got {}".format(type(item).__name__),
                        )
                    )
            if len(val) == 0:
                out.append(("empty_list:{}".format(key), "array must be non-empty"))
    return out


def validate_role_output(
    role: str, raw_text: str, forbid_answer: bool = False
) -> ValidationResult:
    """Validate one Arm-C role output.

    ``forbid_answer`` additionally rejects any raw output that carries a final
    answer (``\\boxed``/"Final Answer"/"the answer is").  Used for the planner
    and the reviewer, which must not own the submission text.
    """
    schema = SCHEMAS[role]
    violations: List[Tuple[str, str]] = []

    # Constraint 1: the no-answer constraint is checked against the RAW text,
    # not only the parsed object, so prose smuggled outside the JSON is caught.
    if forbid_answer:
        leak = find_answer_leak(raw_text)
        if leak is not None:
            violations.append((leak, "role {} may not author a final answer".format(role)))

    obj, err = extract_json_object(raw_text)
    if obj is None:
        violations.append(("json_parse_error", err or "unparseable"))
        first = violations[0]
        return ValidationResult(
            ok=False,
            violated_constraint=first[0],
            detail=first[1],
            obj=None,
            all_violations=[v[0] for v in violations],
        )

    violations.extend(_check_schema(obj, schema))

    if forbid_answer:
        # Constraint 1b: also scan the parsed string content.
        for key, val in obj.items():
            texts: List[str] = []
            if isinstance(val, str):
                texts = [val]
            elif isinstance(val, list):
                texts = [v for v in val if isinstance(v, str)]
            for t in texts:
                leak = find_answer_leak(t)
                if leak is not None:
                    violations.append(
                        ("{}@{}".format(leak, key), "no-answer constraint violated inside field")
                    )
                    break

    if violations:
        first = violations[0]
        return ValidationResult(
            ok=False,
            violated_constraint=first[0],
            detail=first[1],
            obj=obj,
            all_violations=[v[0] for v in violations],
        )
    return ValidationResult(ok=True, obj=obj, detail="valid", all_violations=[])


def validate_planner(raw_text: str) -> ValidationResult:
    return validate_role_output("planner", raw_text, forbid_answer=True)


def validate_executor(raw_text: str) -> ValidationResult:
    return validate_role_output("executor", raw_text, forbid_answer=False)


def validate_reviewer(raw_text: str) -> ValidationResult:
    return validate_role_output("reviewer", raw_text, forbid_answer=True)


VALIDATORS = {
    "planner": validate_planner,
    "executor": validate_executor,
    "reviewer": validate_reviewer,
}


def always_valid(raw_text: str) -> ValidationResult:
    """Arm A / Arm B: no architectural constraint exists, so nothing can fail.

    The code path (validate -> maybe regenerate) is identical across arms; only
    the constraint set differs.  This is the manipulated variable.
    """
    return ValidationResult(ok=True, obj=None, detail="no constraint (unconstrained arm)")
