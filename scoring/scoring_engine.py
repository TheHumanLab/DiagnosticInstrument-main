"""
Founder Dependency Audit™ — Scoring Engine
Kaylee-Jane | Version 1.0

Takes a JSON payload of 30 question responses and produces
a complete scoring result including dimension scores,
classifications, overall index, profile assignment,
and risk register entries.
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path


# ─────────────────────────────────────────────
# LOAD CONFIGURATION FILES
# ─────────────────────────────────────────────

def load_config():
    """Load all configuration JSON files."""
    base = Path(__file__).parent

    with open(base / "classifications.json") as f:
        classifications = json.load(f)

    with open(base / "profiles.json") as f:
        profiles = json.load(f)

    with open(base / "risk_register.json") as f:
        risk_rules = json.load(f)

    with open(base / "content_library.json") as f:
        content_library = json.load(f)

    with open(Path(__file__).parent.parent / "assessment" / "questions.json") as f:
        questions = json.load(f)

    return classifications, profiles, risk_rules, content_library, questions


# ─────────────────────────────────────────────
# DIMENSION CONFIGURATION
# ─────────────────────────────────────────────

DIMENSIONS = {
    "DA": {
        "name": "Decision Authority",
        "questions": ["q1", "q2", "q3", "q4", "q5", "q6"],
        "weight": 0.25
    },
    "KI": {
        "name": "Knowledge & Intelligence",
        "questions": ["q7", "q8", "q9", "q10", "q11", "q12"],
        "weight": 0.20
    },
    "RA": {
        "name": "Relationship & Authority",
        "questions": ["q13", "q14", "q15", "q16", "q17", "q18"],
        "weight": 0.20
    },
    "OC": {
        "name": "Operational Continuity",
        "questions": ["q19", "q20", "q21", "q22", "q23", "q24"],
        "weight": 0.20
    },
    "LA": {
        "name": "Leadership Architecture",
        "questions": ["q25", "q26", "q27", "q28", "q29", "q30"],
        "weight": 0.15
    }
}


# ─────────────────────────────────────────────
# SCORING FUNCTIONS
# ─────────────────────────────────────────────

def calculate_dimension_scores(responses):
    """
    Calculate raw score, independence %, and dependency score
    for each dimension.

    Dependency Score = 100 - Independence %
    Higher dependency score = more dependent on founder.
    """
    results = {}

    for code, dim in DIMENSIONS.items():
        # Sum the question values for this dimension
        raw = sum(int(responses[q]) for q in dim["questions"])

        # Maximum possible raw score = 6 questions x 4 max value
        max_raw = len(dim["questions"]) * 4

        # Independence percentage (high = more independent)
        independence_pct = round((raw / max_raw) * 100, 1)

        # Dependency score (high = more dependent) — inverted
        dependency_score = round(100 - independence_pct, 1)

        results[code] = {
            "name": dim["name"],
            "raw": raw,
            "max_raw": max_raw,
            "independence_pct": independence_pct,
            "dependency_score": dependency_score,
            "weight": dim["weight"]
        }

    return results


def classify_dimension(dependency_score, classifications):
    """Map a dependency score to a classification tier."""
    for tier in classifications["dimension_tiers"]:
        if tier["min"] <= dependency_score <= tier["max"]:
            return {
                "classification": tier["classification"],
                "code": tier["code"],
                "risk_severity": tier["risk_severity"]
            }

    # Fallback — should never reach here with valid scores
    return {
        "classification": "Unknown",
        "code": "UNKNOWN",
        "risk_severity": None
    }


def calculate_overall_index(dimension_scores):
    """
    Calculate the weighted overall Dependency Index.
    Each dimension's dependency score is multiplied by its weight.
    """
    overall = sum(
        dim["dependency_score"] * dim["weight"]
        for dim in dimension_scores.values()
    )
    return round(overall, 1)


def classify_overall(overall_index, classifications):
    """Map the overall index to a classification tier."""
    for tier in classifications["overall_tiers"]:
        if tier["min"] <= overall_index <= tier["max"]:
            return {
                "classification": tier["classification"],
                "code": tier["code"],
                "summary": tier["summary"]
            }

    return {
        "classification": "Unknown",
        "code": "UNKNOWN",
        "summary": ""
    }


# ─────────────────────────────────────────────
# PROFILE ASSIGNMENT
# ─────────────────────────────────────────────

def assign_profile(dimension_scores, overall_index, profiles):
    """
    Assign a Founder Dependency Profile based on overall index
    and dimensional pattern. Rules are evaluated from Profile 5
    (most severe) to Profile 1 (most independent).
    """

    da = dimension_scores["DA"]["dependency_score"]
    ki = dimension_scores["KI"]["dependency_score"]
    ra = dimension_scores["RA"]["dependency_score"]
    oc = dimension_scores["OC"]["dependency_score"]
    la = dimension_scores["LA"]["dependency_score"]

    # Count dimensions scoring High (60-79) or Critical (80-100)
    high_critical_count = sum(
        1 for score in [da, ki, ra, oc, la] if score >= 60
    )

    # Count dimensions (excluding DA) scoring High or Critical
    other_dims_high_critical = sum(
        1 for score in [ki, ra, oc, la] if score >= 60
    )

    # ── Profile 5: The Load-Bearing Founder ──
    if overall_index >= 80 or high_critical_count >= 4:
        return 5

    # ── Profile 4: The Central Founder ──
    # Tiebreaker: DA and RA both High/Critical but OC is Moderate or below
    da_ra_high = da >= 60 and ra >= 60
    oc_moderate_or_below = oc < 60

    if overall_index >= 66:
        return 4

    if da >= 60 and other_dims_high_critical >= 2:
        return 4

    if da_ra_high and oc_moderate_or_below:
        return 4

    # ── Profile 3: The Operational Founder ──
    # Founder has stepped back from strategic decisions
    # but remains operationally embedded
    oc_or_la_high = oc >= 60 or la >= 60
    da_below_high = da < 60

    if 46 <= overall_index <= 65 and oc_or_la_high and da_below_high:
        return 3

    # ── Profile 2: The Transitional Founder ──
    if 26 <= overall_index <= 45 and high_critical_count <= 2:
        return 2

    # ── Profile 1: The Structural Founder ──
    if overall_index < 26 and high_critical_count == 0:
        return 1

    # ── Fallback: assign based on overall index alone ──
    if overall_index >= 66:
        return 4
    elif overall_index >= 46:
        return 3
    elif overall_index >= 26:
        return 2
    else:
        return 1


# ─────────────────────────────────────────────
# RISK REGISTER GENERATION
# ─────────────────────────────────────────────

def generate_risk_register(dimension_scores, risk_rules):
    """
    Generate Structural Risk Register entries based on
    dimension classifications. Only Critical, High, and
    Moderate classifications generate entries.
    """
    risks = []
    ref_counter = 1

    # Process dimensions in a defined order for consistent output
    dimension_order = ["DA", "KI", "RA", "OC", "LA"]

    for code in dimension_order:
        dim = dimension_scores[code]
        severity_code = dim.get("classification_code")

        # Only generate entries for Critical, High, Moderate
        if severity_code not in ["CRITICAL", "HIGH", "MODERATE"]:
            continue

        dim_rules = risk_rules["dimensions"].get(code, {})
        entry = dim_rules.get(severity_code)

        if entry:
            risks.append({
                "ref": f"SR-0{ref_counter}",
                "dimension_code": code,
                "dimension_name": dim["name"],
                "description": entry["description"],
                "severity": entry["severity"],
                "structural_condition": entry["structural_condition"]
            })
            ref_counter += 1

    return risks


# ─────────────────────────────────────────────
# CONTENT SELECTION
# ─────────────────────────────────────────────

def select_content(dimension_scores, content_library):
    """
    Select the appropriate pre-written content for each dimension
    based on its classification code.
    """
    content = {}

    for code, dim in dimension_scores.items():
        classification_code = dim.get("classification_code", "MODERATE")
        dim_content = content_library["dimensions"].get(code, {})
        tier_content = dim_content.get(classification_code, {})

        content[code] = {
            "finding": tier_content.get("finding", ""),
            "implication": tier_content.get("implication", ""),
            "structural_cost": tier_content.get("structural_cost", ""),
            "risk": tier_content.get("risk", ""),
            "priority": tier_content.get("priority", "")
        }

    return content


# ─────────────────────────────────────────────
# ACTION FRAMEWORK GENERATION
# ─────────────────────────────────────────────

def generate_action_framework(dimension_scores, overall_classification_code, profile_number):
    """
    Generate the three-horizon action framework based on
    the overall classification and dimensional findings.
    Selects the most critical dimensions for immediate action.
    """

    # Sort dimensions by dependency score (highest first)
    sorted_dims = sorted(
        dimension_scores.items(),
        key=lambda x: x[1]["dependency_score"],
        reverse=True
    )

    # Immediate actions — top 3 highest dependency dimensions
    immediate = []
    medium_term = []
    long_term = []

    immediate_actions = {
        "DA": "Design and implement a decision rights framework that defines which decisions can be made at each structural level without escalation.",
        "KI": "Initiate a knowledge capture programme beginning with client knowledge and operational processes — the two domains with the highest immediate commercial risk.",
        "RA": "Introduce leadership team members into the organisation's most significant client and partner relationships with a structured transition plan.",
        "OC": "Design a formal operational continuity structure covering financial authorities, decision escalation protocols, and leadership continuity arrangements.",
        "LA": "Define the roles, authorities, and accountabilities of the leadership layer as a deliberate design exercise."
    }

    medium_actions = {
        "DA": "Document authority boundaries for cross-functional and strategically significant decisions. Define escalation thresholds.",
        "KI": "Complete documentation of strategic context, institutional reasoning, and client relationship history.",
        "RA": "Transfer the organisation's highest-value external relationships to institutional ownership with defined timelines.",
        "OC": "Test the operational continuity structure under a planned extended absence before it is required under unplanned conditions.",
        "LA": "Establish a leadership governance structure — meeting architecture, decision protocol, and collective accountability framework."
    }

    long_term_actions = {
        "DA": "Maintain the decision rights framework as a living document. Review it at each significant structural change.",
        "KI": "Establish knowledge architecture as an ongoing governance discipline rather than a periodic documentation exercise.",
        "RA": "Ensure all new significant relationships are institutionalised from the outset rather than allowed to become personally dependent.",
        "OC": "Design the organisation's continuity architecture to scale with its operational complexity.",
        "LA": "Review and update the leadership architecture at each significant change in organisational scale or strategic direction."
    }

    for i, (code, dim) in enumerate(sorted_dims):
        if i < 3 and dim["dependency_score"] >= 40:
            immediate.append({
                "dimension": dim["name"],
                "action": immediate_actions.get(code, "")
            })
        elif i < 5 and dim["dependency_score"] >= 20:
            medium_term.append({
                "dimension": dim["name"],
                "action": medium_actions.get(code, "")
            })

    # Long-term actions based on profile
    if profile_number >= 4:
        long_term = [
            {"action": long_term_actions["DA"]},
            {"action": long_term_actions["LA"]},
            {"action": long_term_actions["RA"]}
        ]
    elif profile_number == 3:
        long_term = [
            {"action": long_term_actions["OC"]},
            {"action": long_term_actions["LA"]},
            {"action": long_term_actions["KI"]}
        ]
    else:
        long_term = [
            {"action": long_term_actions["DA"]},
            {"action": long_term_actions["KI"]},
            {"action": long_term_actions["OC"]}
        ]

    return {
        "immediate": immediate,
        "medium_term": medium_term,
        "long_term": long_term
    }


# ─────────────────────────────────────────────
# MASTER SCORING FUNCTION
# ─────────────────────────────────────────────

def run_scoring(payload):
    """
    Master function. Takes a submission payload and returns
    a complete scoring result ready for report generation.
    """

    # Load all config
    classifications, profiles, risk_rules, content_library, questions = load_config()

    # ── Step 1: Calculate dimension scores ──
    dimension_scores = calculate_dimension_scores(payload["responses"])

    # ── Step 2: Classify each dimension ──
    for code in dimension_scores:
        classification = classify_dimension(
            dimension_scores[code]["dependency_score"],
            classifications
        )
        dimension_scores[code]["classification"] = classification["classification"]
        dimension_scores[code]["classification_code"] = classification["code"]
        dimension_scores[code]["risk_severity"] = classification["risk_severity"]

    # ── Step 3: Calculate overall index ──
    overall_index = calculate_overall_index(dimension_scores)

    # ── Step 4: Classify overall ──
    overall_classification = classify_overall(overall_index, classifications)

    # ── Step 5: Assign profile ──
    profile_number = assign_profile(dimension_scores, overall_index, profiles)
    profile_data = profiles["profiles"][str(profile_number)]

    # ── Step 6: Generate risk register ──
    risk_register = generate_risk_register(dimension_scores, risk_rules)

    # ── Step 7: Select content ──
    content = select_content(dimension_scores, content_library)

    # ── Step 8: Generate action framework ──
    action_framework = generate_action_framework(
        dimension_scores,
        overall_classification["code"],
        profile_number
    )

    # ── Step 9: Assemble final result ──
    result = {
        "submission_id": payload.get("submission_id", "TEST-001"),
        "assessment_date": datetime.now().strftime("%d %B %Y"),
        "respondent": payload.get("respondent", {}),
        "dimension_scores": dimension_scores,
        "overall_index": overall_index,
        "overall_classification": overall_classification["classification"],
        "overall_classification_code": overall_classification["code"],
        "overall_summary": overall_classification["summary"],
        "profile_number": profile_number,
        "profile_name": profile_data["name"],
        "profile_description": profile_data["description"],
        "profile_signature": profile_data["signature"],
        "risk_register": risk_register,
        "content": content,
        "action_framework": action_framework
    }

    return result


# ─────────────────────────────────────────────
# CLI ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Founder Dependency Audit™ Scoring Engine"
    )
    parser.add_argument(
        "--payload",
        type=str,
        required=True,
        help="JSON string containing submission payload"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/scoring_results.json",
        help="Output file path for scoring results"
    )
    args = parser.parse_args()

    # Parse payload
    try:
        payload = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON payload — {e}", file=sys.stderr)
        sys.exit(1)

    # Run scoring
    try:
        result = run_scoring(payload)
    except Exception as e:
        print(f"ERROR: Scoring failed — {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    # Print summary to stdout
    print(f"✓ Scoring complete")
    print(f"  Submission ID : {result['submission_id']}")
    print(f"  Overall Index : {result['overall_index']}%")
    print(f"  Classification: {result['overall_classification']}")
    print(f"  Profile       : {result['profile_number']} — {result['profile_name']}")
    print(f"  Risk entries  : {len(result['risk_register'])}")
    print(f"  Output written: {output_path}")


if __name__ == "__main__":
    main()