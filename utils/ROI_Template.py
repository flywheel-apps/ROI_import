import flywheel
import logging
import math
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

# CONSTANTS FOR COLUMN HEADERS for user input only
# There were some differences between these and the actual metadata keys that they would
# become, but I have removed most of those.  Should I just combine anything that's
# redundant (header value = keyword value?) or keep these separate?
# I think yes...so it's clear what keywords are supported by the template and which
# aren't



# @dataclass
# class Property:
#     roi: str = None
#     csv: str = ""
#     value: Any = None
#
#     def __post_init__(self):
#         # If only a single value is passed in, we assume the key is the same for both the ROI and the CSV.
#         if isinstance(self.roi, str) and self.csv == "":
#             self.csv = self.roi
#
#
#
#
# # These are for identifying columns in the CSV, they only exist in the CSV:
# GROUP = Property("group")
# PROJECT = Project("project")
# SUBJECT = Property("subject")
# SESSION = Property("session")
# FILE = Property("file")
# FILETYPE = Property("file type")
#
# MAPPING_COLUMN = FILE.csv
#
# # These properties are actually used in both (or rather are actual ROI properties to be coppied)
# ACTIVE = Property("active")
# LOCATION = Property("location")
# DESCRIPTION = Property("description")
# XMIN = Property('x',"x min")
# XMAX = Property("x","x max")
# YMIN = Property("y","y min")
# YMAX = Property("y","y max")
# USERORIGIN = Property("user origin")
# VISIBLE = Property("visible")
# ROITYPE = Property("toolType","roi type")
# HIGHLIGHT = Property("highlight")
# HEIGHT = Property("height")
# LEFT = Property("left")
# RIGHT = Property("right")
# TOP = Property("top")
# WIDTH = Property("width")
#
#
# ALLOWEDOUTSIDE = Property("allowedOutsideImage")
# DRAWNINDEPENDENTLY = Property("drawnIndependently")
# HASBOUNDINGBOX = Property("hasBoundingBox")
# HASMOVED = Property("hasMoved")
# MOVESINDEPENDENTLY = Property("movesIndependently")
# INITIALROTATION = Property("initialRotation")
#
# AREA = Property("area")
# COUNT = Property("count")
# MAX = Property("max")
# MEAN = Property("mean")
# MIN = Property("min")
# STDDEV = Property("stdDev")
# VARIANCE = Property("variance")
#
# HANDLE = Property("handles", None)
# SERIESINSTANCEUID = Property("SeriesInstanceUID")
# SOPINSTANCEUID = Property("SOPInstanceUID")
# STUDYINSTANCEUID = Property("StudyInstanceUID")





# Suffix _HDR means this  comes from the input file
ACTIVE_HDR = "active"
GROUP_HDR = "group"
PROJECT_HDR = "project"
SUBJECT_HDR = "subject"
SESSION_HDR = "session"
FILE_HDR = "file"
DICOMMEMBER_HDR = "dicom_member"

MAPPING_COLUMN = FILE_HDR

FILETYPE_HDR = "file type"
LOCATION_HDR = "location"
DESCRIPTION_HDR = "description"
XMIN_HDR = "x min"
XMAX_HDR = "x max"
YMIN_HDR = "y min"
YMAX_HDR = "y max"
USERORIGIN_HDR = "user origin"
VISIBLE_HDR = "visible"
ROITYPE_HDR = "roi type"
HIGHLIGHT_HDR = "highlight"
HEIGHT_HDR = "height"
LEFT_HDR = "left"
RIGHT_HDR = "right"
TOP_HDR = "top"
WIDTH_HDR = "width"


ALLOWEDOUTSIDE_HDR = "allowedOutsideImage"
DRAWNINDEPENDENTLY_HDR = "drawnIndependently"
HASBOUNDINGBOX_HDR = "hasBoundingBox"
HASMOVED_HDR = "hasMoved"
MOVESINDEPENDENTLY_HDR = "movesIndependently"
INITIALROTATION_HDR = "initialRotation"


