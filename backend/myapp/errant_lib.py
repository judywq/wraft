"""
ERRANT library wrapper for extracting grammatical edits.

This module provides a wrapper around the ERRANT (Error Annotation) library
for identifying grammatical edits between original and corrected text.
ERRANT is used for surface-level error detection and annotation.
"""

from errant import load

# Load ERRANT annotator for English language
errant_annotator = load("en")


def get_errant_edits(orig_text: str, cor_text: str) -> list[dict]:
    """
    Extract edits between original and corrected text using ERRANT annotator.

    Uses the ERRANT library to identify grammatical edits (errors and corrections)
    between the original and corrected versions of text. Returns a list of
    edit dictionaries with position, text, and error type information.

    Args:
        orig_text: The original text with errors
        cor_text: The corrected version of the text

    Returns:
        list[dict]: List of edit dictionaries, each containing:
            - id: Edit index number
            - start: Start position in original text
            - end: End position in original text
            - highlighted_text: The original text that was changed
            - corrected_text: The corrected text
            - error_type: Type of error (e.g., "SPELL", "GRAMMAR")
    """
    # Parse both texts into ERRANT format
    original_parse = errant_annotator.parse(orig_text)
    corrected_parse = errant_annotator.parse(cor_text)
    # Annotate edits between original and corrected versions
    edit_list = errant_annotator.annotate(original_parse, corrected_parse)
    # Convert ERRANT edit objects to dictionaries
    return [
        {
            "id": edit_index,
            "start": edit_item.o_start,  # Start position in original
            "end": edit_item.o_end,  # End position in original
            "highlighted_text": edit_item.o_str,  # Original text
            "corrected_text": edit_item.c_str,  # Corrected text
            "error_type": edit_item.type,  # Type of error
        }
        for edit_index, edit_item in enumerate(edit_list)
    ]
