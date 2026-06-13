/**
 * Founder Dependency Audit™ — PDF Converter
 * Kaylee-Jane | Version 1.0
 *
 * Converts the populated HTML report to a professional PDF
 * using Puppeteer headless Chrome.
 *
 * Usage:
 *   node pdf/convert_to_pdf.js
 *
 * Environment variables:
 *   SUBMISSION_ID   — used for output filename
 *   HTML_INPUT      — path to populated HTML (default: data/report_populated.html)
 *   PDF_OUTPUT      — path for PDF output (default: data/report_FDA_[id].pdf)
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function convertToPDF() {

  // ── Configuration ──
  const submissionId = process.env.SUBMISSION_ID || 'TEST';
  const htmlInput   = process.env.HTML_INPUT
                      || path.resolve(__dirname, '../data/report_populated.html');
  const pdfOutput   = process.env.PDF_OUTPUT
                      || path.resolve(__dirname, `../data/report_FDA_${submissionId}.pdf`);

  // ── Verify input exists ──
  if (!fs.existsSync(htmlInput)) {
    console.error(`ERROR: HTML input not found at ${htmlInput}`);
    process.exit(1);
  }

  console.log(`Converting report to PDF...`);
  console.log(`  Input  : ${htmlInput}`);
  console.log(`  Output : ${pdfOutput}`);

  // ── Launch Puppeteer ──
  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-gpu',
      '--font-render-hinting=none'
    ]
  });

  try {
    const page = await browser.newPage();

    // Set viewport to A4 dimensions at 96dpi
    await page.setViewport({
      width: 794,
      height: 1123,
      deviceScaleFactor: 2
    });

    // Load the HTML file
    // Use file:// protocol for local files
    const fileUrl = `file://${htmlInput}`;
    await page.goto(fileUrl, {
      waitUntil: 'networkidle0',
      timeout: 30000
    });

    // Wait for fonts to load
    await page.evaluateHandle('document.fonts.ready');

    // Additional wait for any remaining rendering
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Generate PDF
    await page.pdf({
      path: pdfOutput,
      format: 'A4',
      printBackground: true,       // Critical — renders dark background
      preferCSSPageSize: false,
      margin: {
        top:    '0mm',
        bottom: '0mm',
        left:   '0mm',
        right:  '0mm'
      },
      displayHeaderFooter: false
    });

    // Verify output
    const stats = fs.statSync(pdfOutput);
    const sizeKB = Math.round(stats.size / 1024);

    console.log(`✓ PDF generated successfully`);
    console.log(`  File size : ${sizeKB} KB`);
    console.log(`  Location  : ${pdfOutput}`);

  } catch (error) {
    console.error(`ERROR: PDF conversion failed — ${error.message}`);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

convertToPDF();