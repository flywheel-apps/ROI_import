import flywheel
import logging
import pprint

from utils import fwobject_utils as fu

logging.basicConfig(level="INFO")
log = logging.getLogger("ROI")


# optional = ['visible',
#             'active',
#             'invalidated',
#             'handles.start.highlight',
#             'handles.start.active',
#             'handles.end.highlight',
#             'handles.end.active',
#             'handles.initialrotation',
#             'handles.textBox',
#             'uuid',
#             '_id',
#             'frameIndex',
#             'lesionNamingNumber',
#             'userId',
#             'patientId',
#             'flywheelOrigin',
#             'timepointId',
#             'measurementNumber',
#             'cachedStats',
#             'viewport',
#             'location',
#             'description',
#             'unit']
#
# required = ['imagePath',
#             'sopInstanceUid',
#             'studyInstanceUid',
#             'sopInstanceUid',
#             'toolType',
#             'handles.start.x',
#             'handles.start.y',
#             'handles.end.x',
#             'handles.end.y']


class BoundingBox:
    def __init__(self, **kwargs):
        self.height = kwargs.get("height", 45)
        self.left = kwargs.get("left", 400)
        self.top = kwargs.get("top", 150)
        self.width = kwargs.get("width", 250)

    def to_dict(self):
        output_dict = {
            "height": self.height,
            "left": self.left,
            "top": self.top,
            "width": self.width,
        }

        return output_dict


class Coords:
    def __init__(self, x=0, y=0, active=False, highlight=None):
        self.x = x
        self.y = y
        self.active = active
        self.highlight = highlight

    def to_dict(self):
        output_dict = {
            "x": self.x,
            "y": self.y,
            "active": self.active,
            "highlight": self.highlight,
        }

        if self.highlight is None:
            trash = output_dict.pop("highlight")

        return output_dict


class TextBox:
    def __init__(self, **kwargs):
        self.coords = Coords(kwargs.get("x"), kwargs.get("y"), kwargs.get("active"))
        self.allowedOutsideImage = kwargs.get("allowedOutsideImage", True)
        self.drawnIndependently = kwargs.get("drawnIndependently", True)
        self.hasBoundingBox = kwargs.get("hasBoundingBox", True)
        self.hasMoved = kwargs.get("hasMoved", False)
        self.movesIndependently = kwargs.get("movesIndependently", False)
        self.boundingBox = BoundingBox(**kwargs.get("boundingBox", {}))

    def to_dict(self):
        output_dict = {
            "allowedOutsideImage": self.allowedOutsideImage,
            "drawnIndependently": self.drawnIndependently,
            "hasBoundingBox": self.hasBoundingBox,
            "hasMoved": self.hasMoved,
            "movesIndependently": self.movesIndependently,
            "boundingBox": self.boundingBox.to_dict(),
        }
        output_dict.update(self.coords.to_dict())

        return output_dict


class Handle:
    def __init__(self, **kwargs):
        self.handle_args = ["start", "end", "textBox", "initialRotation"]

        if "start" not in kwargs or "end" not in kwargs:
            log.error('ROI requires both "start" and "end"')
            pass

        start = kwargs.get("start", {})
        self.start = Coords(start.get("x"), start.get("y"), start.get("active", True))
        self.start.highlight = start.get("highlight", True)

        end = kwargs.get("end", {})
        self.end = Coords(end.get("x"), end.get("y"), end.get("active", False))
        self.end.highlight = end.get("highlight", True)

        text = kwargs.get("textBox", {})
        if "x" not in text:
            text["x"] = start.get("x")
        if "y" not in text:
            text["y"] = start.get("y") - (start.get("y") - end.get("y")) / 2.0
        self.textBox = TextBox(**text)

        self.initialRotation = kwargs.get("initialRotation", 0)

    def to_dict(self):

        output_dict = {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "textBox": self.textBox.to_dict(),
            "initialRotation": self.initialRotation,
        }
        return output_dict

class Cached_stats:
    
    def __init__(self, handle):
        x_limits = (handle.start.x, handle.end.x)
        y_limits = (handle.start.y, handle.end.y)
        
        print(y_limits)
        
        xmax = max(x_limits)
        ymax = max(y_limits)
        
        xmin = min(x_limits)
        ymin = min(y_limits)
        
        self.area = (xmax-xmin) * (ymax - ymin)
        self.count = (round(xmax) - round(xmin)) * (round(ymax)-round(ymin))
        self.max = 0
        self.min = 0
        self.mean = 0
        self.stdDev = 0
        self.variance = 0
    
    def to_dict(self):
        output_dict = {
            'area': self.area,
            'count': self.count,
            'max': self.max,
            'mean': self.mean,
            'min': self.min,
            'stdDev': self.stdDev,
            'variance': self.variance
        }
        return output_dict
    

