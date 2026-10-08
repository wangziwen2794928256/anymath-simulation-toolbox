"""Check declared prerequisites; never convert missing facts into a recommendation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REFERENCE = Path(__file__).resolve().parents[1] / "references/method-assumptions.json"


def load_rules(path=REFERENCE):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def check_rules(rules, method_ids):
    problems = []
    if not isinstance(rules, dict) or rules.get("schema_version") != 1:
        return ["assumption rules must be a schema_version=1 object"]
    fields = rules.get("fields", {})
    entries = rules.get("methods", {})
    if not isinstance(fields, dict) or not fields or not isinstance(entries, dict):
        return ["assumption fields/methods must be nonempty objects"]
    if any(not isinstance(v, str) or not v.strip() for v in fields.values()):
        problems.append("prerequisite descriptions must be nonempty strings")
    if set(entries) != set(method_ids):
        problems.append("assumption rules must cover exactly the method library ids")
    for mid, entry in entries.items():
        if not isinstance(entry, dict):
            problems.append(f"{mid}: rule must be an object")
            continue
        if not entry.get("requires") or not entry.get("manual_checks"):
            problems.append(f"{mid}: requires/manual_checks must be nonempty")
        requires = entry.get("requires", [])
        manual = entry.get("manual_checks", [])
        if (not isinstance(requires, list) or any(not isinstance(v, str) for v in requires)
                or not isinstance(manual, list) or any(not isinstance(v, str) or not v.strip() for v in manual)):
            problems.append(f"{mid}: requires/manual_checks must be string lists")
            continue
        if len(requires) != len(set(requires)):
            problems.append(f"{mid}: duplicate prerequisites")
        for field in requires:
            if field not in fields:
                problems.append(f"{mid}: unknown prerequisite {field}")
    return problems


def validate_context(context, rules):
    if not isinstance(context, dict) or set(context) - {"schema_version", "facts", "notes"}:
        raise ValueError("context must contain only schema_version, facts and optional notes")
    if type(context.get("schema_version")) is not int or context["schema_version"] != 1:
        raise ValueError("context schema_version must be 1")
    facts = context.get("facts")
    if not isinstance(facts, dict):
        raise ValueError("facts must be an object")
    if set(facts) - set(rules["fields"]):
        raise ValueError(f"unknown fact keys: {sorted(set(facts) - set(rules['fields']))}")
    for field, fact in facts.items():
        if fact is None:
            continue
        if not isinstance(fact, dict) or set(fact) - {"value", "basis"} or "value" not in fact:
            raise ValueError(f"{field}: use null or an object with value/basis")
        value = fact["value"]
        if value is not None and type(value) is not bool:
            raise ValueError(f"{field}: value must be true/false/null, not a string or number")
        if value is not None and (not isinstance(fact.get("basis"), str) or not fact["basis"].strip()):
            raise ValueError(f"{field}: declared facts need a nonempty basis")
    return facts


def assess(methods, context, rules=None):
    rules = rules or load_rules()
    facts = validate_context(context, rules)
    result = []
    for method in methods:
        entry = rules["methods"][method["id"]]
        checks = []
        for field in entry["requires"]:
            fact = facts.get(field)
            value = fact.get("value") if isinstance(fact, dict) else None
            state = "pending" if value is None else "met" if value else "conflict"
            checks.append({"field": field, "requirement": rules["fields"][field],
                           "state": state, "declared_value": value,
                           "basis": fact.get("basis", "") if isinstance(fact, dict) else ""})
        status = ("conflict" if any(c["state"] == "conflict" for c in checks)
                  else "pending" if any(c["state"] == "pending" for c in checks)
                  else "compatible_with_declared_facts")
        result.append({"id": method["id"], "name": method["name"], "status": status,
                       "checks": checks, "manual_checks": entry["manual_checks"],
                       "next_step": "resolve conflicts" if status == "conflict" else
                       "supply missing facts" if status == "pending" else
                       "run minimal validation; compatibility is not effectiveness"})
    return result


def report(methods, context, rules=None):
    rules = rules or load_rules()
    canonical = json.dumps(context, ensure_ascii=False, sort_keys=True).encode("utf-8")
    rule_bytes = json.dumps(rules, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {"schema_version": 1,
            "scope": "Prerequisites of the specified formulation/implementation; not a proof of validity or performance",
            "context_sha256": hashlib.sha256(canonical).hexdigest(),
            "rules_sha256": hashlib.sha256(rule_bytes).hexdigest(),
            "candidate_definitions_sha256": hashlib.sha256(
                json.dumps(methods, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
            "methods": assess(methods, context, rules)}


def render(assessment):
    labels = {"conflict": "前提冲突", "pending": "信息待补",
              "compatible_with_declared_facts": "与已声明条件相容（待实验）"}
    lines = ["【题目条件检查：声明相容 ≠ 模型有效 ≠ 方法更优】"]
    for item in assessment["methods"]:
        lines.append(f"  {item['id']}: {labels[item['status']]}")
        for check in item["checks"]:
            lines.append(f"    {check['state']}: {check['requirement']}；依据={check['basis'] or '未提供'}")
        lines.append("    待实证核查：" + "；".join(item["manual_checks"]))
    return "\n".join(lines)
