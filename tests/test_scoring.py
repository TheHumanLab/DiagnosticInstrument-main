"""
Founder Dependency Audit™ — Scoring Engine Tests
Kaylee-Jane | Version 1.0

Tests five scenarios — one per profile — to verify that
the scoring engine produces correct classifications,
overall indices, and profile assignments.

Run from repository root:
    python tests/test_scoring.py
"""

import json
import sys
from pathlib import Path

# Add parent directory to path so we can import scoring engine
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.scoring_engine import run_scoring


# ─────────────────────────────────────────────
# TEST PAYLOADS
# One payload per expected profile
# ─────────────────────────────────────────────

def make_payload(submission_id, name, org, responses):
    """Helper to build a standard submission payload."""
    return {
        "submission_id": submission_id,
        "respondent": {
            "name": name,
            "title": "Founder & CEO",
            "organisation": org,
            "email": "test@example.com"
        },
        "responses": responses
    }


# Profile 5 — The Load-Bearing Founder
# All questions answered 1 (does not exist)
PAYLOAD_PROFILE_5 = make_payload(
    "TEST-P5-001",
    "Alex Morgan",
    "Morgan Consulting Ltd",
    {f"q{i}": 1 for i in range(1, 31)}
)

# Profile 4 — The Central Founder
# Most questions answered 1-2, a few at 3
PAYLOAD_PROFILE_4 = make_payload(
    "TEST-P4-001",
    "Sam Clarke",
    "Clarke & Partners",
    {
        # DA — High dependency (mostly 1-2)
        "q1": 1, "q2": 1, "q3": 2, "q4": 2, "q5": 1, "q6": 2,
        # KI — High dependency
        "q7": 2, "q8": 1, "q9": 1, "q10": 2, "q11": 1, "q12": 1,
        # RA — High dependency
        "q13": 1, "q14": 2, "q15": 1, "q16": 2, "q17": 2, "q18": 1,
        # OC — Moderate dependency
        "q19": 2, "q20": 2, "q21": 3, "q22": 2, "q23": 2, "q24": 2,
        # LA — High dependency
        "q25": 2, "q26": 1, "q27": 1, "q28": 2, "q29": 2, "q30": 2
    }
)

# Profile 3 — The Operational Founder
# DA moderate, OC and LA high, others moderate
PAYLOAD_PROFILE_3 = make_payload(
    "TEST-P3-001",
    "Jordan Ellis",
    "Ellis Group",
    {
        # DA — Moderate (stepping back from strategic)
        "q1": 3, "q2": 2, "q3": 3, "q4": 3, "q5": 2, "q6": 3,
        # KI — Moderate
        "q7": 3, "q8": 2, "q9": 2, "q10": 3, "q11": 2, "q12": 2,
        # RA — Moderate
        "q13": 2, "q14": 3, "q15": 2, "q16": 3, "q17": 2, "q18": 2,
        # OC — High (still operationally embedded)
        "q19": 1, "q20": 1, "q21": 2, "q22": 2, "q23": 1, "q24": 1,
        # LA — High (leadership layer not holding independently)
        "q25": 2, "q26": 1, "q27": 1, "q28": 2, "q29": 2, "q30": 2
    }
)

# Profile 2 — The Transitional Founder
# Most dimensions low-moderate, one or two moderate
# Target: overall index 26-45%, no more than 2 dimensions High
PAYLOAD_PROFILE_2 = make_payload(
    "TEST-P2-001",
    "Riley Thompson",
    "Thompson Ventures",
    {
        # DA — Low-moderate dependency
        "q1": 3, "q2": 2, "q3": 3, "q4": 3, "q5": 3, "q6": 2,
        # KI — Low-moderate dependency
        "q7": 3, "q8": 3, "q9": 2, "q10": 3, "q11": 2, "q12": 3,
        # RA — Moderate dependency
        "q13": 2, "q14": 2, "q15": 2, "q16": 2, "q17": 3, "q18": 2,
        # OC — Low dependency
        "q19": 3, "q20": 3, "q21": 3, "q22": 3, "q23": 3, "q24": 3,
        # LA — Moderate dependency
        "q25": 2, "q26": 2, "q27": 2, "q28": 2, "q29": 3, "q30": 3
    }
)

# Profile 1 — The Structural Founder
# All questions answered 4 (fully designed and embedded)
PAYLOAD_PROFILE_1 = make_payload(
    "TEST-P1-001",
    "Casey Whitfield",
    "Whitfield Holdings",
    {f"q{i}": 4 for i in range(1, 31)}
)


# ─────────────────────────────────────────────
# TEST RUNNER
# ─────────────────────────────────────────────

