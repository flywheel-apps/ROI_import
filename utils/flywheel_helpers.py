from pathlib import Path

def get_containers_at_level(fw, container, level):
    """Given a starting container, return parent or children containers of that container.

    Returns a parent, or children of a flywheel container. The level to return is specified
    by the string `level`.  If the level is HIGHER than the container (a parent), that
    single parent is returned.  if the level is LOWER than the container (a child), then
    all children of that type are returned.  The flywheel Container Hierarchy is as follows:

    1. Group
    2. Project
    3. Subject
    4. Session
    5. Acquisition

    Essentially, projects through acquisitions can also have files and analysis' attached to them.

    Args:
        fw (flywheel.Client): flywheel SDK client
        container (flywheel.ContainerReference): A flywheel container (project, session, subject,
        acquisition, analysis)
        level (string): the container level to return.

    Returns:
        containers (list): a list of containers or files

    """
    try:
        ct = container.container_type
    except Exception:
        ct = "analysis"

    if ct == level:
        return [container]

    if level == "acquisition":
        # Expanding To Children
        if ct == "project" or ct == "subject":
            containers = []
            temp_containers = container.sessions()
            for cont in temp_containers:
                containers.extend(cont.acquisitions())

        elif ct == "session":
            containers = container.acquisitions()

        # Shrink to parent
        else:
            containers = [get_acquisition(fw, container)]

    elif level == "session":
        # Expanding To Children
        if ct == "project" or "subject":
            containers = container.sessions()

        # Shrink to parent
        else:
            containers = [get_session(fw, container)]

    elif level == "subject":
        # Expanding To Children
        if ct == "project":
            containers = container.subjects()

        # Shrink to parent
        else:
            containers = [get_subject(fw, container)]

    elif level == "analysis":
        containers = container.analyses
    elif level == "file":
        containers = container.files

    return containers


def get_children(container):

    ct = container.get("container_type", "analysis")
    if ct == "project":
        children = container.subjects()
    elif ct == "subject":
        children = container.sessions()
    elif ct == "session":
        children = container.acquisitions()
    elif ct == "acquisition" or ct == "analysis":
        children = container.files
    else:
        children = []

    return children


def get_parent(fw, container):

    ct = container.get("container_type", "analysis")

    if ct == "project":
        parent = fw.get_group(container.group)
    elif ct == "subject":
        parent = fw.get_project(container.project)
    elif ct == "session":
        parent = container.subject
    elif ct == "acquisition":
        parent = container.get_session(container.session)
    elif ct == "analysis":
        parent = fw.get(container.parent["id"])
    elif ct == "file":
        parent = container.parent.reload()
    else:
        parent = None

    return parent


def get_subject(fw, container):

    ct = container.get("container_type", "analysis")

    if ct == "project":
        subject = None
    elif ct == "subject":
        subject = container
    elif ct == "session":
        subject = container.subject
    elif ct == "acquisition":
        subject = fw.get_subject(container.parents.subject)
    elif ct == "file":
        subject = get_subject(container.parent.reload())
    elif ct == "analysis":
        sub_id = container.parents.subject
        if sub_id is not None:
            subject = fw.get_subject(sub_id)
        else:
            subject = None

    return subject


def get_session(fw, container):

    ct = container.get("container_type", "analysis")

    if ct == "project":
        session = None
    elif ct == "subject":
        session = None
    elif ct == "session":
        session = container
    elif ct == "acquisition":
        session = fw.get_session(container.parents.session)
    elif ct == "file":
        session = get_session(container.parent.reload())
    elif ct == "analysis":
        ses_id = container.parents.session
        if ses_id is not None:
            session = fw.get_session(ses_id)
        else:
            session = None

    return session


def get_acquisition(fw, container):
    ct = container.get("container_type", "analysis")

    print(container.container_type)

    if ct == "project":
        acquisition = None
    elif ct == "subject":
        acquisition = None
    elif ct == "session":
        acquisition = None
    elif ct == "acquisition":
        acquisition = container
    elif ct == "file":
        acquisition = get_acquisition(container.parent.reload())
    elif ct == "analysis":
        ses_id = container.parents.acquisition
        if ses_id is not None:
            acquisition = fw.get_acquisition(ses_id)
        else:
            acquisition = None

    return acquisition


def get_analysis(fw, container):
    ct = container.get("container_type", "analysis")

    if ct == "project":
        analysis = None
    elif ct == "subject":
        analysis = None
    elif ct == "session":
        analysis = None
    elif ct == "acquisition":
        analysis = None
    elif ct == "file":
        analysis = get_analysis(container.parent.reload())
    elif ct == "analysis":
        analysis = container

    return analysis


