// build_cv.js — reads master_cv.yml and writes a polished, ATS-friendly A4 CV.
// Usage:  node build_cv.js   (run from the folder containing master_cv.yml)
const fs = require("fs");
const yaml = require("js-yaml");
const {
  Document, Packer, Paragraph, TextRun, AlignmentType,
  LevelFormat, BorderStyle, TabStopType, ExternalHyperlink,
} = require("docx");

const cv = yaml.load(fs.readFileSync("master_cv.yml", "utf8"));

const FONT = "Arial";
const NAVY = "1F3864";
const GREY = "595959";
const A4 = { width: 11906, height: 16838 };
const MARGIN = 1080;                 // 0.75"
const CW = A4.width - MARGIN * 2;    // content width for right-aligned dates

const realYear = (y) => (y && !String(y).includes("[") ? String(y) : "");

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
function roleHead(left, right) {
  const kids = [new TextRun({ text: left, bold: true, size: 21, font: FONT })];
  if (right) kids.push(new TextRun({ text: "\t" + right, size: 20, font: FONT, color: GREY }));
  return new Paragraph({
    tabStops: [{ type: TabStopType.RIGHT, position: CW }],
    spacing: { before: 130, after: 0 },
    children: kids,
  });
}
function sub(text) {
  return new Paragraph({
    spacing: { after: 30 },
    children: [new TextRun({ text, italics: true, size: 19, font: FONT, color: GREY })],
  });
}

// ---- header ----
const c = cv.contact || {};
const children = [
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 20 },
    children: [new TextRun({ text: cv.name, bold: true, size: 34, color: NAVY, font: FONT })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 40 },
    children: [new TextRun({ text: "Data, Analytics & Reporting Professional", size: 21, color: GREY, font: FONT })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 20 },
    children: [new TextRun({
      text: [cv.location, c.phone, c.email].filter(Boolean).join("  •  "),
      size: 18, font: FONT,
    })],
  }),
];

// links line (hyperlinked)
const linkRuns = [];
const addLink = (label, url) => {
  if (linkRuns.length) linkRuns.push(new TextRun({ text: "  •  ", size: 18, font: FONT }));
  linkRuns.push(new ExternalHyperlink({
    link: url.startsWith("http") ? url : "https://" + url,
    children: [new TextRun({ text: label, size: 18, font: FONT, color: "1155CC", underline: {} })],
  }));
};
if (c.github) addLink(c.github, c.github);
if (c.linkedin) addLink(c.linkedin, c.linkedin);
if (linkRuns.length) {
  children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 }, children: linkRuns }));
}

// ---- summary ----
if (cv.headline) {
  children.push(heading("Professional Summary"));
  children.push(new Paragraph({
    spacing: { after: 40 },
    children: [new TextRun({ text: cv.headline.trim().replace(/\s+/g, " "), size: 20, font: FONT })],
  }));
}

// ---- skills (grouped by honest level) ----
const skills = cv.skills || [];
const core = skills.filter((s) => s.level === "core").map((s) => s.name);
const tech = skills.filter((s) => s.level !== "core").map((s) => s.name);
children.push(heading("Core Skills"));
if (core.length) {
  children.push(new Paragraph({
    spacing: { after: 30 },
    children: [
      new TextRun({ text: "Core strengths: ", bold: true, size: 20, font: FONT }),
      new TextRun({ text: core.join(", "), size: 20, font: FONT }),
    ],
  }));
}
if (tech.length) {
  children.push(new Paragraph({
    spacing: { after: 30 },
    children: [
      new TextRun({ text: "Technical skills: ", bold: true, size: 20, font: FONT }),
      new TextRun({ text: tech.join(", "), size: 20, font: FONT }),
    ],
  }));
}

// ---- experience ----
if ((cv.experience || []).length) {
  children.push(heading("Professional Experience"));
  for (const e of cv.experience) {
    const dates = [e.start, e.end].filter(Boolean).join(" – ");
    children.push(roleHead(e.role, dates));
    children.push(sub([e.employer, e.location].filter(Boolean).join("  •  ")));
    for (const b of e.bullets || []) children.push(bullet(b.text));
  }
}

// ---- projects ----
if ((cv.projects || []).length) {
  children.push(heading("Selected Projects"));
  for (const p of cv.projects) {
    children.push(new Paragraph({
      spacing: { before: 120, after: 0 },
      children: [new TextRun({ text: p.name, bold: true, size: 21, font: FONT })],
    }));
    for (const b of p.bullets || []) children.push(bullet(b.text));
  }
}

// ---- education ----
if ((cv.education || []).length) {
  children.push(heading("Education"));
  for (const ed of cv.education) {
    children.push(roleHead(ed.qualification, realYear(ed.year)));
    if (ed.institution) children.push(sub(ed.institution));
  }
}

// ---- certifications ----
if ((cv.certifications || []).length) {
  children.push(heading("Certifications"));
  for (const cert of cv.certifications) children.push(bullet(cert));
}

// ---- assemble ----
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: {
    config: [{
      reference: "b",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 360, hanging: 200 } } },
      }],
    }],
  },
  sections: [{
    properties: { page: { size: A4, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("Christopher_Modina_CV.docx", buf);
  console.log("Wrote Christopher_Modina_CV.docx");
});
