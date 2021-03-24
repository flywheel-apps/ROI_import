import logging

from utils import flywheel_helpers as fh
from utils.ROI_Template import ROI
import utils.fwobject_utils as fu

log = logging.getLogger("__main__")
MAPPING_COLUMN = "File"


def get_handle_from_row(series):
    """Generate the flywheel handle from the series.
    
    The only truly "required" columns needed to create a handle from the series are:
    X min
    Y min
    X max
    Y max
    
    Args:
        series (pandas.Series): a row from a dataframe describing an ROI

    Returns:
        handle_dict (dict): a nested dictionary object mirroring the "handle" object
            used for the flywheel ROI metadata

    """
    start_dict = {
        "x": panda_pop(series, "X min"),
        "y": panda_pop(series, "Y min"),
        "active": panda_pop(series, "active", True),
        "highlight": panda_pop(series, "highlight", False),
    }

    end_dict = {
        "x": panda_pop(series, "X max"),
        "y": panda_pop(series, "Y max"),
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

    # This summarizes the final form of the dictionary.
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
    """recreate the behavior of a dictionary "pop" for a pandas series
    
    behavior:
    if element exists, return the value and remove the element
    if the element doesn't exist, return the default
    the default default is "None"
    
    Args:
        series (pandas.Series): The series to pop from
        key (string): the key to look for and pop
        default (anything): the default value to return if the key isn't present

    Returns:

    """
    if key in series:
        return series.pop(key)
    else:
        return default


def get_roi_from_row(series, file, session):
    """Generate the dictionaries from a pandas series to create the ROI in flywheel
    
    Args:
        series (pandas.Series): a row from a dataframe describing an ROI
        file (flywheel.File): a flywheel file to attach the ROI to
        session (flywheel.Session): the parent session of the file

    Returns:
        roi (ROI_Template.ROI): a custom ROI object

    """

    # Get the handle from the row.  The handle contains the x/y bounds of the ROI
    handle = get_handle_from_row(series)

    id_dict = fu.get_uids_from_filename(file)

    for k in id_dict.keys():
        panda_pop(series, k)

    roi_dict = {"Handle": handle}
    roi_dict.update(id_dict)
    roi_dict.update(series)
    roi_dict["patientId"] = file.info.get("PatientID")

    roi_number_dict = fu.get_roi_number(session, roi_dict.get("ROI type"))
    roi_dict.update(roi_number_dict)
    roi_dict["timepointId"] = "TimepointId"

    roi = ROI()
    roi.roi_from_dict(**roi_dict)

    return roi


def save_df_to_csv(df, output_dir):
    """saves a dataframe to the specified output directory with the name "Data_Import_Status_Report.csv"
    
    Args:
        df (pandas.DataFrame): the dataframe to save
        output_dir (Pathlike): the directory to save to

    Returns:

    """
    output_path = output_dir / "Data_Import_Status_report.csv"
    df.to_csv(output_path, index=False)


def get_fw_path(series):
    """A function to consolidate the extraction of the fw object's location
    
    Args:
        series (pandas.Series): a pandas series, which is a single row from the ROI
            dataframe

    Returns:
        object_name (string): The file name of the file to attach the ROI to
        group_name (string): The group that the object belongs to
        project_name (string): The project that the object belongs to
        subject_label (string): The subject that the object belongs to
        session_label (string): The session that the object belongs to
    """

    object_name = series.get(MAPPING_COLUMN)
    group_name = series.get("Group")
    project_name = series.get("Project")
    subject_label = series.get("Subject")
    session_label = series.get("Session")
    return object_name, group_name, project_name, subject_label, session_label