def get_project(fw, container):
    ct = container.get("container_type", "analysis")

    if ct == "project":
        project = container
    elif ct == "subject":
        project = fw.get_project(container.parents.project)
    elif ct == "session":
        project = fw.get_project(container.parents.project)
    elif ct == "acquisition":
        project = fw.get_project(container.parents.project)
    elif ct == "file":
        project = get_project(container.parent.reload())
    elif ct == "analysis":
        project = fw.get_project(container.parents.project)

    return project


def get_parent_at_level(fw, container, level):

    if level == "project":
        parent = get_project(fw, container)
    elif level == "subject":
        parent = get_subject(fw, container)
    elif level == "session":
        parent = get_session(fw, container)
    elif level == "acquistion":
        parent = get_acquisition(fw, container)
    elif level == "analysis":
        parent = get_analysis(fw, container)

    return parent


def get_level(fw, id, level):
    if level == "project":
        container = fw.get_project(id)
    elif level == "subject":
        container = fw.get_subject(id)
    elif level == "session":
        container = fw.get_session(id)
    elif level == "acquisition":
        container = fw.get_acquisition(id)
    elif level == "analysis":
        container = fw.get_analysis(id)
    else:
        container = None

    return container


def generate_path_to_container(
    fw,
    container,
    group=None,
    project=None,
    subject=None,
    session=None,
    acquisition=None,
    analysis=None,
):
    """Generates a flywheel path to an object that can be used with `fw.lookup`.

    path format is <group>/<project>/<subject>/<session>/<acquisition>/<analysis>/<file>
    Everything following "group" is optional.  For example, if I pass in a flywheel subject, this
    would only return <group>/<project>/<subject>

    If I pass in a file attached at the session level, it would return
    <group>/<project>/<subject>/<session>/<file>

    Args:
        fw (flywheel.Client): flywheel SDK client
        container (Flywheel object): the flywheel container or file to map
        group (string): the flywheel group (if known)
        project (string): the flywheel project (if known)
        subject (string): the flywheel subject (if known)
        session (string): the flywheel session (if known)
        acquisition (string): the flywheel acquisition (if known)
        analysis (string): the flywheel analysis (if known)

    Returns:
        fw_path (string): the flywheel path of the container passed in

    """

    try:
        ct = container.container_type
    except Exception:
        ct = "analysis"

    if ct == "file":
        path_to_file = generate_path_to_container(
            fw,
            container.parent.reload(),
            group,
            project,
            subject,
            session,
            acquisition,
            analysis,
        )

        fw_path = f"{path_to_file}/{container.name}"

    else:
        fw_path = ""

        if group is not None:
            append = group
        elif group is None and container.parents.group is not None:
            append = container.parents.group
        else:
            append = ""

        fw_path += append

        if project is not None:
            append = f"/{project}"
        elif project is None and container.parents.project is not None:
            project = get_project(fw, container)
            append = f"/{project.label}"
        else:
            append = ""

        fw_path += append

        if subject is not None:
            append = f"/{subject}"
        elif subject is None and container.parents.subject is not None:
            subject = get_subject(fw, container)
            append = f"/{subject.label}"
        else:
            append = ""

        fw_path += append

        if session is not None:
            append = f"/{session}"
        elif session is None and container.parents.session is not None:
            session = get_session(fw, container)
            append = f"/{session.label}"
        else:
            append = ""

        fw_path += append

        if acquisition is not None:
            append = f"/{acquisition}"
        elif acquisition is None and container.parents.acquisition is not None:
            acquisition = get_acquisition(fw, container)
            append = f"/{acquisition.label}"
        else:
            append = ""

        fw_path += append

        if analysis is not None:
            append = f"/{analysis}"
        elif (
            analysis is None
            and container.get("container_type", "analysis") == "analysis"
        ):
            analysis = container.label
            append = f"/{analysis}"
        else:
            analysis = ""

        fw_path += append

        # append = f"/{container.label}"
        #
        # fw_path += append

    return fw_path


## Currently unused but will be needed for future development:
# 1. currently it only matches file names.  This means that it doesn't actually have "slice" info, which
# The OHIF viewer stores as SOP instance UID of the particular slice.
#
# Future plans are to get the ROI export to export the "slice Number", then have THIS gear search through individual
# Dicoms to find that slice and copy the UID.  Done this way vs matching SOP uid because sometimes customers will have a
# copy of a scan that's annotated or something and they want the ROI on that one not the orininal, and in that case
# SOP wouldn't be the  same but we could still find slice number.  Probably.


