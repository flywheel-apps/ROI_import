import collections.abc
import numpy as np
import pprint
from flywheel.rest import ApiException

import logging

from utils import flywheel_helpers as fh
import utils.fwobject_utils as fu
import utils.csv_utils as cu

# df_path = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Metadata_import_Errorprone/Data_Entry_2017_test.csv'
# firstrow_spec = 1
#
# sheets_spec = "MRIDataTracker"


log = logging.getLogger("__main__")


def import_data(fw, df, overwrite=False, dry_run=False):

    nrows, ncols = df.shape
    log.info("Starting Mapping")
    df["Gear_Status"] = "Failed"
    df["Gear_FW_Location"] = None

    if "User_Origin" not in df:
        user = fw.get_current_user()
        user_id = user.id
        df["User_Origin"] = user_id

    success_counter = 0

    for row in range(nrows):

        try:
            series = df.iloc[row]
            series.pop("Gear_Status")
            series.pop("Gear_FW_Location")

            (
                object_name,
                group_name,
                project_name,
                subject_label,
                session_label,
            ) = cu.get_fw_path(series)

            try:
                lookup_string = (
                    f"{group_name}/{project_name}/{subject_label}/{session_label}"
                )
                log.info(f"Checking for location {lookup_string}")
                ses = fw.lookup(lookup_string)
            except ApiException:
                log.error(
                    f"No session found for: {lookup_string}\n please double check.  Skipping "
                )
                continue

            get_files = True
            objects_for_processing = fu.get_objects_for_processing(
                fw, ses, "acquisition", get_files
            )

            log.info(
                f"\n==================================================\n"
                f"Setting Metadata For {object_name}\n"
                f"--------------------------------------------------"
            )
            log.info(series)

            matches = [
                m for m in objects_for_processing if m.get("name") == object_name
            ]

            if len(matches) > 1:
                log.warning(
                    f"Multiple matches for for object name '{object_name}'. "
                    f"please get better at specifying flywheel objects."
                )
                log.info(
                    "\n--------------------------------------------------\n"
                    "STATUS: Failed\n"
                    "==================================================\n"
                )
                continue

            elif len(matches) == 0:
                log.warning(f"No match for object name '{object_name}'.")
                log.info(
                    "\n--------------------------------------------------\n"
                    "STATUS: Failed\n"
                    "==================================================\n"
                )
                continue

            match = matches[0]
            address = fh.generate_path_to_container(fw, match)
            parent = match.parent

            if parent.container_type == "session":
                ses = parent.reload()

            else:
                ses = fw.get_session(parent.parents.session)

            roi = cu.get_roi_from_row(series, match, ses)

            if dry_run:
                log.info(f"Would modify info on {address}")
                df.loc[df.index == row, "Gear_Status"] = "Dry-Run Success"
                df.loc[df.index == row, "Gear_FW_Location"] = address
                log.info(
                    "\n--------------------------------------------------\n"
                    "DRYRUN STATUS: Success\n"
                    "==================================================\n"
                )
                success_counter += 1
            else:

                log.info(f"Creating CSV")
                log.debug(f"{pprint.pprint(roi.to_dict(),indent=2)}")
                df.loc[df.index == row, "Gear_Status"] = "Success"
                df.loc[df.index == row, "Gear_FW_Location"] = address

                log.info(
                    "\n--------------------------------------------------\n"
                    "STATUS: Success\n"
                    "==================================================\n"
                )

                roi.append_to_container(ses)
                success_counter += 1

        except Exception as e:

            log.warning(
                f"\n--------------------------------------------------\n"
                f"DRYRUN STATUS: Failed\n"
                f"row {row} unable to process for reason: {e}"
                f"==================================================\n"
            )

            log.exception(e)

    log.info(
        f"\n\n"
        f"===============================================================================\n"
        f"Final Report: {success_counter}/{nrows} objects updated successfully\n"
        f"{success_counter/nrows*100}%\n"
        f"See output report file for more details\n"
        f"===============================================================================\n"
    )

    return df


# https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
# TODO: Smarter exception handling