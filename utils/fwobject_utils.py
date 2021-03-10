import collections.abc
import numpy as np

import logging

from utils import flywheel_helpers as fh

log = logging.getLogger("__main__")


def get_uids_from_filename(file):
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
    
    session = session.reload()
    sinfo = session.info

    if (
        "ohifViewer" in sinfo
        and "measurements" in sinfo["ohifViewer"]
        and roi_type in sinfo["ohifViewer"]["measurements"]
    ):

        rois = sinfo["ohifViewer"]["measurements"][roi_type]
        if len(rois) == 0:
            new_num = 1

        else:
            lesion_nums = [r.get("lesionNamingNumber", -1) for r in rois]
            meausrement_nums = [r.get("measurementNumber", -1) for r in rois]

            mlesion = max(lesion_nums)
            mnum = max(meausrement_nums)

            new_num = max([mlesion, mnum])
            new_num += 1

    else:
        new_num = 1

    number_dict = {"lesionNamingNumber": new_num, "measurementNumber": new_num}
    
    return number_dict


def get_objects_for_processing(fw, container, level, get_files):
    log.debug(f"Got container {container.label}")
    child_containers = fh.get_containers_at_level(fw, container, level)
    log.debug(f"Initial Pass: found {len(child_containers)} containers")
    if get_files:
        resulting_containers = []
        for cc in child_containers:
            resulting_containers.extend(
                fh.get_containers_at_level(fw, cc.reload(), "file")
            )

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
    for k, v in dict.items():
        if isinstance(v, collections.abc.Mapping):
            log.info(f"descending into {v}")
            dict[k] = cleanse_the_filthy_numpy(dict.get(k, {}))
        else:
            # Flywheel doesn't like numpy data types:
            if type(v).__module__ == np.__name__:
                v = v.item()
                dict[k] = v
    return dict
