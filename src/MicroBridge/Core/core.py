from xml.dom import minidom

def convert_ndpa_to_lmd_core(input_filename: str, output_filename: str) -> None:
    # 1. Parsing The input
    with open(input_filename, "r", encoding="utf-8") as file:
        ndpa_xml = minidom.parse(file)

    # Find all 'ndpviewstate' elements
    regions = ndpa_xml.getElementsByTagName("ndpviewstate")

    # 2. Extract Calibration points
    calibration_points = []

    for cal_idx in range(min(3, len(regions))):
        region = regions[cal_idx]
        x_um, y_um = None, None

        # Method 1: checking for circle annotations (Should always use as the instructional documentation states)
        annotations = region.getElementsByTagName("annotation")
        if annotations:
            x_elems = annotations[0].getElementsByTagName("x")
            y_elems = annotations[0].getElementsByTagName("y")

            if x_elems and y_elems:
                # Data is in nanometers. Divide by 1000 to get micrometers
                x_um = int(round(float(x_elems[0].firstChild.data) / 1000))
                y_um = int(round(float(y_elems[0].firstChild.data) / 1000))

        if x_um is None: # Method 2: Fallback to Freehand points
            pointlist = region.getElementsByTagName("point")
            if pointlist:
                x_elem = pointlist[0].getElementsByTagName("x")[0]
                y_elem = pointlist[0].getElementsByTagName("y")[0]

                x_um = int(round(float(x_elem.firstChild.data) / 1000))
                y_um = int(round(float(y_elem.firstChild.data) / 1000))

        if x_um is None:
            raise ValueError(f"Calibration point {cal_idx + 1} came back malformed or incorrectly made")

        calibration_points.append((x_um, y_um))

    # 3. Extracting Capture shapes
    valid_shapes = []
    shape_num = 1

    for shape_idx in range(3, len(regions)):
        region = regions[shape_idx]

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

                    x_um = int(round(float(x_elem.firstChild.data) / 1000))
                    y_um = int(round(float(y_elem.firstChild.data) / 1000))
                except (IndexError, AttributeError) as e:
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
            f1.write(f" <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n")
            f1.write(f" <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n")

        f1.write(f" <ShapeCount>{len(valid_shapes)}</ShapeCount>\n")

        for shape_data in valid_shapes:
            s_num = shape_data["shape_num"]
            points = shape_data["points"]

            f1.write(f"     <Shape_{s_num}>\n")
            f1.write(f"         <PointCount>{len(points)}</PointCount>\n")

            # We write the X/Y cords for the Verticies of this shape
            for point_idx, (x_um, y_um) in enumerate(points):
                f1.write(f"     <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                f1.write(f"     <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")

            f1.write(f" </Shape_{s_num}>\n")

        f1.write("</ImageData>\n")
