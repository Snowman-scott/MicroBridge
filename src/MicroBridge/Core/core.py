import re

from pathlib import Path
from xml.dom import minidom
from xml.dom.minidom import Text


# A reference point is a region titled ref_1, ref_2 or ref_3. The separator is
# forgiving (ref 1, ref-1, Ref1 all count) but the stem is not, so there is one
# convention to teach scientists rather than a family of near-misses.
REF_TITLE_PATTERN = re.compile(r"^ref[\s_-]*([123])$", re.IGNORECASE)

REF_POINT_NUMBERS = (1, 2, 3)


class NoReferencePointError(ValueError):
    """Raised when a file has no usable set of reference points.

    Subclasses ValueError so the existing CLI/GUI error handling keeps catching it.
    """


def _element_text(element: minidom.Element) -> str:
    first_child = element.firstChild
    if not isinstance(first_child, Text):
        raise ValueError(f"<{element.tagName}> element has no text content")
    return first_child.data


def _region_title(region: minidom.Element) -> str:
    titles = region.getElementsByTagName("title")
    if not titles:
        return ""
    first_child = titles[0].firstChild
    if not isinstance(first_child, Text):
        return ""
    return first_child.data.strip()


def _is_circle(region: minidom.Element) -> bool:
    return any(
        annotation.getAttribute("type") == "circle"
        for annotation in region.getElementsByTagName("annotation")
    )


def _region_coordinates(region: minidom.Element) -> tuple[int, int] | None:
    """Pull a single (x, y) micrometre pair out of a region, or None if absent."""
    # Method 1: circle annotations carry their centre directly (the documented way).
    annotations = region.getElementsByTagName("annotation")
    if annotations:
        x_elems = annotations[0].getElementsByTagName("x")
        y_elems = annotations[0].getElementsByTagName("y")

        if x_elems and y_elems:
            # Data is in nanometers. Divide by 1000 to get micrometers
            return (
                int(round(float(_element_text(x_elems[0])) / 1000)),
                int(round(float(_element_text(y_elems[0])) / 1000)),
            )

    # Method 2: Fallback to Freehand points
    pointlist = region.getElementsByTagName("point")
    if pointlist:
        x_elem = pointlist[0].getElementsByTagName("x")[0]
        y_elem = pointlist[0].getElementsByTagName("y")[0]

        return (
            int(round(float(_element_text(x_elem)) / 1000)),
            int(round(float(_element_text(y_elem)) / 1000)),
        )

    return None


def _find_named_reference_points(
    regions: list[minidom.Element],
) -> tuple[dict[int, int], list[int]]:
    """Map ref number -> region index, plus any ref numbers claimed more than once."""
    found: dict[int, int] = {}
    duplicates: list[int] = []

    for index, region in enumerate(regions):
        match = REF_TITLE_PATTERN.match(_region_title(region))
        if not match:
            continue

        ref_num = int(match.group(1))
        if ref_num in found:
            if ref_num not in duplicates:
                duplicates.append(ref_num)
            continue

        found[ref_num] = index

    return found, duplicates


def _reference_points_by_name(
    regions: list[minidom.Element], found: dict[int, int], duplicates: list[int]
) -> tuple[list[tuple[int, int]], set[int], list[str]]:
    if duplicates:
        listed = ", ".join(f"ref_{n}" for n in sorted(duplicates))
        raise NoReferencePointError(
            f"More than one region is titled {listed}. "
            "Each of ref_1, ref_2 and ref_3 must name exactly one region."
        )

    missing = [n for n in REF_POINT_NUMBERS if n not in found]
    if missing:
        listed = ", ".join(f"ref_{n}" for n in missing)
        raise NoReferencePointError(
            f"No reference point named {listed}. "
            "A file using the ref_N convention needs all three of ref_1, ref_2 and ref_3."
        )

    warnings: list[str] = []
    reference_points: list[tuple[int, int]] = []
    used_indices: set[int] = set()

    for ref_num in REF_POINT_NUMBERS:
        index = found[ref_num]
        region = regions[index]

        if not _is_circle(region):
            warnings.append(
                f"ref_{ref_num} is not a circle annotation. Using it as a reference "
                "point anyway, but reference points should be drawn as circles."
            )

        coordinates = _region_coordinates(region)
        if coordinates is None:
            raise NoReferencePointError(
                f"ref_{ref_num} came back malformed or incorrectly made"
            )

        reference_points.append(coordinates)
        used_indices.add(index)

    return reference_points, used_indices, warnings


