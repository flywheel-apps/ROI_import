import collections.abc
import numpy as np
import pprint
from flywheel.rest import ApiException

import logging

from utils import flywheel_helpers as fh
import utils.fwobject_utils as fu
import utils.csv_utils as cu
import utils.ROI_Template as ROI

# df_path = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Metadata_import_Errorprone/Data_Entry_2017_test.csv'
# firstrow_spec = 1
#
# sheets_spec = "MRIDataTracker"


log = logging.getLogger("__main__")


def import_data(fw, df, dry_run=False):
    """Imports a pandas DataFrame into flywheel as ROI's
    
    Args:
        fw (flywheel.Client): the flywheel Client
        df (pandas.DataFrame): The pandas dataframe generated from the input CSV file,
            with the columns described in "Sample.csv"
        dry_run (boolean): Indicates if the data is actually imported (False) or a log
            is made of what would be changed, but no changes are actually made (True)

    Returns:
        df (pandas.DataFrame): The input dataframe, but with two additional columns
            indicating the success or failure of the upload, and the flywheel object
            that the ROI was uploaded to.

    """

    # Initialize the two new columns in the dataframe that indicate if the data was
    # Successfully uploaded or not, and where
    nrows, ncols = df.shape
    log.info("Starting Mapping")
    df["Gear_Status"] = "Failed"
    df["Gear_FW_Location"] = None

    # If the "User Origin" column is not present in the Dataframe, generate it using
    # the user ID of the person running this gear (or logged into the flywheel client)
    if ROI.USERORIGIN_HDR not in df:
        user = fw.get_current_user()
        user_id = user.id
        df[ROI.USERORIGIN_HDR] = user_id

    success_counter = 0

    for row in range(nrows):

        try:

            # Pop the "Gear_Status" and "Gear_FW_Location" elements from the series
            series = df.iloc[row]
            series.pop("Gear_Status")
            series.pop("Gear_FW_Location")

            # Get the location of the object that this series indicates it's targeting.
            (
                object_name,
                group_name,
                project_name,
                subject_label,
                session_label,
            ) = cu.get_fw_path(series)

            try:
                # Generate a lookup string from the object location to locate the
                # group/project/subject/session
                lookup_string = (
                    f"{group_name}/{project_name}/{subject_label}/{session_label}"
                )
                log.info(f"Checking for location {lookup_string}")

                # use flywheel lookup to see if the instance can find the path
                ses = fw.lookup(lookup_string)
                ses=ses.reload()
            except ApiException:
                log.error(
                    f"No session found for: {lookup_string}\n please double check.  Skipping "
                )
                continue

            # This is just creating a human readable variable to pass "True" value to the next
            # function.  This makes it easier to understand what it's doing.
            get_files = True

            # Get a list of all files attached to the acquisitions in the session identified
            # by the object location found above
            objects_for_processing = fu.get_objects_for_processing(
                fw, ses, "acquisition", get_files
            )

            log.info(
                f"\n==================================================\n"
                f"Setting Metadata For {object_name}\n"
                f"--------------------------------------------------\n"
            )
            log.info(series)

            # Find any files that match the name of the file specified in this row of the dataframe
            matches = [
                m for m in objects_for_processing if m.get("name") == object_name
            ]
            
            
            
            if len(matches) == 0:
                log.debug(
                    f"No matches found for {object_name}, appending File type '.{series.get('file type')}'")
                object_name += f".{series.get('File Type')}"
            
            log.debug(f"looking for {object_name}")
            
            matches = [
                m for m in objects_for_processing if m.get("name") == object_name
            ]
            
            # Names must be unique, so warn if there are multiple matches.
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

            # Names must exist, so warn if nothing maches
            elif len(matches) == 0:
                log.warning(f"No match for object name '{object_name}'.")
                log.info(
                    "\n--------------------------------------------------\n"
                    "STATUS: Failed\n"
                    "==================================================\n"
                )
                continue

            # Take the (hopefully) one match
            match = matches[0]

            # Generate a flywheel path to this file.  A little redundant since we
            # already have group/project/subject/session, but this will also find
            # acquisition and file.
            address = fh.generate_path_to_container(fw, match)

            # We write ROI info to the parent Session metadata, so get the containing session
            # of the matching file.
            parent = match.parent
            if parent.container_type == "session":
                ses = parent.reload()

            else:
                ses = fw.get_session(parent.parents.session)

            # Get an ROI object from the row using required and optional columns.
            roi = cu.get_roi_from_row(series, match, ses)

            # If this gear is a dry run, we'll only log, not actually upload
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

            # Otherwise make the ROI
            else:

                log.info(f"Creating ROI")
                log.debug(f"{pprint.pprint(roi.to_dict(),indent=2)}")
                try:
                    # add the ROI to the container.
                    roi.append_to_container(ses)
                    success_counter += 1
                    df.loc[df.index == row, "Gear_Status"] = "Success"
                    df.loc[df.index == row, "Gear_FW_Location"] = address

                    log.info(
                        "\n--------------------------------------------------\n"
                        "STATUS: Success\n"
                        "==================================================\n"
                    )
                except Exception as e:
                    log.warning("Error uploading metadata")
                    log.exception(e)

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
