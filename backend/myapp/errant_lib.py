from errant import load

annotator = load("en")


def get_errant_edits(orig_text: str, cor_text: str) -> list[dict]:
    """Process edits between original and corrected text using ERRANT annotator."""
    orig = annotator.parse(orig_text)
    cor = annotator.parse(cor_text)
    edits = annotator.annotate(orig, cor)
    return [
        {
            "id": i,
            "start": e.o_start,
            "end": e.o_end,
            "highlighted_text": e.o_str,
            "corrected_text": e.c_str,
            "error_type": e.type,
        }
        for i, e in enumerate(edits)
    ]