def _reference_points_by_position(
    regions: list[minidom.Element],
) -> tuple[list[tuple[int, int]], set[int], list[str]]:
    """Legacy layout: the first three regions are the reference points.

    Kept so annotation files drawn before the ref_N convention existed still convert.
    """
    if not regions:
        raise NoReferencePointError(
            "No reference points found: the file contains no annotated regions."
        )

    warnings = [
        "No regions named ref_1, ref_2 or ref_3 were found. Falling back to treating "
        "the first three regions as the reference points. Retitle them ref_1, ref_2 "
        "and ref_3 to convert this file reliably."
    ]
    reference_points: list[tuple[int, int]] = []

    for index in range(min(3, len(regions))):
        coordinates = _region_coordinates(regions[index])
        if coordinates is None:
            raise ValueError(
                f"Calibration point {index + 1} came back malformed or incorrectly made"
            )
        reference_points.append(coordinates)

    return reference_points, set(range(min(3, len(regions)))), warnings


def resolve_reference_points(
    regions: list[minidom.Element],
) -> tuple[list[tuple[int, int]], set[int], list[str]]:
    """Work out the reference points and which region indices they consumed.

    Names win: if anything is titled ref_N we commit to that convention and refuse
    to guess. Only a file with no ref_N titles at all falls back to position.
    """
    found, duplicates = _find_named_reference_points(regions)

    if found or duplicates:
        return _reference_points_by_name(regions, found, duplicates)

    return _reference_points_by_position(regions)


def derive_output_filename(input_filename: str) -> str:
    p = Path(input_filename)
    new_path = p.parent / (p.stem + "_LMD.xml")

    return str(new_path)

def convert_ndpa_to_lmd_core(input_filename: str, output_filename: str) -> list[str]:
    """Convert an .ndpa file to LMD XML. Returns any non-fatal warnings for the caller."""
    # 1. Parsing The input
    with open(input_filename, "r", encoding="utf-8") as file:
        ndpa_xml = minidom.parse(file)

    # Find all 'ndpviewstate' elements
    regions = ndpa_xml.getElementsByTagName("ndpviewstate")

    # 2. Extract reference points, by name where possible and by position otherwise
    calibration_points, reference_indices, warnings = resolve_reference_points(regions)

    # 3. Extracting Capture shapes
    valid_shapes = []
    shape_num = 1

    for shape_idx, region in enumerate(regions):
        # Whichever regions became reference points are not capture shapes
        if shape_idx in reference_indices:
            continue

        # We do this to stop Any rulers from breaking and crashing the program
        annotations = region.getElementsByTagName("annotation")
        if annotations and annotations[0].getAttribute("type") == "linearmeasure":
            continue

        # We use this to extract all the annotations the scientists want
        pointlist = region.getElementsByTagName("point")
        if len(pointlist) > 0:
            points = [] # Could change the name later to reduce the chances of "eye-slip"
            for point_idx, point in enumerate(pointlist):
                try:
                    x_elem = point.getElementsByTagName("x")[0]
                    y_elem = point.getElementsByTagName("y")[0]

                    x_um = int(round(float(_element_text(x_elem)) / 1000))
                    y_um = int(round(float(_element_text(y_elem)) / 1000))
                except (IndexError, AttributeError, ValueError) as e:
                    raise ValueError(f"Shape {shape_num} data malformed at point {point_idx + 1}") from e
                points.append((x_um, y_um))

            valid_shapes.append({
                "shape_num": shape_num,
                "points":   points
            })
            shape_num += 1

    # 4. LMD XML output
    with open(output_filename, "w", encoding="utf-8") as f1:
        f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f1.write("<ImageData>\n")
        f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")

        # We write the 3 calibration points first
        for cal_idx, (x_um, y_um) in enumerate(calibration_points):
            f1.write(f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n")
            f1.write(f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n")

        f1.write(f"  <ShapeCount>{len(valid_shapes)}</ShapeCount>\n")

        for shape_data in valid_shapes:
            s_num = shape_data["shape_num"]
            points = shape_data["points"]

            f1.write(f"  <Shape_{s_num}>\n")
            f1.write(f"    <PointCount>{len(points)}</PointCount>\n")

            # We write the X/Y cords for the Verticies of this shape
            for point_idx, (x_um, y_um) in enumerate(points):
                f1.write(f"    <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                f1.write(f"    <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")

            f1.write(f"  </Shape_{s_num}>\n")

        f1.write("</ImageData>\n")

    return warnings