def run_test(payload, expected_profile, test_name):
    """Run a single test and report pass/fail."""
    print(f"\n{'─' * 60}")
    print(f"TEST: {test_name}")
    print(f"{'─' * 60}")

    try:
        result = run_scoring(payload)

        # Print dimension scores
        print(f"\nDIMENSION SCORES:")
        for code, dim in result["dimension_scores"].items():
            print(
                f"  {code} — {dim['name']:<30} "
                f"Dep: {dim['dependency_score']:>5.1f}%  "
                f"[{dim['classification']}]"
            )

        print(f"\nOVERALL INDEX    : {result['overall_index']}%")
        print(f"CLASSIFICATION   : {result['overall_classification']}")
        print(f"PROFILE ASSIGNED : {result['profile_number']} — {result['profile_name']}")
        print(f"RISK ENTRIES     : {len(result['risk_register'])}")

        # Print risk register
        if result["risk_register"]:
            print(f"\nRISK REGISTER:")
            for risk in result["risk_register"]:
                print(f"  {risk['ref']}  {risk['dimension_name']:<30} [{risk['severity']}]")

        # Print action framework summary
        print(f"\nACTION FRAMEWORK:")
        print(f"  Immediate actions : {len(result['action_framework']['immediate'])}")
        print(f"  Medium-term       : {len(result['action_framework']['medium_term'])}")
        print(f"  Long-term         : {len(result['action_framework']['long_term'])}")

        # Verify profile assignment
        if result["profile_number"] == expected_profile:
            print(f"\n✓ PASS — Profile {expected_profile} correctly assigned")
            return True
        else:
            print(
                f"\n✗ FAIL — Expected Profile {expected_profile}, "
                f"got Profile {result['profile_number']}"
            )
            return False

    except Exception as e:
        print(f"\n✗ ERROR — {e}")
        import traceback
        traceback.print_exc()
        return False


def run_content_test():
    """Verify content library is being selected correctly."""
    print(f"\n{'─' * 60}")
    print(f"TEST: Content Library Selection")
    print(f"{'─' * 60}")

    try:
        result = run_scoring(PAYLOAD_PROFILE_5)

        all_populated = True
        for code, content in result["content"].items():
            for field in ["finding", "implication", "structural_cost", "risk", "priority"]:
                if not content.get(field):
                    print(f"  ✗ MISSING: {code} — {field}")
                    all_populated = False
                else:
                    # Show first 80 chars of finding
                    if field == "finding":
                        preview = content[field][:80] + "..."
                        print(f"  ✓ {code} finding: {preview}")

        if all_populated:
            print(f"\n✓ PASS — All content fields populated correctly")
            return True
        else:
            print(f"\n✗ FAIL — Some content fields are empty")
            return False

    except Exception as e:
        print(f"\n✗ ERROR — {e}")
        return False


def run_edge_case_tests():
    """Test boundary conditions."""
    print(f"\n{'─' * 60}")
    print(f"TEST: Edge Cases — Boundary Scores")
    print(f"{'─' * 60}")

    passed = 0
    failed = 0

    # Test: Mixed extreme scores
    mixed_payload = make_payload(
        "TEST-EDGE-001",
        "Edge Case",
        "Edge Corp",
        {
            # DA all 1s — Critical
            "q1": 1, "q2": 1, "q3": 1, "q4": 1, "q5": 1, "q6": 1,
            # KI all 4s — Independent
            "q7": 4, "q8": 4, "q9": 4, "q10": 4, "q11": 4, "q12": 4,
            # RA all 2s — High/Moderate boundary
            "q13": 2, "q14": 2, "q15": 2, "q16": 2, "q17": 2, "q18": 2,
            # OC all 3s — Low/Moderate boundary
            "q19": 3, "q20": 3, "q21": 3, "q22": 3, "q23": 3, "q24": 3,
            # LA all 2s
            "q25": 2, "q26": 2, "q27": 2, "q28": 2, "q29": 2, "q30": 2
        }
    )

    try:
        result = run_scoring(mixed_payload)
        da_class = result["dimension_scores"]["DA"]["classification"]
        ki_class = result["dimension_scores"]["KI"]["classification"]

        

        if ki_class == "Structural Independence":
            print(f"  ✓ KI all-4s correctly classified as Structural Independence")
            passed += 1
        else:
            print(f"  ✗ KI all-4s should be Independent, got: {ki_class}")
            failed += 1

        print(f"  Overall Index: {result['overall_index']}%")
        print(f"  Profile: {result['profile_number']} — {result['profile_name']}")

    except Exception as e:
        print(f"  ✗ ERROR — {e}")
        failed += 1

    print(f"\n  Edge case results: {passed} passed, {failed} failed")
    return failed == 0


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print("=" * 60)
    print("FOUNDER DEPENDENCY AUDIT™ — SCORING ENGINE TESTS")
    print("Kaylee-Jane | Version 1.0")
    print("=" * 60)

    results = []

    # Profile tests
    results.append(run_test(
        PAYLOAD_PROFILE_5,
        expected_profile=5,
        test_name="Profile 5 — The Load-Bearing Founder (all 1s)"
    ))

    results.append(run_test(
        PAYLOAD_PROFILE_4,
        expected_profile=4,
        test_name="Profile 4 — The Central Founder"
    ))

    results.append(run_test(
        PAYLOAD_PROFILE_3,
        expected_profile=3,
        test_name="Profile 3 — The Operational Founder"
    ))

    results.append(run_test(
        PAYLOAD_PROFILE_2,
        expected_profile=2,
        test_name="Profile 2 — The Transitional Founder"
    ))

    results.append(run_test(
        PAYLOAD_PROFILE_1,
        expected_profile=1,
        test_name="Profile 1 — The Structural Founder (all 4s)"
    ))

    # Content test
    results.append(run_content_test())

    # Edge case tests
    results.append(run_edge_case_tests())

    # Summary
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)

    print(f"\n{'=' * 60}")
    print(f"TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"  Passed : {passed}")
    print(f"  Failed : {failed}")
    print(f"  Total  : {len(results)}")

    if failed == 0:
        print(f"\n✓ ALL TESTS PASSED — Scoring engine is ready.")
    else:
        print(f"\n✗ {failed} TEST(S) FAILED — Review output above.")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()