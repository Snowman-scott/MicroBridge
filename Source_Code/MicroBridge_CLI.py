import os
from xml.dom import minidom

def convert_ndpa_to_lmd(input_filename, output_filename=None):
    """
    Convert NDP.view2 annotation file (.ndpa) to LMD-compatible XML format.
    
    Args:
        input_filename: Path to the .ndpa XML file
        output_filename: Optional output filename. If not provided, will use input name with '_LMD.xml'
    
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
        with open(input_filename, 'r', encoding='utf-8') as file:
            ndpa_xml = minidom.parse(file)
        
        # Get all ndpviewstate elements (regions)
        regions = ndpa_xml.getElementsByTagName('ndpviewstate')
        
        print(f"Found {len(regions)} regions in the file")
        
        if len(regions) < 4:
            print(f"WARNING: Found only {len(regions)} regions. Need at least 4 (3 calibration + 1 shape)")
            if len(regions) < 3:
                print("ERROR: Need at least 3 regions for calibration points!")
                return False
            print("Proceeding with available regions...")
        
        # Create output XML file
        with open(output_filename, 'w', encoding='utf-8') as f1:
            # Write XML header
            f1.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f1.write("<ImageData>\n")
            f1.write("  <GlobalCoordinates>1</GlobalCoordinates>\n")
            
            print("\nProcessing calibration points...")
            
            # Process first 3 regions as calibration points
            for cal_idx in range(min(3, len(regions))):
                region = regions[cal_idx]
                
                # Get region title for debugging
                title_elem = region.getElementsByTagName('title')
                title = title_elem[0].firstChild.data if title_elem and title_elem[0].firstChild else "Unnamed"
                
                # Get the pointlist for this region
                pointlist = region.getElementsByTagName('point')
                
                if len(pointlist) == 0:
                    print(f"  WARNING: Calibration region {cal_idx + 1} ('{title}') has no points!")
                    continue
                
                # Use the first point of each calibration region as the reference point
                first_point = pointlist[0]
                x_elem = first_point.getElementsByTagName('x')[0]
                y_elem = first_point.getElementsByTagName('y')[0]
                
                # Convert from nanometers to micrometers and round to integer
                x_nm = float(x_elem.firstChild.data)
                y_nm = float(y_elem.firstChild.data)
                x_um = int(round(x_nm / 1000))
                y_um = int(round(y_nm / 1000))
                
                print(f"  Calibration Point {cal_idx + 1} ('{title}'): X={x_um} µm, Y={y_um} µm")
                
                # Write calibration point
                f1.write(f"  <X_CalibrationPoint_{cal_idx + 1}>{x_um}</X_CalibrationPoint_{cal_idx + 1}>\n")
                f1.write(f"  <Y_CalibrationPoint_{cal_idx + 1}>{y_um}</Y_CalibrationPoint_{cal_idx + 1}>\n")
            
            # Calculate number of shapes (total regions minus 3 calibration regions)
            num_shapes = max(0, len(regions) - 3)
            f1.write(f"  <ShapeCount>{num_shapes}</ShapeCount>\n")
            
            print(f"\nProcessing {num_shapes} capture shapes...")
            
            # Process remaining regions as shapes
            for shape_idx in range(3, len(regions)):
                region = regions[shape_idx]
                shape_num = shape_idx - 2  # Shape numbering starts at 1
                
                # Get region title
                title_elem = region.getElementsByTagName('title')
                title = title_elem[0].firstChild.data if title_elem and title_elem[0].firstChild else f"Shape_{shape_num}"
                
                # Get all points in this region
                pointlist = region.getElementsByTagName('point')
                num_points = len(pointlist)
                
                if num_points == 0:
                    print(f"  WARNING: Shape {shape_num} ('{title}') has no points! Skipping...")
                    continue
                
                print(f"  Shape {shape_num} ('{title}'): {num_points} vertices")
                
                # Write shape header
                f1.write(f"  <Shape_{shape_num}>\n")
                f1.write(f"    <PointCount>{num_points}</PointCount>\n")
                
                # Write all vertices for this shape
                for point_idx, point in enumerate(pointlist):
                    x_elem = point.getElementsByTagName('x')[0]
                    y_elem = point.getElementsByTagName('y')[0]
                    
                    # Convert from nanometers to micrometers and round to integer
                    x_nm = float(x_elem.firstChild.data)
                    y_nm = float(y_elem.firstChild.data)
                    x_um = int(round(x_nm / 1000))
                    y_um = int(round(y_nm / 1000))
                    
                    # Write point coordinates
                    f1.write(f"    <X_{point_idx + 1}>{x_um}</X_{point_idx + 1}>\n")
                    f1.write(f"    <Y_{point_idx + 1}>{y_um}</Y_{point_idx + 1}>\n")
                
                # Close shape
                f1.write(f"  </Shape_{shape_num}>\n")
            
            # Close XML
            f1.write("</ImageData>\n")
        
        print(f"\n✓ Conversion complete!")
        print(f"  Output saved to: {output_filename}")
        print(f"  Total regions processed: {len(regions)}")
        print(f"    - 3 calibration/reference points")
        print(f"    - {num_shapes} capture shapes")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR during conversion: {e}")
        import traceback
        traceback.print_exc()
        return False


def batch_convert_directory(directory="."):
    """
    Convert all .ndpa files in the specified directory.
    
    Args:
        directory: Path to directory containing .ndpa files (default is current directory)
    
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
            if convert_ndpa_to_lmd(ndpa_file):
                successful += 1
            print()
        except Exception as e:
            print(f"✗ Unexpected error converting {os.path.basename(ndpa_file)}: {e}")
            print()
    
    print("=" * 70)
    print(f"Batch conversion complete: {successful}/{len(ndpa_files)} files converted successfully")
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
    
    if len(sys.argv) > 1:
        # Convert specific file(s) provided as arguments
        print(f"Converting {len(sys.argv) - 1} file(s) from command line arguments...\n")
        successful = 0
        for filename in sys.argv[1:]:
            if convert_ndpa_to_lmd(filename):
                successful += 1
            print()
        print(f"\nConverted {successful}/{len(sys.argv) - 1} file(s) successfully")
    else:
        # Batch convert all .ndpa files in current directory
        print("No files specified. Searching current directory for .ndpa files...\n")
        batch_convert_directory(".")