class ROI:
    def __init__(self):

        log.info("Initializing ROI")

        self.mandatory_keys = [
            "Handle",
            "SeriesInstanceUID",
            "SOPInstanceUID",
            "StudyInstanceUID",
            "ROI_type",
        ]

        self.forbidden_keys = ["imagePath", "uuid", "_id"]
        self.namespace = "ohifViewer"

        self.handle = None
        self.seriesInstanceUid = None
        self.sopInstanceUid = None
        self.studyInstanceUid = None
        self.imagePath = None

        self.patientId = None
        self.toolType = None

        # Some important values we'll call out specifically for consistency
        self.visible = None
        self.active = None
        self.description = None
        self.location = None
        self.flywheelOrigin = None
        self.lesionNamingNumber = None
        self.measurementNumber = None
        self.timepointId = None
        self.cachedStats = None
        self.kwargs = None
        
    def generate_imagePath(self):

        # I don't understand either.
        path_delimiter = "$$$"
        path_suffix = "0"

        imagePath = (
            f"{self.studyInstanceUid}"
            f"{path_delimiter}"
            f"{self.seriesInstanceUid}"
            f"{path_delimiter}"
            f"{self.sopInstanceUid}"
            f"{path_delimiter}"
            f"{path_suffix}"
        )
        
        return imagePath
        

    def roi_from_dict(self, **kwargs):

        for fk in self.forbidden_keys:
            if fk in kwargs:
                log.error(f"Forbidden key {fk} found in {kwargs.keys()}")
                raise Exception("Forbidden Keys")

        for mk in self.mandatory_keys:
            if mk not in kwargs:
                log.error(f"Mandatory key {mk} not present in kwargs {kwargs.keys()}")
                raise Exception("Missing Mandatory Key")

        self.handle = Handle(**kwargs.pop("Handle"))
        self.seriesInstanceUid = kwargs.pop("SeriesInstanceUID")
        self.sopInstanceUid = kwargs.pop("SOPInstanceUID")
        self.studyInstanceUid = kwargs.pop("StudyInstanceUID")
        self.patientId = kwargs.pop('patientId')

        self.toolType = kwargs.pop("ROI_type")

        self.imagePath = self.generate_imagePath()

        # Some important values we'll call out specifically for consistency
        self.visible = kwargs.pop("visible", True)
        self.active = kwargs.pop("active", True)
        self.description = kwargs.pop("description", None)
        self.location = kwargs.pop("location", None)

        fw_origin = dict()
        if "User_Origin" in kwargs:
            fw_origin["type"] = "user"
            fw_origin["id"] = kwargs.pop("User_Origin")
        else:
            fw_origin["type"] = "gear"
            fw_origin["id"] = "CSV to ROI Gear"
        
        self.flywheelOrigin = fw_origin
        self.lesionNamingNumber = kwargs.pop("lesionNamingNumber")
        self.measurementNumber = kwargs.pop("measurementNumber")
        self.timepointId = kwargs.pop("timepointId")
        
        self.cachedStats = Cached_stats(self.handle)
        
        self.kwargs = kwargs

    def to_dict(self):

        output_dict = {
            "handles": self.handle.to_dict(),
            "cachedStats": self.cachedStats.to_dict(),
            "flywheelOrigin": self.flywheelOrigin,
            "seriesInstanceUid": self.seriesInstanceUid,
            "studyInstanceUid": self.studyInstanceUid,
            "sopInstanceUid": self.sopInstanceUid,
            "imagePath": self.imagePath,
            "visible": self.visible,
            "description": self.description,
            "location": self.location,
            "toolType": self.toolType,
            "lesionNamingNumber": self.lesionNamingNumber,
            "measurementNumber": self.measurementNumber,
            "timepointId": self.timepointId,
            "patientId": self.patientId
        }

        return output_dict

    def append_to_container(self, container):

        info = container.info

        roi_dict = self.to_dict()
        clean_dict = fu.cleanse_the_filthy_numpy(roi_dict)

        if self.namespace not in info:
            info[self.namespace] = {}
        if "measurements" not in info[self.namespace]:
            info[self.namespace]["measurements"] = {}
        if self.toolType not in info[self.namespace]["measurements"]:
            info[self.namespace]["measurements"][self.toolType] = []

        if not isinstance(info[self.namespace]["measurements"][self.toolType], list):
            log.info("namespace (ROI type) is not list.  Resetting")
            info[self.namespace]["measurements"][self.toolType] = [clean_dict]
        else:

            log.info("Appending to namespace (ROI type)")
            info[self.namespace]["measurements"][self.toolType].append(clean_dict)

        log.info("updating container...")

        container.update_info(info)

        pass
