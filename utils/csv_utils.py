import logging

from utils import flywheel_helpers as fh
from utils.ROI_Template import ROI
import utils.fwobject_utils as fu

log = logging.getLogger("__main__")
MAPPING_COLUMN = "img_file_name"


def get_handle_from_row(series):
    start_dict = {
        "x": panda_pop(series, "X_min"),
        "y": panda_pop(series, "Y_min"),
        "active": panda_pop(series, "active", True),
        "highlight": panda_pop(series, "highlight", False),
    }
    print(start_dict)
    end_dict = {
        "x": panda_pop(series, "X_max"),
        "y": panda_pop(series, "Y_max"),
        "active": panda_pop(series, "active", True),
        "highlight": panda_pop(series, "highlight", False),
    }

    bounding_dict = {
        "height": panda_pop(series, "height", 45),
        "left": panda_pop(series, "left", 400),
        "top": panda_pop(series, "top", 150),
        "width": panda_pop(series, "width", 250),
    }

    textbox_dict = {
        "allowedOutsideImage": panda_pop(series, "allowedOutsideImage", True),
        "drawnIndependently": panda_pop(series, "drawnIndependently", True),
        "hasBoundingBox": panda_pop(series, "hasBoundingBox", True),
        "hasMoved": panda_pop(series, "hasMoved", False),
        "movesIndependently": panda_pop(series, "movesIndependently", False),
        "boundingBox": bounding_dict,
    }

    handle_dict = {
        "start": start_dict,
        "end": end_dict,
        "initialRotation": panda_pop(series, "initialRotation", 0),
        "textBox": textbox_dict,
    }

    if "Handle" in series:
        log.warning("Column name <Handle> is reserved.  Data will not be uploaded.")
        series.pop("Handle")

    return handle_dict


def panda_pop(series, key, default=None):
    if key in series:
        return series.pop(key)
    else:
        return default


def get_roi_from_row(series, file, session):

    handle = get_handle_from_row(series)
    id_dict = fu.get_uids_from_filename(file)

    for k in id_dict.keys():
        panda_pop(series, k)

    roi_dict = {"Handle": handle}
    roi_dict.update(id_dict)
    roi_dict.update(series)
    roi_dict['patientId'] = file.info.get('PatientID')
    
    roi_number_dict = fu.get_roi_number(session, roi_dict.get('ROI_type'))
    roi_dict.update(roi_number_dict)
    roi_dict['timepointId'] = 'TimepointId'
    
    roi = ROI()
    roi.roi_from_dict(**roi_dict)

    return roi


def save_df_to_csv(df, output_dir):
    output_path = output_dir / "Data_Import_Status_report.csv"
    df.to_csv(output_path, index=False)


def get_fw_path(series):

    object_name = series.get(MAPPING_COLUMN)
    group_name = series.get("Group")
    project_name = series.get("Project")
    subject_label = series.get("Subject")
    session_label = series.get("Sessionl")

    return object_name, group_name, project_name, subject_label, session_label