AREA_HDR = "area"
COUNT_HDR = "count"
MAX_HDR = "max"
MEAN_HDR = "mean"
MIN_HDR = "min"
STDDEV_HDR = "stdDev"
VARIANCE_HDR = "variance"

SERIESINSTANCEUID_HDR = "SeriesInstanceUID"
SOPINSTANCEUID_HDR = "SOPInstanceUID"
STUDYINSTANCEUID_HDR = "StudyInstanceUID"


# suffix _KWD means These are KEYWORDS for the metadata.
RECTANGLE_KWD = "RectangleRoi"
ELLIPTICAL_KWD = "EllipticalRoi"

VALIDROI_KWD = [RECTANGLE_KWD, ELLIPTICAL_KWD]


HIGHLIGHT_KWD = "highlight"
X_KWD = "x"
Y_KWD = "y"
HEIGHT_KWD = "height"
LEFT_KWD = "left"
RIGHT_KWD = "right"
TOP_KWD = "top"
WIDTH_KWD = "width"
ACTIVE_KWD = "active"
VISIBLE_KWD = VISIBLE_HDR
ROITYPE_KWD = "toolType"
DESCRIPTION_KWD = DESCRIPTION_HDR
LOCATION_KWD = LOCATION_HDR
USERORIGIN_KWD = USERORIGIN_HDR

ALLOWEDOUTSIDE_KWD = "allowedOutsideImage"
DRAWNINDEPENDENTLY_KWD = "drawnIndependently"
HASBOUNDINGBOX_KWD = "hasBoundingBox"
HASMOVED_KWD = "hasMoved"
MOVESINDEPENDENTLY_KWD = "movesIndependently"
BOUNDINGBOX_KWD = "boundingBox"

START_KWD = "start"
END_KWD = "end"
TEXTBOX_KWD = "textBox"
INITIALROTATION_KWD = "initialRotation"

AREA_KWD = "area"
COUNT_KWD = "count"
MAX_KWD = "max"
MEAN_KWD = "mean"
MIN_KWD = "min"
STDDEV_KWD = "stdDev"
VARIANCE_KWD = "variance"

HANDLE_KWD = "handles"
SERIESINSTANCEUID_KWD = "SeriesInstanceUID"
SOPINSTANCEUID_KWD = "SOPInstanceUID"
STUDYINSTANCEUID_KWD = "StudyInstanceUID"

PATIENTID_KWD = "PatientID"
CACHEDSTATS_KWD = "cachedStats"
TIMEPOINTID_KWD = "timepointId"
FLYWHEELORIGIN_KWD = "flywheelOrigin"

LESIONNAMINGNUMBER_KWD = "lesionNamingNumber"
MEASUREMENTNUMBER_KWD = "measurementNumber"

IMPORTMETHOD_KWD = "ImportMethod"


MEASUREMENTS_KWD = "measurements"

NAMESPACE_KWD = "ohifViewer"

MOVING_KWD = "moving"
USERID_KWD = "userId"

IMAGEPATH_KWD = "imagePath"
UUID_KWD = "uuid"
ID_KWD = "_id"

FORBIDDEN_KWD = [IMAGEPATH_KWD, UUID_KWD, ID_KWD]

MANDATORY_KWD = [
    HANDLE_KWD,
    SERIESINSTANCEUID_KWD,
    SOPINSTANCEUID_KWD,
    STUDYINSTANCEUID_KWD,
    ROITYPE_KWD,
]


class BoundingBox:
    def __init__(self, **kwargs):
        # Initialize to a kind of "catch all" value (good for many use cases)
        # Determined empirically
        self.height = kwargs.get(HEIGHT_KWD, 45)
        self.left = kwargs.get(LEFT_KWD, 400)
        self.top = kwargs.get(TOP_KWD, 150)
        self.width = kwargs.get(WIDTH_KWD, 250)

    def to_dict(self):
        output_dict = {
            HEIGHT_KWD: self.height,
            LEFT_KWD: self.left,
            TOP_KWD: self.top,
            WIDTH_KWD: self.width,
        }

        return output_dict


