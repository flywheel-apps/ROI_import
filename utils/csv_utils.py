import logging

import utils.ROI_Template as ROI
import utils.fwobject_utils as fu

log = logging.getLogger("__main__")
MAPPING_COLUMN = ROI.MAPPING_COLUMN


def get_stats_from_row(series):

    stats_dict = {
        ROI.AREA_KWD: panda_pop(series, ROI.AREA_HDR, 0),
        ROI.COUNT_KWD: panda_pop(series, ROI.COUNT_HDR, 0),
        ROI.MAX_KWD: panda_pop(series, ROI.MAX_HDR, 0),
        ROI.MEAN_KWD: panda_pop(series, ROI.MEAN_HDR, 0),
        ROI.MIN_KWD: panda_pop(series, ROI.MIN_HDR, 0),
        ROI.STDDEV_KWD: panda_pop(series, ROI.STDDEV_HDR, 0),
        ROI.VARIANCE_KWD: panda_pop(series, ROI.VARIANCE_HDR, 0),
    }

    return stats_dict


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
        ROI.X_KWD: panda_pop(series, ROI.XMIN_HDR),
        ROI.Y_KWD: panda_pop(series, ROI.YMIN_HDR),
        ROI.ACTIVE_HDR: panda_pop(series, ROI.ACTIVE_HDR, False),
        ROI.HIGHLIGHT_KWD: panda_pop(series, ROI.HIGHLIGHT_HDR, False),
    }

    end_dict = {
        ROI.X_KWD: panda_pop(series, ROI.XMAX_HDR),
        ROI.Y_KWD: panda_pop(series, ROI.YMAX_HDR),
        ROI.ACTIVE_KWD: panda_pop(series, ROI.ACTIVE_HDR, False),
        ROI.HIGHLIGHT_KWD: panda_pop(series, ROI.HIGHLIGHT_HDR, False),
    }

    bounding_dict = {
        ROI.HEIGHT_KWD: panda_pop(series, ROI.HEIGHT_HDR, 45),
        ROI.LEFT_KWD: panda_pop(series, ROI.LEFT_HDR, 400),
        ROI.TOP_KWD: panda_pop(series, ROI.TOP_HDR, 150),
        ROI.WIDTH_KWD: panda_pop(series, ROI.WIDTH_HDR, 250),
    }

    textbox_dict = {
        ROI.ALLOWEDOUTSIDE_KWD: panda_pop(series, ROI.ALLOWEDOUTSIDE_HDR, True),
        ROI.DRAWNINDEPENDENTLY_KWD: panda_pop(series, ROI.DRAWNINDEPENDENTLY_HDR, True),
        ROI.HASBOUNDINGBOX_KWD: panda_pop(series, ROI.HASBOUNDINGBOX_HDR, True),
        ROI.HASMOVED_KWD: panda_pop(series, ROI.HASMOVED_HDR, False),
        ROI.MOVESINDEPENDENTLY_KWD: panda_pop(
            series, ROI.MOVESINDEPENDENTLY_HDR, False
        ),
        ROI.ACTIVE_KWD: panda_pop(series, ROI.ACTIVE_HDR, False),
        # ROI.BOUNDINGBOX_KWD: bounding_dict,
    }

    # This summarizes the final form of the dictionary.
    handle_dict = {
        ROI.START_KWD: start_dict,
        ROI.END_KWD: end_dict,
        ROI.INITIALROTATION_KWD: panda_pop(series, ROI.INITIALROTATION_HDR, 0),
        ROI.TEXTBOX_KWD: textbox_dict,
    }

    log.debug("handle:")
    log.debug(handle_dict)
    if ROI.HANDLE_KWD in series:
        log.warning(
            f"Column name{ROI.HANDLE_KWD} is reserved.  Data will not be uploaded."
        )
        series.pop(ROI.HANDLE_KWD)

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
        file (flywheel.FileEntry): a flywheel file to attach the ROI to
        session (flywheel.Session): the parent session of the file

    Returns:
        roi (ROI_Template.ROI): a custom ROI object

    """

    # Get the handle from the row.  The handle contains the x/y bounds of the ROI
    handle = get_handle_from_row(series)
    stats = get_stats_from_row(series)

    # This currently does not support putting ROI's on a specific slice number (intended for 2D images)
    # That would require either the SOPInstanceUID from the original image or the slice number
    # The problem with the SOPInstanceUID is that sometimes those UID's are hashed when a file is exported to another
    # project using deid-export, so it wouldn't work trying to match them.
    # The problem with slice number is that we'd have to load each and every dicom slice, read the metadata, and try
    # To match the slice number.
    id_dict = fu.get_uids_from_filename(file)

    for k in id_dict.keys():
        panda_pop(series, k)

    roi_dict = {ROI.HANDLE_KWD: handle}
    roi_dict.update(id_dict)

    if ROI.ROITYPE_HDR in series or "ROI type" in series:
        roi_dict[ROI.ROITYPE_KWD] = panda_pop(series, ROI.ROITYPE_HDR)
    else:
        log.warning('Must Specify ROI type with the key "roi type"')

    # This adds all remaining keys to the roi dict.
    roi_dict.update(series)

    roi_dict[ROI.PATIENTID_KWD] = file.info.get("PatientID")
    roi_dict[ROI.CACHEDSTATS_KWD] = stats

    roi_number_dict = fu.get_roi_number(session)
    roi_dict.update(roi_number_dict)
    roi_dict[ROI.TIMEPOINTID_KWD] = "TimepointId"

    roi = ROI.ROI()
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
    group_name = series.get(ROI.GROUP_HDR)
    project_name = series.get(ROI.PROJECT_HDR)
    subject_label = series.get(ROI.SUBJECT_HDR)
    session_label = series.get(ROI.SESSION_HDR)
    return object_name, group_name, project_name, subject_label, session_label
