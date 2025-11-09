"""
Utility functions for essay evaluation processing.

This module provides helper functions for text processing, position finding,
tag removal, and post-processing of deep correction data.
"""

from typing import Literal

# Delimiter used to separate paragraphs in formatted essay text
PARAGRAPH_DELIMITER = "\n"


def find_nearest_text_position_word(
    text: str,
    full_text: str,
    start_pos: int | None = None,
) -> int | None:
    """
    Locate the nearest position of the given text in full_text by searching
    around the specified start_pos and stopping when a match is found.

    Searches outward from the start position (both left and right) to find
    the nearest occurrence of the target text. Uses word-based matching to
    handle variations in whitespace.

    Args:
        text: The target text to locate
        full_text: The text to search within
        start_pos: An approximate starting position for the search (word index)
        
    Returns:
        int: The word index position of the nearest occurrence, or None if not found
    """
    if start_pos is None:
        # Default to beginning if no start position provided
        start_pos = 0

    def words_match(word_list, full_word_list):
        """Check if word list matches within full word list."""
        return " ".join(word_list) in " ".join(full_word_list)

    # Split both texts into word lists
    target_words = text.split()
    target_word_count = len(target_words)

    source_words = full_text.split()
    source_word_count = len(source_words)

    # Clamp start_pos to valid range (0 to source_word_count)
    start_pos = max(0, min(source_word_count, start_pos))

    # Search outward from start_pos (bidirectional search)
    left_index, right_index = start_pos, start_pos
    target_length = target_word_count
    source_length = source_word_count

    # Expand search range until match found or boundaries reached
    while left_index >= 0 or right_index < source_length:
        # Check left side (searching backward)
        if left_index >= 0 and words_match(target_words, source_words[left_index : left_index + target_length]):
            return left_index

        # Check right side (searching forward)
        if right_index < source_length and words_match(
            target_words,
            source_words[right_index : right_index + target_length],
        ):
            return right_index

        # Expand search range outward
        left_index -= 1
        right_index += 1

    # Return None if no match found
    return None


def remove_tag(raw_content: str, end_tag: str) -> str:
    """
    Remove all content before the specified end tag.
    
    Finds the end tag in the content and returns everything after it.
    Used to extract content from XML-like tags (e.g., <essay_analysis>...</essay_analysis>).
    
    Args:
        raw_content: The content that may contain tags
        end_tag: The end tag to search for (e.g., "</essay_analysis>")
        
    Returns:
        str: Content after the end tag, or original content if tag not found
    """
    # Find the position of the end tag
    tag_position = raw_content.find(end_tag)
    if tag_position == -1:
        # Tag not found - return original content
        return raw_content
    # Return content after the end tag
    return raw_content[tag_position + len(end_tag) :]


def post_process_deep(
    essay_data: dict,
    deep_data: dict,
    content_type: Literal["micro", "macro"],
) -> list[dict]:
    """
    Process and format deep correction content from LLM responses.
    
    Takes raw deep correction data from LLM responses and formats it into
    a structured list of comments. For micro corrections, also calculates
    word positions for highlighting. Links comments to their paragraphs.
    
    Args:
        essay_data: Dictionary containing essay data including corrected paragraphs
        deep_data: Dictionary containing raw deep correction data from LLM
        content_type: Either "micro" or "macro" to determine processing logic
        
    Returns:
        list[dict]: List of formatted comment dictionaries, each containing:
            - id: Comment ID
            - paragraph_id: ID of the paragraph this comment refers to
            - comment: The comment text
            - paragraph_text: The full text of the paragraph
            - (for micro only) type, highlighted_text, start, end: Position info
    """
    # Get list of comments from deep correction data
    comment_list = deep_data.get("comments", [])
    processed_comments = []
    # Get corrected paragraphs for linking comments
    corrected_paragraphs = essay_data["essay_paragraphs_corrected"]

    # Process each comment
    for comment_item in comment_list:
        # Extract comment text (try "comment" field first, then "data")
        text_content = comment_item.get("comment", "")
        if text_content == "":
            text_content = comment_item.get("data", "")

        # Build base comment dictionary
        formatted_comment = {
            "id": comment_item["id"],
            "paragraph_id": comment_item["paragraph_id"],
            "comment": text_content,
        }
        # Add type field for micro corrections
        if content_type == "micro":
            formatted_comment["type"] = comment_item.get("type", "")

        # Link comment to its paragraph
        para_id = comment_item["paragraph_id"]
        if para_id is not None and para_id < len(corrected_paragraphs):
            # Add full paragraph text
            formatted_comment["paragraph_text"] = corrected_paragraphs[para_id]

            # For micro corrections, calculate word positions for highlighting
            if content_type == "micro":
                formatted_comment["highlighted_text"] = comment_item["highlighted_text"]
                # Find the position of highlighted text in the paragraph
                start_position = find_nearest_text_position_word(
                    comment_item["highlighted_text"],
                    formatted_comment["paragraph_text"],
                    comment_item["start"],
                )
                # Set positions (-1 if not found)
                if start_position is None:
                    start_position = -1
                    end_position = -1
                else:
                    # Calculate end position based on word count
                    highlighted_word_count = len(comment_item["highlighted_text"].split())
                    end_position = start_position + highlighted_word_count
                formatted_comment["start"] = start_position
                formatted_comment["end"] = end_position

        processed_comments.append(formatted_comment)
    return processed_comments