class Coords:
    def __init__(self, x=0.0, y=0.0, active=False, highlight=None):
        self.x = x
        self.y = y
        self.active = active
        self.highlight = highlight

    def to_dict(self):
        output_dict = {
            X_KWD: self.x,
            Y_KWD: self.y,
            ACTIVE_KWD: self.active,
            HIGHLIGHT_KWD: self.highlight,
        }

        if self.highlight is None:
            trash = output_dict.pop(HIGHLIGHT_KWD)

        return output_dict


class TextBox:
    def __init__(self, **kwargs):
        self.coords = Coords(
            kwargs.get(X_KWD), kwargs.get(Y_KWD), kwargs.get(ACTIVE_KWD)
        )
        self.allowedOutsideImage = kwargs.get(ALLOWEDOUTSIDE_KWD, True)
        self.drawnIndependently = kwargs.get(DRAWNINDEPENDENTLY_KWD, True)
        self.hasBoundingBox = kwargs.get(HASBOUNDINGBOX_KWD, True)
        self.hasMoved = kwargs.get(HASMOVED_KWD, False)
        self.movesIndependently = kwargs.get(MOVESINDEPENDENTLY_KWD, False)
        self.boundingBox = BoundingBox(**kwargs.get(BOUNDINGBOX_KWD, {}))
        self.active = kwargs.get(ACTIVE_KWD, False)

    def to_dict(self):
        output_dict = {
            ALLOWEDOUTSIDE_KWD: self.allowedOutsideImage,
            DRAWNINDEPENDENTLY_KWD: self.drawnIndependently,
            HASBOUNDINGBOX_KWD: self.hasBoundingBox,
            HASMOVED_KWD: self.hasMoved,
            MOVESINDEPENDENTLY_KWD: self.movesIndependently,
            BOUNDINGBOX_KWD: self.boundingBox.to_dict(),
            ACTIVE_KWD: self.active,
        }
        output_dict.update(self.coords.to_dict())

        return output_dict


class Handle:
    def __init__(self, **kwargs):
        self.handle_args = [START_KWD, END_KWD, TEXTBOX_KWD, INITIALROTATION_KWD]

        if START_KWD not in kwargs or END_KWD not in kwargs:
            log.error(f"ROI requires both '{START_KWD}' and '{END_KWD}'")
            pass

        start = kwargs.get(START_KWD, {})
        log.debug("start:")
        log.debug(start)
        self.start = Coords(
            start.get(X_KWD), start.get(Y_KWD), start.get(ACTIVE_KWD, False)
        )
        self.start.highlight = start.get(HIGHLIGHT_KWD, True)

        end = kwargs.get(END_KWD, {})
        log.debug("end:")
        log.debug(end)
        self.end = Coords(end.get(X_KWD), end.get(Y_KWD), end.get(ACTIVE_KWD, False))
        self.end.highlight = end.get(HIGHLIGHT_KWD, True)

        text = kwargs.get(TEXTBOX_KWD, {})
        if X_KWD not in text:
            text[X_KWD] = start.get(X_KWD)
        if Y_KWD not in text:
            text[Y_KWD] = start.get(Y_KWD) - (start.get(Y_KWD) - end.get(Y_KWD)) / 2.0
        self.textBox = TextBox(**text)

        self.initialRotation = kwargs.get(INITIALROTATION_KWD, 0)

    def to_dict(self):

        output_dict = {
            START_KWD: self.start.to_dict(),
            END_KWD: self.end.to_dict(),
            TEXTBOX_KWD: self.textBox.to_dict(),
            INITIALROTATION_KWD: self.initialRotation,
        }
        return output_dict


