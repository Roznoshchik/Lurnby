import copy
import re

from bs4 import BeautifulSoup, NavigableString, Tag


VOID_ELEMENTS = {"br", "hr"}
ANCHOR_ELEMENTS = {"img"}
BLOCK_CONTENT = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "figcaption"}


def build_content_tree(content):
    """Build a content tree with text offsets from an HTML string."""
    soup = BeautifulSoup(content or "", "lxml")
    offset = 0
    last_char = [None]
    pending_space = [False]

    def is_legacy_highlight_span(node):
        if node.name != "span":
            return False
        node_id = node.get("id", "")
        if node_id.startswith("highlight"):
            return True
        node_class = node.get("class", [])
        if isinstance(node_class, str):
            node_class = [node_class]
        return any("highlight" in c for c in node_class)

    def process(node):
        nonlocal offset

        if isinstance(node, NavigableString):
            raw = str(node)
            had_leading_ws = raw and raw[0] in " \t\n\r\xa0"
            had_trailing_ws = raw and raw[-1] in " \t\n\r\xa0"
            raw = raw.replace("’", "'").replace("‘", "'")
            raw = raw.replace("“", '"').replace("”", '"')
            raw = raw.replace("–", "-").replace("—", "-")
            text = re.sub(r"[\xa0\s]+", " ", raw).strip()
            if not text:
                if had_leading_ws or had_trailing_ws:
                    pending_space[0] = True
                return None
            first_char = text[0] if text else ""
            before_closing = first_char not in ",.;:!?)\"']"
            after_opening = last_char[0] not in "\"'([" if last_char[0] else True
            needs_space = (pending_space[0] or had_leading_ws) and last_char[0] and before_closing and after_opening
            if needs_space:
                text = " " + text
            pending_space[0] = had_trailing_ws
            last_char[0] = text[-1] if text else None
            start = offset
            offset += len(text)
            return {"type": "text", "text": text, "start": start, "length": len(text)}

        if isinstance(node, Tag):
            if is_legacy_highlight_span(node):
                children = []
                for child in node.children:
                    child_node = process(child)
                    if child_node:
                        if isinstance(child_node, list):
                            children.extend(child_node)
                        else:
                            children.append(child_node)
                if children:
                    return children if len(children) > 1 else children[0]
                return None

            if node.name in VOID_ELEMENTS:
                start = offset
                offset += 1
                return {"type": "void", "tag": node.name, "start": start, "length": 1}

            if node.name in ANCHOR_ELEMENTS:
                start = offset
                offset += 1
                return {
                    "type": "anchor",
                    "tag": node.name,
                    "src": node.get("src"),
                    "alt": node.get("alt"),
                    "start": start,
                    "length": 1,
                }

            if node.name in BLOCK_CONTENT:
                pending_space[0] = False
                last_char[0] = None

            children = []
            for child in node.children:
                child_node = process(child)
                if child_node:
                    if isinstance(child_node, list):
                        children.extend(child_node)
                    else:
                        children.append(child_node)

            if not children:
                return None

            if node.name in BLOCK_CONTENT:
                children.append({"type": "text", "text": "\n", "start": offset, "length": 1})
                offset += 1

            first = children[0]
            last = children[-1]
            end = last["end"] if "end" in last else last["start"] + last["length"]

            return {"type": "element", "tag": node.name, "children": children, "start": first["start"], "end": end}

        return None

    tree = []
    root = soup.body or soup
    for child in root.children:
        node = process(child)
        if node:
            if isinstance(node, list):
                tree.extend(node)
            else:
                tree.append(node)

    return tree


def get_flat_text(content_tree):
    """Extract plain text from a content tree, using \\x00 as a void element placeholder."""
    if not content_tree:
        return ""

    def extract(node):
        if node["type"] == "text":
            return node["text"]
        if node["type"] in ("void", "anchor"):
            return "\x00"
        if node["type"] == "element":
            return "".join(extract(child) for child in node.get("children", []))
        return ""

    return "".join(extract(node) for node in content_tree)


def get_tree_end_offset(tree):
    """Return the offset after the last character in the tree."""
    if not tree:
        return 0
    last = tree[-1]
    return last.get("end") or (last.get("start", 0) + last.get("length", 0))


def find_split_points(tree, total_length, min_size, max_size):
    """Find optimal split offsets for chunking a tree."""
    split_points = []
    current_start = 0

    while current_start + min_size < total_length:
        search_start = current_start + min_size
        search_end = min(current_start + max_size, total_length)

        best = find_best_split_in_range(tree, search_start, search_end)
        if best is None:
            best = search_end

        split_points.append(best)
        current_start = best

    return split_points