# def match_zipped_dicom_member(acq, file, sop_uid):
#
#     zip_info = acq.get_file_zip_info(file['name'])
#
#     # First pass - we will look for a simple string match in the zipped dicom:
#     match = [p['path'] for p in zip_info['members'] if sop_uid in p['path']]
#
#     if match:
#         dicom_file = match[0]
#         return dicom_file
#
#     # otherwise we have to pull each dicom, read the header, and compare SOP id's.
#     # Do this one zip member by one in the chance that you will find the correct
#     # file early on and you don't have to download everything:
#     for zip_member in zip_info["members"]:
#
#         if zip_member.get('size', 0) == 0:
#             log.debug(f"skipping directory {zip_member.get('path')}")
#             continue
#
#         try:
#             # This reads the raw dicom data stream into a pydicom object
#             #     (https://github.com/pydicom/pydicom/issues/653#issuecomment-449648844)
#             raw_dcm = DicomBytesIO(
#                 acq.read_file_zip_member(file['name'], zip_member.path))
#
#             dcm = pydicom.dcmread(raw_dcm, force=True)
#
#         except Exception as e:
#             log.info(f"Error Loading dicom member '{zip_member.get('path', 'NO PATH PRESENT')}'.  Skipping")
#             continue
#
#         if dcm.SOPInstanceUID == sop_uid:
#             match = zip_member.path
#             return match
#
#     return None
#
# def match_unzipped_dicom(file, sop_uid):
#
#     try:
#         raw_dcm = DicomBytesIO(file.read())
#         dcm = pydicom.dcmread(raw_dcm, force=True)
#     except Exception as e:
#         log.info(f"Error Loading dicom member '{zip_member.get('path', 'NO PATH PRESENT')}'.  Skipping")
#         return None
#
#     if dcm.SOPInstanceUID == sop_uid:
#         return file
#
#     return None
#
#
#
# def get_dicom_file_sop(fw_object, study_uid, series_uid, sop_uid):
#         """ locates the specific dicom file associated with a given ROI.
#
#         Given an ROI's study UID, series UID, and SOP uid, locate the exact dicom file
#         that the roi corresponds to.
#
#         Args:
#             fw_object (flywheel object): flywheel file or a parent container of a file
#             study_uid (str): the study UID on the ROI
#             series_uid (str): the series UID on the ROI
#             sop_uid (str):  the SOP uid on the ROI
#
#         Returns:
#             dicom_file (str) the name of the dicom file that the ROI is on.
#
#         """
#
#         container_type = fw_object.container_type
#         if container_type == "file":
#             log.debug('working on file')
#             acq = fw_object.parent
#             files = [fw_object]
#             object_name = fw_object.name
#
#         elif container_type == "acquisition":
#             log.debug('working on acquisition')
#             files = fw_object.reload().files
#             object_name = fw_object.label
#
#         elif container_type == "session":
#             # first extract all files from the session.
#             log.debug('working on session')
#             files = []
#             for acq in fw_object.acquisitions():
#                 acq = acq.reload()
#                 files.extend(acq.files)
#             object_name = fw_object.label
#
#         else:
#             log.warning(f"container type {container_type} is invalid for ROI importer")
#             return None
#
#         # Filter by file type, study UID and series UID:
#         files = [f for f in files if f.type == "dicom" and f.info.get("StudyInstanceUID") == study_uid and f.info.get(
#             "SeriesInstanceUID") == series_uid]
#         if len(files) == 0:
#             log.warning(f"No dicom files found in session {object_name} with matching study/series UID "
#                         f" Dicom Classifier must be run before ROI export.")
#             return None
#
#         # If we found more than one dicom matching study/series, something is probably wrong...duplicate upload?
#         if len(files) > 1:
#             log.warning(f"more than 1 file found matching:\nStudyUID: {study_uid}\nSeriesUID: {series_uid}")
#
#         file = files[0]
#         if Path(file) == ".zip":
#             acq = file.parent
#             match = match_zipped_dicom_member(acq, file, sop_uid)
#         else:
#             match = match_unzipped_dicom(file, sop_uid)
#
#
#         if match is None:
#             log.warning(
#                 f"found matching Study and Series UID but no matching SOP uid:\nSTUDY:{study_uid}\tSERIES:{series_uid}\nSOP:{sop_uid}")
#             return None
#
#         else:
#             return match