class Cached_stats:
    def __init__(self, handle, kwargs):

        x_limits = (handle.start.x, handle.end.x)
        y_limits = (handle.start.y, handle.end.y)

        xmax = max(x_limits)
        ymax = max(y_limits)

        xmin = min(x_limits)
        ymin = min(y_limits)

        if AREA_KWD in kwargs:
            self.area = kwargs[AREA_KWD]
        else:
            self.area = (xmax - xmin) * (ymax - ymin)

        if COUNT_KWD in kwargs:
            self.count = kwargs[COUNT_KWD]
        else:
            self.count = (round(xmax) - round(xmin)) * (round(ymax) - round(ymin))

        self.max = kwargs.get(MAX_KWD, 0)
        self.min = kwargs.get(MIN_KWD, 0)
        self.mean = kwargs.get(MEAN_KWD, 0)
        self.stdDev = kwargs.get(STDDEV_KWD, 0)
        self.variance = kwargs.get(VARIANCE_KWD, 0)

    def to_dict(self):
        output_dict = {
            AREA_KWD: self.area,
            COUNT_KWD: self.count,
            MAX_KWD: self.max,
            MEAN_KWD: self.mean,
            MIN_KWD: self.min,
            STDDEV_KWD: self.stdDev,
            VARIANCE_KWD: self.variance,
        }
        return output_dict


