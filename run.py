from pathlib import Path
import pathvalidate as pv
import sys
import logging

import flywheel
import flywheel_gear_toolkit as gt

from utils import load_data as ld, import_data as id, csv_utils as cu

log = logging.getLogger()


def main(csv_file, first_row, delimiter, api_key, dry_run, output_dir, destination):
    """Imports ROI's from a CSV file into Flywheel

    This function initializes a flywheel Client, loads a CSV file, ingests that data
    into a format that can be used to generate ROI's, uploads those to flywheel, and
    saves a report.
    Args:
        csv_file (Pathlike): The location of the CSV file for ROI import
        first_row (integer): The row in the CSV file that contains the headers of the
            columns.  Data is assumed to be below this row.
        delimiter (string): The type of delimiter used in this file.
        api_key (string): The flywheel API key of the user running this gear.
        dry_run (boolean): Sets if the gear is going to perform a dry-run (will not
            rite data)
        output_dir (Pathlike): The directory to save gear outputs to
        group (Flywheel.Group): The group that the gear is being run in.
        project (Flyhweel.Project): The project that the gear is being run in.

    Returns:
        exit_status (integer): indicates if the script was successful (0) or encountered
        an error (1)
    """

    exit_status = 0

    try:
        # Initialize the flywheel client using an API-ket
        fw = flywheel.Client(api_key)

        destination = fw.get(destination['id'])
        group = fw.get_group(destination.parents.group)
        project = fw.get_project(destination.parents.project)
        log.debug(f'working in project {project.label}')

        # We now assume that this data is being uploaded to the group/project that the gear is being run on.

        # import the csv file as a dataframe
        df = ld.load_text_dataframe(csv_file, first_row, delimiter)

        # Format the data for ROI's from the data headers and upload to flywheel
        df = id.import_data(fw, df, group, project, dry_run)

        # Save a report
        cu.save_df_to_csv(df, output_dir)

    except Exception as e:
        log.exception(e)
        exit_status = 1

    return exit_status


def process_gear_inputs(context):
    """Process the flywheel inputs/config options for running the main script

    Takes the flywheel gear toolkit context object and extracts the inputs and config
    options provided to the gear.
    Args:
        context (flywheel_gear_toolkit.GearToolkitContext): The flywheel gear context

    Returns:
        csv_file (Pathlike): The location of the CSV file for ROI import
        first_row (integer): The row in the CSV file that contains the headers of the
            columns.  Data is assumed to be below this row.
        delimiter (string): The type of delimiter used in this file.
        api_key (string): The flywheel API key of the user running this gear.
        dry_run (boolean): Sets if the gear is going to perform a dry-run (will not
            rite data)
        output_dir (Pathlike): The directory to save gear outputs to
        log (logging.Logger): A logger to be used in the rest of the gear.

    """

    # First extract the configuration options
    config = context.config

    # Examine the inputs for the "api-key" token and extract it
    for inp in context.config_json["inputs"].values():
        if inp["base"] == "api-key" and inp["key"]:
            api_key = inp["key"]

    # Setup basic logging and log the configuration for this job
    if config["gear_log_level"] == "INFO":
        context.init_logging("info")
    else:
        context.init_logging("debug")
    context.log_config()

    # Get the path of the CSV file provided by the user
    csv_file = context.get_input_path("csv_file")

    # The gear shouldn't run if this isn't provided but we check anyway.
    if csv_file is None or not Path(csv_file).exists():
        log.error("No file provided or file does not exist")
        raise Exception("No valid CSV file")

    # Pathify `csv_file` as it is currently a string, and extract data parts.
    csv_file = Path(csv_file)
    name = csv_file.stem
    valid_name = pv.sanitize_filename(name)

    if len(valid_name) == 0:
        log.error(
            "You made your filename entirely out of invalid characters."
            "Just go home and think about that."
            "You are a danger to computers."
        )
        raise Exception("Invalid CSV file name")

    # Extract the various config options from the gear's config.json file.
    # These options are created in the manifest and set by the user upon runtime.
    dry_run = config.get("dry-run", False)
    log.debug(f"dry_run is {dry_run}")

    first_row = config.get("first_row", 1)
    log.debug(f"Data starting on row{first_row}")

    delimiter = config.get("delimiter", ",")
    log.debug(f"Using Delimiter: {delimiter}")

    # Check to make sure we have a valid destination container for this gear.
    destination_level = context.destination.get("type")
    if destination_level is None:
        log.error(f"invalid destination {destination_level}")
        raise Exception("Invalid gear destination")

    # Get the destination group/project
    destination = context.destination
    output_dir = context.output_dir


    # TODO: Possibly not needed
    # destination_id = context.destination.get("id")
    # dest_container = fw.get(destination_id)
    # project = dest_container.parents.get("project")

    return csv_file, first_row, delimiter, api_key, dry_run, output_dir, destination


if __name__ == "__main__":

    (
        csv_file,
        first_row,
        delimiter,
        api_key,
        dry_run,
        output_dir,
        destination
    ) = process_gear_inputs(gt.GearToolkitContext())

    result = main(csv_file, first_row, delimiter, api_key, dry_run, output_dir, destination)
    sys.exit(result)