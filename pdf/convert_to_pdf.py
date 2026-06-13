"""
Founder Dependency Audit™ — PDF Converter
Kaylee-Jane | Version 1.0

Converts the populated HTML report to a professional PDF
using Playwright (Python) with headless Chromium.

No npm install required — uses the system Playwright installation.

Usage:
    python pdf/convert_to_pdf.py
    python pdf/convert_to_pdf.py --input data/report_populated.html --output data/report.pdf

Environment variables (alternative to CLI args):
    SUBMISSION_ID   — used for default output filename
    HTML_INPUT      — path to populated HTML
    PDF_OUTPUT      — path for PDF output
"""

import argparse
import os
import sys
from pathlib import Path


def convert_to_pdf(html_input, pdf_output):
    """
    Convert HTML report to PDF using Playwright headless Chromium.
    """
    from playwright.sync_api import sync_playwright

    html_path = Path(html_input).resolve()
    pdf_path  = Path(pdf_output).resolve()

    if not html_path.exists():
        print(f"ERROR: HTML input not found at {html_path}", file=sys.stderr)
        sys.exit(1)

    # Ensure output directory exists
    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Converting report to PDF...")
    print(f"  Input  : {html_path}")
    print(f"  Output : {pdf_path}")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--font-render-hinting=none"
            ]
        )

        try:
            page = browser.new_page()

            # Set viewport to A4 at 96dpi
            page.set_viewport_size({"width": 794, "height": 1123})

            # Load HTML file
            file_url = f"file://{html_path}"
            page.goto(file_url, wait_until="networkidle", timeout=30000)

            # Wait for fonts
            page.evaluate("document.fonts.ready")

            # Small additional wait for rendering
            page.wait_for_timeout(1500)

            # Generate PDF
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={
                    "top":    "0mm",
                    "bottom": "0mm",
                    "left":   "0mm",
                    "right":  "0mm"
                },
                display_header_footer=False
            )

            # Verify output
            size_kb = round(pdf_path.stat().st_size / 1024)
            print(f"✓ PDF generated successfully")
            print(f"  File size : {size_kb} KB")
            print(f"  Location  : {pdf_path}")

        finally:
            browser.close()


def main():
    parser = argparse.ArgumentParser(
        description="Founder Dependency Audit™ PDF Converter"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=os.environ.get("HTML_INPUT", "data/report_populated.html"),
        help="Path to populated HTML report"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for PDF output"
    )
    args = parser.parse_args()

    # Build default output path if not specified
    if not args.output:
        submission_id = os.environ.get("SUBMISSION_ID", "TEST")
        args.output = f"data/report_FDA_{submission_id}.pdf"

    convert_to_pdf(args.input, args.output)


if __name__ == "__main__":
    main()