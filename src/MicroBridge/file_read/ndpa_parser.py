from MicroBridge.file_read.IR_classes import AnnotFile
from xml.dom import minidom
import regex


def ndpa_parser(filename: str) -> AnnotFile:
    pass

def refPointsLocator(filename: str):
    ndpa_xml = minidom.parse(filename)
    regions = ndpa_xml.getElementsByTagName("ndpviewstate")
