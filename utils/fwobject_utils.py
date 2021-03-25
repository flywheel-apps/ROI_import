import collections.abc
import numpy as np

import logging

from utils import flywheel_helpers as fh

log = logging.getLogger("__main__")


def get_uids_from_filename(file):
    """Extract the UUID's of the file and generate a path for the ROI
    
    This is how the OHIF viewer links ROI's to files in flywheel.
    
    Args:
        file (flywheel.File): A DICOM file to extract UID's from

    Returns:
        id_dict (dict): a dictionary containing the ID's necessary to link the ROI to the file.

    """
    id_dict = {
        "SeriesInstanceUID": None,
        "SOPInstanceUID": None,
        "StudyInstanceUID": None,
    }

    for id in id_dict.keys():
        value = file.info.get(id)
        id_dict[id] = value
        log.info(f"Found {value} for {id}")
    return id_dict


def get_roi_number(session, roi_type):
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
    if (
        "ohifViewer" in sinfo
        and "measurements" in sinfo["ohifViewer"]
        and roi_type in sinfo["ohifViewer"]["measurements"]
    ):

        # See how many ROI's there are already present of this type
        rois = sinfo["ohifViewer"]["measurements"][roi_type]
        if len(rois) == 0:
            # If it's zero, we start at one.
            new_num = 1

        else:
            # sometimes things can get wonky so we just look at the maximum of the two possible
            # items that are used to assign ROI numbers
            lesion_nums = [r.get("lesionNamingNumber", -1) for r in rois]
            meausrement_nums = [r.get("measurementNumber", -1) for r in rois]

            mlesion = max(lesion_nums)
            mnum = max(meausrement_nums)

            new_num = max([mlesion, mnum])
            new_num += 1

    # if that metadata object doesn't exist we will create it later, for now we're measurement 1
    else:
        new_num = 1

    number_dict = {"lesionNamingNumber": new_num, "measurementNumber": new_num}

    return number_dict


def get_objects_for_processing(fw, container, level, get_files):
    """Returns flywheel child containers of files.
    
    Gets all containers at a certain level (or files of containers at a certain level) that are
    children of a given flywheel container.
    
    Args:
        fw (flywheel.Client): the flywheel SDK Client
        container (flywheel.ContainerReference): a flywheel container. This will be the "parent"
            container that child containers or files at a given level will be collected and
            returned.
        level (string): the level of child container to return to (session, acquisition, etc)
        get_files (boolean): If True, return the files attached to the containers at `level`.
            If false, return the containers themselves at `level`

    Returns:
        resulting_containers (list): a list of containers or files

    """

    log.debug(f"Got container {container.label}")
    # Use the flywheel helper to get the containers at "level"
    child_containers = fh.get_containers_at_level(fw, container, level)
    log.debug(f"Initial Pass: found {len(child_containers)} containers")

    # If we are also getting the files from those, loop through and concatenate all files to return
    if get_files:
        resulting_containers = []
        for cc in child_containers:
            resulting_containers.extend(
                fh.get_containers_at_level(fw, cc.reload(), "file")
            )

    # Otherwise just return the containers we found
    else:
        resulting_containers = child_containers

    log.debug(f"Final Pass: found {len(child_containers)} containers:")
    for cc in resulting_containers:
        if get_files:
            log.debug(f"{cc.name}")
        else:
            log.debug(f"{cc.label}")

    return resulting_containers


def expand_metadata(meta_string, container):
    metas = meta_string.split(".")
    ct = container.container_type
    name = fh.get_name(container)

    first = metas.pop(0)
    val = getattr(container, first)
    temp_container = val
    for meta in metas:
        val = temp_container.get(meta)
        if val:
            temp_container = val
        else:
            log.warning(f"No metadata value {meta_string} found for {ct} {name}")
            return None
    return val


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
