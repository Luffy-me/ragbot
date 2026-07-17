"""Generate a sample official-style university PDF for local demos."""

from pathlib import Path

import fitz


PAGES = [
    [
        "UNIVERSITY OF KNOWLEDGE",
        "Official Student Handbook — Academic Year 2025/2026",
        "",
        "1. How to Apply",
        "International students apply online through the Admissions Portal.",
        "Required steps:",
        "- Create an applicant account",
        "- Complete the online application form",
        "- Upload required documents",
        "- Pay the application fee of 50 EUR",
        "Applications for the fall semester open on March 1 and close on June 15.",
        "",
        "2. Required Documents",
        "Applicants must submit:",
        "- Passport copy",
        "- High school diploma or bachelor diploma (certified translation)",
        "- Academic transcript",
        "- Proof of English proficiency (IELTS 6.0 or TOEFL iBT 78)",
        "- Motivation letter",
        "- Proof of financial means",
    ],
    [
        "3. Tuition Fees",
        "Tuition for bachelor programs is 2,500 EUR per semester.",
        "Tuition for master programs is 3,000 EUR per semester.",
        "Tuition must be paid before registration each semester.",
        "",
        "4. Dormitories",
        "The university offers three dormitories:",
        "- North Hall: shared rooms, 120 EUR per month, closest to campus",
        "- River Residence: single rooms, 180 EUR per month, quieter location",
        "- City Loft: shared apartments, 150 EUR per month, near city center",
        "New students should choose North Hall if they want the shortest walk to classes.",
        "",
        "5. Visa Renewal",
        "International students must renew their residence permit 30 days before expiry.",
        "Required documents for visa renewal:",
        "- Valid passport",
        "- Current residence card",
        "- Enrollment certificate",
        "- Proof of accommodation",
        "- Health insurance",
        "- Bank statement covering living costs",
        "Submit the package at the Immigration Office or through the Student Affairs desk.",
    ],
    [
        "6. Academic Calendar",
        "Fall semester begins on September 15.",
        "Spring semester begins on February 10.",
        "Exam periods are held in January and June.",
        "",
        "7. Scholarships",
        "Available scholarships:",
        "- Merit Scholarship: 25% tuition reduction for GPA above 3.5",
        "- International Excellence Award: 1,000 EUR per year",
        "- Need-Based Grant: awarded after financial review",
        "Scholarship applications open on April 1 and close on May 31.",
    ],
]


def main() -> None:
    out = Path(__file__).resolve().parents[2] / "docs" / "samples" / "student_handbook.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for lines in PAGES:
        page = doc.new_page()
        y = 60
        for line in lines:
            page.insert_text((50, y), line, fontsize=11, fontname="helv")
            y += 16
    doc.save(out)
    doc.close()

    # verify extractable text
    check = fitz.open(out)
    text = "".join(p.get_text() for p in check)
    check.close()
    if len(text.strip()) < 100:
        raise RuntimeError("Generated PDF has insufficient extractable text")
    print(f"Wrote {out} ({len(text)} chars, {len(PAGES)} pages)")


if __name__ == "__main__":
    main()
