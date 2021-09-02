import collections.abc
import numpy as np

import logging

from utils import ROI_Template as ROI

log = logging.getLogger(__name__)


def get_uids_from_filename(file):
    """Extract the UUID's of the file and generate a path for the ROI

    This is how the OHIF viewer links ROI's to files in flywheel.

    Args:
        file (flywheel.File): A DICOM file to extract UID's from

    Returns:
        id_dict (dict): a dictionary containing the ID's necessary to link the ROI to the file.

    """
    id_dict = {
        ROI.SERIESINSTANCEUID_KWD: file.info.get(ROI.SERIESINSTANCEUID_HDR),
        ROI.SOPINSTANCEUID_KWD: file.info.get(ROI.SOPINSTANCEUID_HDR),
        ROI.STUDYINSTANCEUID_KWD: file.info.get(ROI.STUDYINSTANCEUID_HDR),
    }

    for id, value in id_dict.items():
        log.info(f"Found {value} for {id}")

    return id_dict


# def get_roi_number(session, roi_type):
def get_roi_number(session):
    """Gets the ROI number from a session if there are previously existing ROI's

    Args:
        session (flywheel.Session): the session that we are adding an ROI to
        roi_type (string): The type of ROI we're adding.

    Returns:
        number_dict (dict): a dictionary with the values needed to properly number the new ROI
    """

    session = session.reload()
    sinfo = session.info

    # If the session has the metadata object "ohifViewer.measurements.<roi_type>":
    # Updated to count ALL roi's to determine ROI number -
    # as of 06/01/2021 this is how I think it works ( as far as I can tell)
    lesion_count = []
    roi_count = []

    if ROI.NAMESPACE_KWD in sinfo and ROI.MEASUREMENTS_KWD in sinfo[ROI.NAMESPACE_KWD]:
        # and roi_type in sinfo[ROI.NAMESPACE_KWD][ROI.MEASUREMENTS_KWD]
        # ):

        roi_count = [
            rc.get(ROI.MEASUREMENTNUMBER_KWD, 0)
            for roitype in sinfo[ROI.NAMESPACE_KWD][ROI.MEASUREMENTS_KWD]
            for rc in sinfo[ROI.NAMESPACE_KWD][ROI.MEASUREMENTS_KWD][roitype]
            if rc
        ]
        lesion_count = [
            rc.get(ROI.LESIONNAMINGNUMBER_KWD, 0)
            for roitype in sinfo[ROI.NAMESPACE_KWD][ROI.MEASUREMENTS_KWD]
            for rc in sinfo[ROI.NAMESPACE_KWD][ROI.MEASUREMENTS_KWD][roitype]
            if rc
        ]

    if len(roi_count) == 0:
        roi_count = 1
    else:
        roi_count = max(roi_count) + 1

    if len(lesion_count) == 0:
        lesion_count = 1
    else:
        lesion_count = max(lesion_count) + 1

    number_dict = {
        ROI.LESIONNAMINGNUMBER_KWD: lesion_count,
        ROI.MEASUREMENTNUMBER_KWD: roi_count,
    }

    return number_dict


def get_session_files(fw, session):
    log.debug('getting session acquisition files')
    for acq in session.acquisitions.iter():
        acq = acq.reload()
        for file_ in acq.files:
            yield file_

def filter_matches(objects, name, file_type):
    name_w_file_type = name + f".{file_type}"
    for obj in objects:
        if obj.get("name") == name or obj.get("name") == name_w_file_type:
            yield obj


def update(d, u, overwrite):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v, overwrite)
        else:
            # Flywheel doesn't like numpy data types:
            if type(v).__module__ == np.__name__:
                v = v.item()

            log.debug(f'checking if "{k}" in {d.keys()}')
            if k in d:
                if overwrite:
                    log.debug(f'Overwriting "{k}" from "{d[k]}" to "{v}"')
                    d[k] = v
                else:
                    log.debug(f'"{k}" present.  Skipping.')
            else:
                log.debug(f"setting {k}")
                d[k] = v

    return d


def cleanse_the_filthy_numpy(dict):
    """change inputs that are numpy classes to python classes

    when you read a csv with Pandas, it makes "int" "numpy_int", and flywheel doesn't like that.
    Does the same for floats and bools, I think.  This fixes it

    Args:
        dict (dict): a dict

    Returns:
        dict (dict): a dict made of only python-base classes.

    """
    for k, v in dict.items():
        if isinstance(v, collections.abc.Mapping):
            dict[k] = cleanse_the_filthy_numpy(dict.get(k, {}))
        else:
            # Flywheel doesn't like numpy data types:
            if type(v).__module__ == np.__name__:
                v = v.item()
                dict[k] = v
    return dict