def find_best_split_in_range(tree, start, end):
    """Find the best split point between start and end offsets."""
    candidates = []

    def walk(node, depth):
        node_start = node.get("start", 0)
        node_end = node.get("end") or (node_start + node.get("length", 0))

        if node_end <= start or node_start >= end:
            return

        if node["type"] == "text":
            text = node["text"]
            text_start = node["start"]

            for i, char in enumerate(text):
                offset = text_start + i
                if offset < start or offset >= end:
                    continue

                if char in ".!?" and i + 1 < len(text) and text[i + 1] == " ":
                    candidates.append((offset + 2, 2, depth))
                elif char == " ":
                    candidates.append((offset + 1, 1, depth))

        elif node["type"] == "element":
            tag = node["tag"]

            if tag in {"h1", "h2", "h3"} and node_start >= start and node_start < end:
                candidates.append((node_start, 4, depth))
            elif tag in {"p", "div", "blockquote", "li", "pre", "figcaption"}:
                if node_end >= start and node_end < end:
                    candidates.append((node_end, 3, depth))

            for child in node.get("children", []):
                walk(child, depth + 1)

    for node in tree:
        walk(node, 0)

    if not candidates:
        return None

    candidates.sort(key=lambda x: (-x[1], x[2]))
    return candidates[0][0]


def slice_tree_at_offsets(tree, split_offsets):
    """Slice a tree at given offsets, adding continues/continuation flags."""
    if not split_offsets:
        return [tree]

    chunks = []
    remaining = copy.deepcopy(tree)

    for split_offset in split_offsets:
        left, right = split_tree_at_offset(remaining, split_offset)
        chunks.append(left)
        remaining = right

    chunks.append(remaining)
    return chunks


def split_tree_at_offset(tree, offset):
    """Split a tree at offset, returning (left, right) trees."""
    left = []
    right = []

    for node in tree:
        node_start = node.get("start", 0)
        node_end = node.get("end") or (node_start + node.get("length", 0))

        if node_end <= offset:
            left.append(copy.deepcopy(node))
        elif node_start >= offset:
            right.append(copy.deepcopy(node))
        else:
            left_part, right_part = split_node_at_offset(node, offset)
            if left_part:
                left.append(left_part)
            if right_part:
                right.append(right_part)

    return left, right


def split_node_at_offset(node, offset):
    """Split a single node at offset, adding continues/continuation flags."""
    node_start = node.get("start", 0)

    if node["type"] == "text":
        text = node["text"]
        split_idx = offset - node_start
        left_text = text[:split_idx]
        right_text = text[split_idx:]

        left_node = None
        right_node = None

        if left_text:
            left_node = {
                "type": "text",
                "text": left_text,
                "start": node_start,
                "length": len(left_text),
            }
        if right_text:
            right_node = {
                "type": "text",
                "text": right_text,
                "start": offset,
                "length": len(right_text),
            }

        return left_node, right_node

    elif node["type"] == "element":
        children = node.get("children", [])
        left_children = []
        right_children = []

        for child in children:
            child_start = child.get("start", 0)
            child_end = child.get("end") or (child_start + child.get("length", 0))

            if child_end <= offset:
                left_children.append(copy.deepcopy(child))
            elif child_start >= offset:
                right_children.append(copy.deepcopy(child))
            else:
                left_part, right_part = split_node_at_offset(child, offset)
                if left_part:
                    left_children.append(left_part)
                if right_part:
                    right_children.append(right_part)

        left_node = None
        right_node = None

        if left_children:
            first = left_children[0]
            last = left_children[-1]
            left_end = last.get("end") or (last.get("start", 0) + last.get("length", 0))
            left_node = {
                "type": "element",
                "tag": node["tag"],
                "children": left_children,
                "start": first.get("start", node_start),
                "end": left_end,
                "continues": True,
            }
            if node.get("continuation"):
                left_node["continuation"] = True

        if right_children:
            first = right_children[0]
            last = right_children[-1]
            right_end = last.get("end") or (last.get("start", 0) + last.get("length", 0))
            right_node = {
                "type": "element",
                "tag": node["tag"],
                "children": right_children,
                "start": first.get("start", offset),
                "end": right_end,
                "continuation": True,
            }
            if node.get("continues"):
                right_node["continues"] = True

        return left_node, right_node

    else:
        if node_start < offset:
            return copy.deepcopy(node), None
        else:
            return None, copy.deepcopy(node)


def rebase_tree_offsets(tree):
    """Rebase tree offsets to start at 0."""
    if not tree:
        return tree

    base_offset = tree[0].get("start", 0)
    if base_offset == 0:
        return tree

    def rebase(node):
        if "start" in node:
            node["start"] -= base_offset
        if "end" in node:
            node["end"] -= base_offset
        for child in node.get("children", []):
            rebase(child)

    rebased = copy.deepcopy(tree)
    for node in rebased:
        rebase(node)

    return rebased
