# Microbridge V3.0 plan

- Take file in as an object
- Extract the calibration points to a 2nd object

- Convert the objects data to the other programs data structure.
- Export out as the correct data type (.ndpa, .geojson)

- Top level conversion between all formats: 
xenium <-> NDPA
NDPA <-> Qupath
Qupath <-> Xenium

- Reverse conversion (LMD -> NDPA, Qupath, xenium)
- Reverse via NDPA then top level convert? (LMD -> NDPA -> qupath or xenium??)
