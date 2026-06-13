"""
Founder Dependency Audit™ — Report Generator
Kaylee-Jane | Version 1.0

Reads scoring_results.json and populates template.html
with real client data, producing a complete HTML report
ready for PDF conversion.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────
# CSS CLASS MAPPING
# Maps classification codes to CSS classes
# ─────────────────────────────────────────────

CLASSIFICATION_CSS = {
    "CRITICAL":    "class-critical",
    "HIGH":        "class-high",
    "MODERATE":    "class-moderate",
    "LOW":         "class-low",
    "INDEPENDENT": "class-independent"
}

SEVERITY_CSS = {
    "CRITICAL": "sev-critical",
    "HIGH":     "sev-high",
    "MODERATE": "sev-moderate"
}


# ─────────────────────────────────────────────
# SUMMARY GENERATION
# Builds the executive summary paragraphs
# from scoring results
# ─────────────────────────────────────────────

def generate_summary_primary_finding(scoring_results):
    """
    Identifies the highest dependency dimension and
    generates the primary finding sentence for the
    executive summary highlight block.
    """
    dims = scoring_results["dimension_scores"]

    # Find highest dependency dimension
    highest = max(dims.items(), key=lambda x: x[1]["dependency_score"])
    code = highest[0]
    dim = highest[1]

    name = dim["name"]
    classification = dim["classification"]
    score = dim["dependency_score"]

    sentences = {
        "DA": f"The highest architectural concentration is recorded in Decision Authority, "
              f"where the assessment identifies a {classification} classification at {score}%. "
              f"The organisation's decision architecture does not currently function without founder involvement.",

        "KI": f"The most significant knowledge concentration is recorded in Knowledge & Intelligence, "
              f"where the assessment identifies a {classification} classification at {score}%. "
              f"Critical organisational knowledge is personally held and has not been structurally captured.",

        "RA": f"The most acute relationship concentration is recorded in Relationship & Authority, "
              f"where the assessment identifies a {classification} classification at {score}%. "
              f"The organisation's external authority and commercial credibility are personally held by the founder.",

        "OC": f"The most significant continuity risk is recorded in Operational Continuity, "
              f"where the assessment identifies a {classification} classification at {score}%. "
              f"The organisation has not been designed to function in the founder's absence.",

        "LA": f"The most significant architectural gap is recorded in Leadership Architecture, "
              f"where the assessment identifies a {classification} classification at {score}%. "
              f"No functioning leadership layer exists with the structural authority to hold the organisation independently."
    }

    return sentences.get(code, f"The highest dependency is recorded in {name} at {score}%.")


def generate_summary_priority_action(scoring_results):
    """
    Generates the priority action sentence for the
    executive summary based on profile and top dimension.
    """
    profile = scoring_results["profile_number"]
    dims = scoring_results["dimension_scores"]
    highest = max(dims.items(), key=lambda x: x[1]["dependency_score"])
    code = highest[0]

    priority_sentences = {
        "DA": "The immediate structural priority is the design and implementation of a decision rights "
              "framework that distributes authority to the appropriate structural level across all "
              "operational, commercial, and strategic domains.",

        "KI": "The immediate structural priority is the initiation of a knowledge capture programme "
              "beginning with client knowledge and operational processes — the two domains where "
              "knowledge loss creates the most acute and most immediate commercial risk.",

        "RA": "The immediate structural priority is the deliberate transfer of key external relationships "
              "to the organisation as an entity, with a structured transition plan and defined timeline "
              "for each significant client and partner relationship.",

        "OC": "The immediate structural priority is the design and implementation of an operational "
              "continuity structure covering financial authorities, decision escalation protocols, "
              "and leadership continuity arrangements.",

        "LA": "The immediate structural priority is the design of a formal leadership architecture — "
              "defining the roles, authorities, accountabilities, and governance structure of the "
              "leadership layer as a deliberate design exercise."
    }

    return priority_sentences.get(code, "The immediate priority is to address the highest-scoring structural dimension.")


# ─────────────────────────────────────────────
# HTML FRAGMENT BUILDERS
# Build the dynamic HTML sections
# ─────────────────────────────────────────────

def build_risk_register_rows(risk_register):
    """Build HTML table rows for the risk register."""
    if not risk_register:
        return """
        <tr>
          <td colspan="4" style="color: #7a9a7a; font-size: 8pt; padding: 4mm 0; text-align: center;">
            No structural risks identified at reportable severity.
          </td>
        </tr>"""

    rows = ""
    for risk in risk_register:
        severity_css = SEVERITY_CSS.get(risk["severity"], "")
        rows += f"""
        <tr>
          <td class="risk-ref">{risk['ref']}</td>
          <td class="risk-dimension">{risk['dimension_name']}</td>
          <td class="risk-description">{risk['description']}</td>
          <td class="risk-severity {severity_css}">{risk['severity']}</td>
        </tr>"""

    return rows


def build_action_items(actions, show_dimension=True):
    """Build HTML list items for the action framework."""
    if not actions:
        return """
        <li>
          <span class="action-number">—</span>
          <span class="action-text" style="color: #a09a8e;">
            No immediate actions required in this horizon.
          </span>
        </li>"""

    items = ""
    for i, action in enumerate(actions, 1):
        dimension_html = ""
        if show_dimension and action.get("dimension"):
            dimension_html = f'<span class="action-dimension">{action["dimension"]}</span>'

        items += f"""
        <li>
          <span class="action-number">{i}</span>
          {dimension_html}
          <span class="action-text">{action.get('action', '')}</span>
        </li>"""

    return items


def build_long_action_items(actions):
    """Build HTML list items for long-term actions (no dimension label)."""
    if not actions:
        return """
        <li>
          <span class="action-number">—</span>
          <span class="action-text" style="color: #a09a8e;">
            No long-term objectives specified.
          </span>
        </li>"""

    items = ""
    for i, action in enumerate(actions, 1):
        items += f"""
        <li>
          <span class="action-number">{i}</span>
          <span class="action-text">{action.get('action', '')}</span>
        </li>"""

    return items


def build_profile_signature_items(signature_list):
    """Build HTML list items for the profile signature."""
    items = ""
    for item in signature_list:
        items += f"<li>{item}</li>"
    return items


# ─────────────────────────────────────────────
# TEMPLATE POPULATION
# ─────────────────────────────────────────────

def populate_template(scoring_results, template_path):
    """
    Read the HTML template and replace all {{ variables }}
    with real data from scoring results.
    Returns the populated HTML string.
    """

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    r = scoring_results
    dims = r["dimension_scores"]
    content = r["content"]

    # ── Respondent details ──
    html = html.replace("{{ client_name }}", r["respondent"].get("name", ""))
    html = html.replace("{{ client_title }}", r["respondent"].get("title", ""))
    html = html.replace("{{ organisation_name }}", r["respondent"].get("organisation", ""))
    html = html.replace("{{ assessment_date }}", r["assessment_date"])
    html = html.replace("{{ submission_id }}", r["submission_id"])

    # ── Overall scores ──
    html = html.replace("{{ overall_index }}", str(r["overall_index"]))
    html = html.replace("{{ overall_classification }}", r["overall_classification"])
    html = html.replace("{{ overall_summary }}", r["overall_summary"])

    # ── Executive summary ──
    html = html.replace(
        "{{ summary_primary_finding }}",
        generate_summary_primary_finding(r)
    )
    html = html.replace(
        "{{ summary_priority_action }}",
        generate_summary_priority_action(r)
    )

    # ── Profile ──
    html = html.replace("{{ profile_number }}", str(r["profile_number"]))
    html = html.replace("{{ profile_name }}", r["profile_name"])
    html = html.replace("{{ profile_description }}", r["profile_description"])
    html = html.replace(
        "{{ profile_signature_items }}",
        build_profile_signature_items(r["profile_signature"])
    )

    # ── Dimension scores and classifications ──
    dimension_map = {
        "DA": "da",
        "KI": "ki",
        "RA": "ra",
        "OC": "oc",
        "LA": "la"
    }

    for code, prefix in dimension_map.items():
        dim = dims[code]
        dim_content = content[code]
        css_class = CLASSIFICATION_CSS.get(dim["classification_code"], "class-moderate")

        html = html.replace(f"{{{{ {prefix}_score }}}}", str(dim["dependency_score"]))
        html = html.replace(f"{{{{ {prefix}_classification }}}}", dim["classification"])
        html = html.replace(f"{{{{ {prefix}_class_css }}}}", css_class)
        html = html.replace(f"{{{{ {prefix}_finding }}}}", dim_content["finding"])
        html = html.replace(f"{{{{ {prefix}_implication }}}}", dim_content["implication"])
        html = html.replace(f"{{{{ {prefix}_structural_cost }}}}", dim_content["structural_cost"])
        html = html.replace(f"{{{{ {prefix}_risk }}}}", dim_content["risk"])
        html = html.replace(f"{{{{ {prefix}_priority }}}}", dim_content["priority"])

    # ── Risk register ──
    html = html.replace(
        "{{ risk_register_rows }}",
        build_risk_register_rows(r["risk_register"])
    )

    # ── Action framework ──
    html = html.replace(
        "{{ immediate_action_items }}",
        build_action_items(r["action_framework"]["immediate"], show_dimension=True)
    )
    html = html.replace(
        "{{ medium_action_items }}",
        build_action_items(r["action_framework"]["medium_term"], show_dimension=True)
    )
    html = html.replace(
        "{{ long_action_items }}",
        build_long_action_items(r["action_framework"]["long_term"])
    )

    return html


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Founder Dependency Audit™ Report Generator"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/scoring_results.json",
        help="Path to scoring results JSON"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="report/template.html",
        help="Path to HTML report template"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/report_populated.html",
        help="Output path for populated HTML report"
    )
    args = parser.parse_args()

    # Load scoring results
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Scoring results not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        scoring_results = json.load(f)

    # Load and populate template
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"ERROR: Template not found at {template_path}", file=sys.stderr)
        sys.exit(1)

    try:
        populated_html = populate_template(scoring_results, template_path)
    except Exception as e:
        print(f"ERROR: Report generation failed — {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(populated_html)

    print(f"✓ Report generated")
    print(f"  Client     : {scoring_results['respondent'].get('name', 'Unknown')}")
    print(f"  Org        : {scoring_results['respondent'].get('organisation', 'Unknown')}")
    print(f"  Profile    : {scoring_results['profile_number']} — {scoring_results['profile_name']}")
    print(f"  Output     : {output_path}")


if __name__ == "__main__":
    main()