class ROI:
    """
    ROI class that essentially stores all the information you need to make and ROI and
    has the ability to spit it back out as a dict.  Since it takes a dictionary as an input,
    this is a little redundant, but I honestly thought this would be a more complicated process.
    """

    def __init__(self):

        log.info("Initializing ROI")

        self.mandatory_keys = MANDATORY_KWD

        self.forbidden_keys = FORBIDDEN_KWD
        self.namespace = NAMESPACE_KWD

        self.handle = None
        self.seriesInstanceUid = None
        self.sopInstanceUid = None
        self.studyInstanceUid = None
        self.imagePath = None

        self.patientId = None
        self.toolType = None

        # Some important values we'll call out specifically for consistency
        self.visible = False
        self.active = False
        self.description = None
        self.location = None
        self.flywheelOrigin = None
        self.lesionNamingNumber = None
        self.measurementNumber = None
        self.timepointId = None
        self.cachedStats = None
        self.userId = None
        self.uuid = ""
        self.id = ""
        self.kwargs = None
        self.valid = True

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

        self.handle = Handle(**kwargs.pop(HANDLE_KWD, {}))
        self.seriesInstanceUid = kwargs.pop(SERIESINSTANCEUID_KWD)
        self.sopInstanceUid = kwargs.pop(SOPINSTANCEUID_KWD)
        self.studyInstanceUid = kwargs.pop(STUDYINSTANCEUID_KWD)
        self.patientId = kwargs.pop(PATIENTID_KWD)

        self.toolType = kwargs.pop(ROITYPE_KWD)
        if self.toolType.lower() not in [roi.lower() for roi in VALIDROI_KWD]:
            log.warning(f'INVALID ROI TYPE {self.toolType}')
            self.valid = False

        self.imagePath = self.generate_imagePath()

        # Some important values we'll call out specifically for consistency
        self.visible = kwargs.pop(VISIBLE_KWD, True)
        self.active = kwargs.pop(ACTIVE_KWD, False)
        self.description = kwargs.pop(DESCRIPTION_KWD, None)
        self.location = kwargs.pop(LOCATION_KWD, None)

        fw_origin = dict()
        if USERORIGIN_KWD in kwargs:
            fw_origin["type"] = "user"
            fw_origin["id"] = kwargs.pop(USERORIGIN_KWD)
        else:
            fw_origin["type"] = "gear"
            fw_origin["id"] = "CSV to ROI Gear"

        self.flywheelOrigin = fw_origin
        self.lesionNamingNumber = kwargs.pop(LESIONNAMINGNUMBER_KWD)
        self.measurementNumber = kwargs.pop(MEASUREMENTNUMBER_KWD)
        self.timepointId = kwargs.pop(TIMEPOINTID_KWD)
        self.cachedStats = Cached_stats(self.handle, kwargs.pop(CACHEDSTATS_KWD, {}))
        self.userId = kwargs.pop(USERID_KWD, "")
        self.uuid = kwargs.pop(UUID_KWD, "")
        # self.id = ?

        self.kwargs = kwargs

    def to_dict(self):

        output_dict = {
            HANDLE_KWD: self.handle.to_dict(),
            CACHEDSTATS_KWD: self.cachedStats.to_dict(),
            FLYWHEELORIGIN_KWD: self.flywheelOrigin,
            SERIESINSTANCEUID_KWD: self.seriesInstanceUid,
            SOPINSTANCEUID_KWD: self.sopInstanceUid,
            STUDYINSTANCEUID_KWD: self.studyInstanceUid,
            IMAGEPATH_KWD: self.imagePath,
            VISIBLE_KWD: self.visible,
            DESCRIPTION_KWD: self.description,
            LOCATION_KWD: self.location,
            ROITYPE_KWD: self.toolType,
            LESIONNAMINGNUMBER_KWD: self.lesionNamingNumber,
            MEASUREMENTNUMBER_KWD: self.measurementNumber,
            TIMEPOINTID_KWD: self.timepointId,
            PATIENTID_KWD: self.patientId,
            ACTIVE_KWD: self.active,
            USERID_KWD: self.userId,
            UUID_KWD: self.uuid,
            ID_KWD: self.id,
            IMPORTMETHOD_KWD: "import-rois"
        }

        return output_dict

    def append_to_container(self, container):

        if not self.valid:
            log.warning("Not updating invalid ROI")
            return False

        info = container.info

        roi_dict = self.to_dict()
        clean_dict = fu.cleanse_the_filthy_numpy(roi_dict)

        if self.namespace not in info:
            info[self.namespace] = {}
        if MEASUREMENTS_KWD not in info[self.namespace]:
            info[self.namespace][MEASUREMENTS_KWD] = {}
        if self.toolType not in info[self.namespace][MEASUREMENTS_KWD]:
            info[self.namespace][MEASUREMENTS_KWD][self.toolType] = []

        if not isinstance(info[self.namespace][MEASUREMENTS_KWD][self.toolType], list):
            log.info(f"namespace {self.toolType} is not list.  Resetting")
            info[self.namespace][MEASUREMENTS_KWD][self.toolType] = [clean_dict]
        else:

            if self.found_duplicate_roi(info[self.namespace][MEASUREMENTS_KWD][self.toolType]):
                log.warning('Will not add duplicate')
                return False
            else:
                log.info(f"Appending to namespace {self.toolType}")
                info[self.namespace][MEASUREMENTS_KWD][self.toolType].append(clean_dict)

        log.info("updating container...")

        container.update_info(info)

        return True


    def found_duplicate_roi(self, existing_rois):

        # We truncate to a length of 4, because sometimes an ROI will have a very long floating point coordinate
        # Value, but when the user loads this into excel, it truncates it to like 6 or 8 decimal places, so we assume
        # that 4 decimal places is small enough to be unique and still catch duplicates even with excell truncating.
        n = 4
        my_x1 = self.handle.start.x
        my_y1 = self.handle.start.y
        my_x2 = self.handle.end.x
        my_y2 = self.handle.end.y

        my_coords = [my_x1, my_y1, my_x2, my_y2]
        my_coords = [truncate(c, n) for c in my_coords]

        for roi in existing_rois:
            roi_x1 = roi.get('handles', {}).get('start', {}).get('x', 0.0)
            roi_y1 = roi.get('handles', {}).get('start', {}).get('y', 0.0)
            roi_x2 = roi.get('handles', {}).get('end', {}).get('x', 0.0)
            roi_y2 = roi.get('handles', {}).get('end', {}).get('y', 0.0)

            roi_coords = [roi_x1, roi_x2, roi_y1, roi_y2]
            roi_coords = [truncate(c, n) for c in roi_coords]

            duplicated = [mc in roi_coords for mc in my_coords]

            if all(duplicated):
                log.warning('Found duplicate ROI (coordinates match out to 4 decimal places)')
                return True

        return False


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n