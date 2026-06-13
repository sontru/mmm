from pathlib import Path
import xml.etree.ElementTree as ET

from .config import ROOT_DIR


GRAPHICS_DIR = ROOT_DIR / "assets" / "graphics"
SVG_NS = "http://www.w3.org/2000/svg"
MAX_SVG_BYTES = 160_000
BLOCKED_TAGS = {"script", "foreignObject", "iframe", "object", "embed"}


def graphics_assets():
    """List editable SVG graphics assets for the admin interface."""
    return [
        {
            "path": _relative_path(path),
            "name": path.name,
            "size": path.stat().st_size,
        }
        for path in sorted(GRAPHICS_DIR.glob("*.svg"))
        if path.is_file()
    ]


def read_graphics_asset(asset_path):
    """Read a validated SVG graphics asset for editing."""
    path = _safe_svg_path(asset_path)
    return {
        "path": _relative_path(path),
        "name": path.name,
        "svg": path.read_text(encoding="utf-8"),
    }


def save_graphics_asset(asset_path, svg):
    """Validate and save an edited SVG graphics asset."""
    path = _safe_svg_path(asset_path)
    if not isinstance(svg, str):
        raise ValueError("SVG content is required")
    svg = svg.strip()
    if len(svg.encode("utf-8")) > MAX_SVG_BYTES:
        raise ValueError("SVG is too large")
    _validate_svg(svg)
    path.write_text(svg + "\n", encoding="utf-8")
    return read_graphics_asset(asset_path)


def _safe_svg_path(asset_path):
    """Resolve and validate a requested SVG asset path."""
    path = (ROOT_DIR / str(asset_path)).resolve()
    try:
        path.relative_to(GRAPHICS_DIR.resolve())
    except ValueError:
        raise ValueError("Asset must be in assets/graphics") from None
    if path.suffix.lower() != ".svg" or not path.exists() or not path.is_file():
        raise ValueError("Unknown SVG asset")
    return path


def _relative_path(path):
    """Return a project-relative POSIX path for display or API payloads."""
    return path.resolve().relative_to(ROOT_DIR).as_posix()


def _validate_svg(svg):
    """Reject SVG markup that is malformed or unsafe for editing."""
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as error:
        raise ValueError(f"Invalid SVG: {error}") from None
    if _local_name(root.tag) != "svg":
        raise ValueError("SVG root element is required")
    for element in root.iter():
        if _local_name(element.tag) in BLOCKED_TAGS:
            raise ValueError("SVG contains an unsupported element")
        for name, value in element.attrib.items():
            clean_name = _local_name(name).lower()
            clean_value = str(value).strip().lower()
            if clean_name.startswith("on"):
                raise ValueError("SVG event attributes are not allowed")
            if clean_value.startswith("javascript:"):
                raise ValueError("SVG javascript links are not allowed")


def _local_name(tag):
    """Return the local XML tag or attribute name without its namespace."""
    return tag.rsplit("}", 1)[-1]
