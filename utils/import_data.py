import collections.abc
import numpy as np
import pprint
from flywheel.rest import ApiException
import flywheel
from dataclasses import dataclass

import logging

import utils.fwobject_utils as fu
import utils.csv_utils as cu
import utils.ROI_Template as ROI

# df_path = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Metadata_import_Errorprone/Data_Entry_2017_test.csv'
# firstrow_spec = 1
#
# sheets_spec = "MRIDataTracker"


log = logging.getLogger("__main__")

@dataclass
class Match:
    file: flywheel.FileEntry = None
    group_label: str = ""
    project_label: str = ""
    subject_label: str = ""
    session_label: str = ""
    acquisition_label: str = ""


    def get_acquisition(self, fw):
        if self.acquisition_label is "" and self.file.parents.acquisition is not None:
            acquisition = fw.get_acquisition(self.file.parents.acquisition)
            append = f"/{acquisition.label}"
        else:
            append = ""

        self.acquisition_label = append


    def path(self):
        return f"{self.group_label}/{self.project_label}/{self.subject_label}/{self.session_label}/{self.acquisition_label}/{self.file.name}"





def import_data(fw, df, group, project, dry_run=False):
    """Imports a pandas DataFrame into flywheel as ROI's

    Args:
        fw (flywheel.Client): the flywheel Client
        df (pandas.DataFrame): The pandas dataframe generated from the input CSV file,
            with the columns described in "Sample.csv"
        group (Flywheel.Group): The group to import the data to.
        project (Flyhweel.Project): The project to import the data to.
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

    group_name = group.id
    project_name = project.label

    ############################################################################
    # STEP 1: Loop through subject/session combos and aggregate file matches  #
    ############################################################################
    # We will first loop through and find any and all matches for each subject/session combination.
    # Group by subject/session combos, to minimize loading.
    unique_subjects = df[ROI.SUBJECT_HDR].unique()
    log.debug(f"{len(unique_subjects)} unique subjects found")
    # We are assuming that the group/project we're running in is the one we want to upload to.
    initial_matching = {}
    # First we will descend into the first unique subject label
    for subject_label in unique_subjects:
        log.debug(f'looking for subject {subject_label}')
        # There may be multiple subjects, but they will all have the same label
        subjects = project.subjects.iter_find(f'label="{subject_label}"')

        # Now we will generate a dataframe group for the unique sessions present in this subject(s)
        session_df = df[df[ROI.SUBJECT_HDR] == subject_label]
        log.debug(f'{len(session_df)} entries for this subject.  Grouping by sessions')
        session_groups = session_df.groupby([ROI.SESSION_HDR])


        # Now we will loop through any subjects we found originally
        for subject in subjects:
            log.debug(f'working on subject {subject.label}')

            # We will loop through our unique session groups
            for session_label, indexs in session_groups.groups.items():
                log.debug(f'looking for session {session_label} - found {len(indexs)} entries')
                # And search for sessions with that label on that subject.
                sessions = subject.sessions.iter_find(f'label="{session_label}"')

                # We may find multiple - it is possible for 2 subjects to have the same label, each with a session with
                #  the same label.
                # Loop through the sessions we find (hopefully only one)
                for session in sessions:
                    log.debug(f'looking for session {session.label}')



                    # With each session, we must now search for each specific file
                    for index in indexs:
                        # Get a list of all files attached to the acquisitions in the session identified
                        # by the object location found above
                        objects_for_processing = fu.get_session_files(fw, session)

                        series = session_df.loc[index]
                        object_name = series.get(ROI.MAPPING_COLUMN)
                        log.debug(f'looking for object {object_name}')

                        lookup_string = f"{group_name}/{project_name}/{subject_label}/{session_label}/{object_name}"

                        matching_files = fu.filter_matches(objects_for_processing, object_name, series.get('file type'))
                        matching_files = [Match(file, group_name, project_name, subject_label, session_label) for file in matching_files]

                        log.debug(f'found {len(matching_files)} matching files')

                        if index in initial_matching:
                            initial_matching[index].extend(matching_files)
                        else:
                            initial_matching[index] = matching_files
                            log.debug(f'adding match {index}, {type(index)}')

    ############################################################################
    # STEP 2: Loop through aggregated matches and ensure there is only one     #
    # Match per row                                                            #
    ############################################################################

    # Now that we have assembled all the possible matches for every index in the dataframe, go through and make sure
    # There aren't duplicates.
    for index in df.index:
        series = df.loc[index]
        log.debug(f'looking for {index} in matches:')

        try:
            if index not in initial_matching:
                log.warning(f'0 matches found for row {index}')
                log.info("\n--------------------------------------------------\n"
                "STATUS: Failed\n"
                "==================================================\n"
                )
                continue

            matches = initial_matching[index]
            if len(matches) != 1:

                log.warning(f'{len(matches)} matches found for index {index}, exactly 1 required')
                log.info("\n--------------------------------------------------\n"
                    "STATUS: Failed\n"
                    "==================================================\n"
                )
                continue

            match = matches[0]
            # Generate a flywheel path to this file.  A little redundant since we
            # already have group/project/subject/session, but this will also find
            # acquisition and file.
            match.get_acquisition(fw)
            # Make this a data property
            address = match.path()

            # We write ROI info to the parent Session metadata, so get the containing session
            # of the matching file.
            parent = match.file.parent
            if parent.container_type == "session":
                ses = parent.reload()
            else:
                ses = fw.get_session(parent.parents.session)

            # Get an ROI object from the row using required and optional columns.
            roi = cu.get_roi_from_row(series, match.file, ses)

            # If this gear is a dry run, we'll only log, not actually upload
            if dry_run:
                log.info(f"Would modify info on {address}")
                df.at[index, "Gear_Status"] = "Dry-Run Success"
                df.at[index, "Gear_FW_Location"] = address
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
                    success = roi.append_to_container(ses)
                    if success:
                        success_counter += 1
                        df.at[index, "Gear_Status"] = "Success"
                        df.at[index, "Gear_FW_Location"] = address

                        log.info(
                            "\n--------------------------------------------------\n"
                            "STATUS: Success\n"
                            "==================================================\n"
                        )
                    else:
                        df.at[index, "Gear_Status"] = "Failed"
                        df.at[index, "Gear_FW_Location"] = address

                        log.info(
                            "\n--------------------------------------------------\n"
                            "STATUS: Failed\n"
                            "==================================================\n"
                        )
                        continue

                except Exception as e:
                    log.warning("Error uploading metadata")
                    log.exception(e)
                    continue

        except Exception as e:
            log.warning(
                f"\n--------------------------------------------------\n"
                f"STATUS: Failed\n"
                f"row {index} unable to process for reason: {e}"
                f"==================================================\n"
            )

            log.exception(e)
            continue

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
