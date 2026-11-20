"""Rules extracted from the two reference PDFs in Reference_materials/.

* "Tech Astro Analysis pages 1 to 265 all final new printout cq 10 2 2020.pdf"
  (cited as TA, with the PDF page number; the book's own printed page number
  is given in brackets where it differs).
* "KD Final PPT PDF 2026.pdf" (cited as KD, with the PDF page / slide number).

Both are image-only scans. Every rule here was read from the page image, and
the transcription notes live in build/pdfref/REFERENCE_PDF_RULES.md.

This package is deliberately separate from finastro/rules. Those rules port
the 2026 source document and are pinned by the census tests; these come from
two other documents by the same school, are evaluated on their own engine
(engine.py) and are merged into the New York calendar by
tools/build_pdf_calendar.py without changing a single existing row.
"""
