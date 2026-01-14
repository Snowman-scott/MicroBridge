import os
from xml.dom import minidom
from xml.parsers.expat import ExpatError


def convert_ndpa_to_lmd(
    input_filename, output_filename=None, allow_missing_calibration=False
):
    """
    Convert NDP.view2 annotation file (.ndpa) to LMD-compatible XML format.

    Args:
        input_filename: Path to the .ndpa XML file
        output_filename: Optional output filename. If not provided, will use input name with '_LMD.xml'
        allow_missing_calibration: If False, conversion fails when calibration points are missing.
                                   If True, writes placeholder (0,0) coordinates with warning.

    Returns:
        True if successful, False otherwise
    """

    try:
        # Check if input file exists
        if not os.path.exists(input_filename):
            print(f"ERROR: Input file not found: {input_filename}")
            return False

        # Generate output filename if not provided
        if output_filename is None:
            base_name = os.path.splitext(input_filename)[0]
            output_filename = f"{base_name}_LMD.xml"

        print(f"Reading: {input_filename}")

        # Parse the NDP.view2 XML file
        with open(input_filename, "r", encoding="utf-8") as file:
            ndpa_xml = minidom.parse(file)

        # Get all ndpviewstate elements (regions)
        regions = ndpa_xml.getElementsByTagName("ndpviewstate")

        print(f"Found {len(regions)} regions in the file")

        if len(regions) < 4:
            print(
                f"WARNING: Found only {len(regions)} regions. Need at least 4 (3 calibration + 1 shape)"
            )
            if len(regions) < 3:
                print("ERROR: Need at least 3 regions for calibration points!")
                return False
            print("Proceeding with available regions...")

        # Create output XML file
        with open(output_filename, "w", encoding="utf-8") as f1:
            # Write XML header
            f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f1.write("<ImageData>\n")
            f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")

            print("\nProcessing calibration points...")

            # Process first 3 regions as calibration points
            for cal_idx in range(min(3, len(regions))):
                region = regions[cal_idx]

                # Get region title for debugging
                title_elem = region.getElementsByTagName("title")
                title = (
                    title_elem[0].firstChild.data  # type: ignore[attr-defined]
                    if title_elem and title_elem[0].firstChild
                    else "Unnamed"
                )

                # Try to get coordinates from annotation element first (circle annotations)
                # If not found, fall back to pointlist (freehand annotations)
                x_um = None
                y_um = None

                # Method 1: Check for annotation element (circle annotations)
                annotations = region.getElementsByTagName("annotation")
                if annotations:
                    annotation = annotations[0]
                    x_elems = annotation.getElementsByTagName("x")
                    y_elems = annotation.getElementsByTagName("y")

                    if x_elems and y_elems:
                        try:
                            x_nm = float(
                                x_elems[0].firstChild.data  # type: ignore[attr-defined]
                                if x_elems[0].firstChild
                                else 0
                            )
                            y_nm = float(
                                y_elems[0].firstChild.data  # type: ignore[attr-defined]
                                if y_elems[0].firstChild
                                else 0
                            )
                            x_um = int(round(x_nm / 1000))
                            y_um = int(round(y_nm / 1000))
                            print(
                                f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (from circle annotation)"
                            )
                        except (ValueError, AttributeError):
                            pass

                # Method 2: Fallback to pointlist (freehand/polygon annotations)
                if x_um is None:
                    pointlist = region.getElementsByTagName("point")
                    if len(pointlist) > 0:
                        try:
                            first_point = pointlist[0]
                            x_elem = first_point.getElementsByTagName("x")[0]
                            y_elem = first_point.getElementsByTagName("y")[0]

                            x_nm = float(
                                x_elem.firstChild.data  # type: ignore[attr-defined]
                                if x_elem.firstChild
                                and hasattr(x_elem.firstChild, "data")
                                else 0
                            )
                            y_nm = float(
                                y_elem.firstChild.data  # type: ignore[attr-defined]
                                if y_elem.firstChild
                                and hasattr(y_elem.firstChild, "data")
                                else 0
                            )
                            x_um = int(round(x_nm / 1000))
                            y_um = int(round(y_nm / 1000))
                            print(
                                f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (from pointlist)"
                            )
                        except (ValueError, AttributeError):
                            pass

                # If both methods failed, handle missing calibration point
                if x_um is None:
                    print(
                        f"  ERROR: Calibration region {cal_idx + 1} ('{title}') has no valid coordinates!"
                    )
                    if not allow_missing_calibration:
                        print("\n✗ CONVERSION FAILED")
                        print(
                            f"  Calibration point {cal_idx + 1} is missing valid coordinate data."
                        )
                        print(
                            "  The LMD system requires accurate calibration points to function correctly."
                        )
                        print("\n  To fix this issue:")
                        print("    1. Open the file in NDP.view2")
                        print(
                            "    2. Ensure the first 3 regions have valid annotations"
                        )
                        print(
                            "    3. Use circle annotations for calibration points (recommended)"
                        )
                        print(
                            "\n  To force conversion with placeholder (0,0) coordinates, use --force flag"
                        )
                        return False
                    else:
                        # User explicitly allowed placeholder coordinates
                        x_um = 0
                        y_um = 0
                        print(
                            "  WARNING: Using placeholder coordinates (0,0) - LMD system may malfunction!"
                        )
                        print(
                            f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm (placeholder)"
                        )

                # Write calibration point (either real or placeholder)
                f1.write(
                    f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n"
                )
                f1.write(
                    f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n"
                )

            # First pass: collect valid shapes (regions with points)
            valid_shapes = []
            for shape_idx in range(3, len(regions)):
                region = regions[shape_idx]
                shape_num = shape_idx - 2  # Shape numbering starts at 1

                # Get region title
                title_elem = region.getElementsByTagName("title")
                title = (
                    title_elem[0].firstChild.data  # type: ignore[attr-defined]
                    if title_elem and title_elem[0].firstChild
                    else f"Shape_{shape_num}"
                )

                # Get all points in this region
                pointlist = region.getElementsByTagName("point")
                num_points = len(pointlist)

                if num_points > 0:
                    valid_shapes.append(
                        {
                            "shape_num": shape_num,
                            "title": title,
                            "pointlist": pointlist,
                            "num_points": num_points,
                        }
                    )

            # Write actual ShapeCount based on valid shapes
            num_shapes = len(valid_shapes)
            f1.write(f"  <ShapeCount>{num_shapes}</ShapeCount>\n")

            print(f"\nProcessing {num_shapes} capture shapes...")

            # Second pass: write valid shapes
            for shape_data in valid_shapes:
                shape_num = shape_data["shape_num"]
                title = shape_data["title"]
                pointlist = shape_data["pointlist"]
                num_points = shape_data["num_points"]

                print(f"  Shape {shape_num} ('{title}'): {num_points} vertices")

                # Write shape header
                f1.write(f"  <Shape_{shape_num}>\n")
                f1.write(f"    <PointCount>{num_points}</PointCount>\n")

                # Write all vertices for this shape
                for point_idx, point in enumerate(pointlist):
                    x_elem = point.getElementsByTagName("x")[0]
                    y_elem = point.getElementsByTagName("y")[0]

                    # Convert from nanometers to micrometers and round to integer
                    x_nm = float(
                        x_elem.firstChild.data  # type: ignore[attr-defined]
                        if x_elem.firstChild and hasattr(x_elem.firstChild, "data")
                        else 0
                    )
                    y_nm = float(
                        y_elem.firstChild.data  # type: ignore[attr-defined]
                        if y_elem.firstChild and hasattr(y_elem.firstChild, "data")
                        else 0
                    )
                    x_um = int(round(x_nm / 1000))
                    y_um = int(round(y_nm / 1000))

                    # Write point coordinates
                    f1.write(f"    <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                    f1.write(f"    <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")

                # Close shape
                f1.write(f"  </Shape_{shape_num}>\n")

            # Close XML
            f1.write("</ImageData>\n")

        print("\n✓ Conversion complete!")
        print(f"  Output saved to: {output_filename}")
        print(f"  Total regions processed: {len(regions)}")
        print("    - 3 calibration/reference points")
        print(f"    - {num_shapes} capture shapes")

        return True

    except FileNotFoundError:
        print("\n✗ ERROR: Input file not found")
        print(f"  File: {input_filename}")
        print("\n  The file may have been moved or deleted.")
        print("  Please check the file path and try again.")
        return False
    except PermissionError:
        print("\n✗ ERROR: Permission denied")
        print(f"  File: {input_filename}")
        print(
            "\n  You don't have permission to read this file or write to the output location."
        )
        print(
            "  Try running with appropriate permissions or choose a different output folder."
        )
        return False
    except ExpatError as e:
        print("\n✗ ERROR: Invalid XML format")
        print(f"  File: {input_filename}")
        print(f"  Details: {e}")
        print("\n  This file may be corrupted or not a valid NDPA file.")
        print("  Try opening it in NDP.view2 to verify it's valid.")
        return False
    except ValueError as e:
        print("\n✗ ERROR: Invalid data in file")
        print(f"  File: {input_filename}")
        print(f"  Details: {e}")
        print("\n  The file contains invalid coordinate or numeric data.")
        print("  Please check the annotation data in NDP.view2.")
        return False
    except Exception as e:
        print("\n✗ ERROR: Unexpected error during conversion")
        print(f"  File: {input_filename}")
        print(f"  Error: {e}")
        print("\n  This is an unexpected error. If it persists:")
        print("    1. Check that the file is a valid NDPA file")
        print("    2. Try converting other files to see if the issue is file-specific")
        print(
            "    3. Report this issue at: https://github.com/Snowman-scott/MicroBridge/issues"
        )

        # Only show traceback if debug mode
        if "--debug" in sys.argv:
            import traceback

            print("\n  Debug traceback:")
            traceback.print_exc()
        else:
            print("\n  (Use --debug flag to see detailed error information)")
        return False


def batch_convert_directory(directory=".", allow_missing_calibration=False):
    """
    Convert all .ndpa files in the specified directory.

    Args:
        directory: Path to directory containing .ndpa files (default is current directory)
        allow_missing_calibration: If False, skip files with missing calibration points

    Returns:
        Number of files successfully converted
    """
    # Find all .ndpa files
    ndpa_files = []
    for file in os.listdir(directory):
        if file.endswith(".ndpa"):
            ndpa_files.append(os.path.join(directory, file))

    if not ndpa_files:
        print(f"No .ndpa files found in directory: {directory}")
        return 0

    print("=" * 70)
    print(f"Found {len(ndpa_files)} .ndpa file(s) to convert:")
    for file in ndpa_files:
        print(f"  - {os.path.basename(file)}")
    print("=" * 70)
    print()

    # Convert each file
    successful = 0
    for ndpa_file in ndpa_files:
        try:
            if convert_ndpa_to_lmd(
                ndpa_file, allow_missing_calibration=allow_missing_calibration
            ):
                successful += 1
            print()
        except Exception as e:
            print(f"✗ Unexpected error converting {os.path.basename(ndpa_file)}: {e}")
            print()

    print("=" * 70)
    print(
        f"Batch conversion complete: {successful}/{len(ndpa_files)} files converted successfully"
    )
    print("=" * 70)

    return successful


# Main execution
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  NDP.view2 to LMD XML Converter")
    print("=" * 70)
    print("\nIMPORTANT: Your .ndpa file must have:")
    print("  • First 3 regions = Reference/Calibration points")
    print("  • Remaining regions = Shapes to capture with LMD")
    print("=" * 70)
    print()

    # Check command line arguments
    import sys

    # Parse flags
    allow_missing = "--force" in sys.argv
    files_to_convert = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if allow_missing:
        print(
            "⚠️  --force flag detected: Will use placeholder (0,0) for missing calibration points"
        )
        print("    WARNING: This may cause the LMD system to malfunction!\n")

    if len(files_to_convert) > 0:
        # Convert specific file(s) provided as arguments
        print(
            f"Converting {len(files_to_convert)} file(s) from command line arguments...\n"
        )
        successful = 0
        for filename in files_to_convert:
            if convert_ndpa_to_lmd(filename, allow_missing_calibration=allow_missing):
                successful += 1
            print()
        print(f"\nConverted {successful}/{len(files_to_convert)} file(s) successfully")
    else:
        # Batch convert all .ndpa files in current directory
        print("No files specified. Searching current directory for .ndpa files...\n")
        batch_convert_directory(".", allow_missing_calibration=allow_missing)
