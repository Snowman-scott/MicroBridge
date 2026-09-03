from datetime import datetime

from MicroBridge.file_read.datapass import Annot, AnnotFile, Metadata, Point


p = Point(x=12, y=16)

an = Annot(id="Test", cords=[p])

met = Metadata(creationDate=datetime.now())

file = AnnotFile(anos=[an], md=met)

print(file)
