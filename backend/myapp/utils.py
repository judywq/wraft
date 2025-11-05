from typing import Literal

PARAGRAPH_DELIMITER = "\n"


def find_nearest_text_position_word(
    text: str,
    full_text: str,
    start_pos: int | None = None,
) -> int | None:
    """
    Find the closest position of the given text in the full_text by searching
    near the given start_pos and stopping early when a match is found.

    Parameters:
    text (str): The target text to find.
    full_text (str): The text in which to search.
    start_pos (int, optional): An approximate starting position.

    Returns:
    int: The position of the closest occurrence of the text in full_text.
    None: If the text is not found.
    """
    if start_pos is None:
        # If no start_pos is provided, default to searching from the start
        start_pos = 0

    def is_same_words(words, full_words):
        return " ".join(words) in " ".join(full_words)

    words = text.split()
    words_length = len(words)

    full_words = full_text.split()
    full_words_length = len(full_words)

    # Ensure start_pos is within valid bounds
    start_pos = max(0, min(full_words_length, start_pos))

    # Search outward from start_pos
    left, right = start_pos, start_pos
    text_length = words_length
    full_length = full_words_length

    while left >= 0 or right < full_length:
        # Check the left side
        if left >= 0 and is_same_words(words, full_words[left : left + text_length]):
            return left

        # Check the right side
        if right < full_length and is_same_words(
            words,
            full_words[right : right + text_length],
        ):
            return right

        # Expand the search range
        left -= 1
        right += 1

    # If no match is found, return None
    return None


def remove_tag(raw_content: str, end_tag: str) -> str:
    """Remove everything before the end_tag tag"""
    start_idx = raw_content.find(end_tag)
    if start_idx == -1:
        return raw_content
    return raw_content[start_idx + len(end_tag) :]


def post_process_deep(
    essay_data: dict,
    deep_data: dict,
    content_type: Literal["micro", "macro"],
) -> list[dict]:
    """Post process the deep content"""
    comments = deep_data.get("comments", [])
    new_comments = []
    essay_paragraphs_corrected = essay_data["essay_paragraphs_corrected"]

    for _, comment in enumerate(comments):
        comment_text = comment.get("comment", "")
        if comment_text == "":
            comment_text = comment.get("data", "")

        # Add to JSON result
        json_comment = {
            "id": comment["id"],
            "paragraph_id": comment["paragraph_id"],
            "comment": comment_text,
        }
        if content_type == "micro":
            json_comment["type"] = comment.get("type", "")

        paragraph_id = comment["paragraph_id"]
        if paragraph_id is not None and paragraph_id < len(essay_paragraphs_corrected):
            json_comment["paragraph_text"] = essay_paragraphs_corrected[paragraph_id]

            if content_type == "micro":
                json_comment["highlighted_text"] = comment["highlighted_text"]
                revised_start = find_nearest_text_position_word(
                    comment["highlighted_text"],
                    json_comment["paragraph_text"],
                    comment["start"],
                )
                if revised_start is None:
                    revised_start = -1
                    revised_end = -1
                else:
                    revised_end = revised_start + len(
                        comment["highlighted_text"].split(),
                    )
                json_comment["start"] = revised_start
                json_comment["end"] = revised_end

        new_comments.append(json_comment)
    return new_comments
