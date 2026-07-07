// ATS-friendly DOCX builder — reads JSON Resume from stdin arg or env
// Usage: node build_cv.js path/to/tailored.md  (optional)
const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, AlignmentType, LevelFormat, BorderStyle } = require("docx");

const FONT = "Arial";
const NAVY = "1F3864";
const GREY = "595959";

function heading(text) {
  return new Paragraph({
    spacing: { before: 220, after: 70 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: NAVY, space: 2 } },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, size: 22, color: NAVY, font: FONT })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "b", level: 0 },
    spacing: { after: 30 },
    children: [new TextRun({ text, font: FONT, size: 20 })],
  });
}

async function buildFromMarkdown(mdPath, outPath) {
  const md = fs.readFileSync(mdPath, "utf8");
  const children = [];
  for (const line of md.split("\n")) {
    if (line.startsWith("# ")) {
      children.push(new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: line.slice(2), bold: true, size: 34, color: NAVY, font: FONT })],
      }));
    } else if (line.startsWith("## ")) {
      children.push(heading(line.slice(3)));
    } else if (line.startsWith("- ")) {
      children.push(bullet(line.slice(2)));
    } else if (line.trim()) {
      children.push(new Paragraph({ children: [new TextRun({ text: line, font: FONT, size: 20 })] }));
    }
  }
  const doc = new Document({
    numbering: {
      config: [{
        reference: "b",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT }],
      }],
    },
    sections: [{ children }],
  });
  const buf = await Packer.toBuffer(doc);
  fs.writeFileSync(outPath, buf);
  console.log("Wrote", outPath);
}

const mdPath = process.argv[2] || path.join("output", "tailored_cv_sample.md");
const outPath = process.argv[3] || mdPath.replace(/\.md$/, ".docx");
buildFromMarkdown(mdPath, outPath).catch((e) => { console.error(e); process.exit(1); });
