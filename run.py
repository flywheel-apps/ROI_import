from pathlib import Path
import pathvalidate as pv
import sys

import flywheel
import flywheel_gear_toolkit as gt

from utils import load_data as ld, import_data as id, csv_utils as cu


def main(context):

    # fw = flywheel.Client()
    config = context.config
    for inp in context.config_json["inputs"].values():
        if inp["base"] == "api-key" and inp["key"]:
            api_key = inp["key"]

    fw = flywheel.Client(api_key)

    # Setup basic logging and log the configuration for this job
    if config["gear_log_level"] == "INFO":
        context.init_logging("info")
    else:
        context.init_logging("debug")
    context.log_config()
    log = context.log

    csv_file = context.get_input_path("csv_file")

    if csv_file is None or not Path(csv_file).exists():
        log.error("No file provided or file does not exist")
        return 1

    csv_file = Path(csv_file)
    name = csv_file.stem
    valid_name = pv.sanitize_filename(name)

    if len(valid_name) == 0:
        log.error(
            "You made your filename entirely out of invalid characters."
            "Just go home and think about that."
            "You are a danger to computers."
        )
        return 1

    valid_name = valid_name.replace(" ", "_")

    dry_run = config.get("dry-run", False)
    log.debug(f"dry_run is {dry_run}")

    first_row = config.get("first_row", 0)
    log.debug(f"Data starting on row{first_row}")

    delimiter = config.get("delimiter", ",")
    log.debug(f"Using Delimiter: {delimiter}")

    destination_level = context.destination.get("type")
    if destination_level is None:
        log.error(f"invalid destination {destination_level}")
        return 1

    try:

        destination_id = context.destination.get("id")
        dest_container = fw.get(destination_id)
        project = dest_container.parents.get("project")

        df = ld.load_text_dataframe(csv_file, first_row, delimiter)

        df = id.import_data(fw, df, dry_run)

        report_output = context.output_dir
        cu.save_df_to_csv(df, report_output)

    except Exception as e:
        log.exception(e)
        return 1

    return 0


if __name__ == "__main__":

    result = main(gt.GearToolkitContext())
    sys.exit(result)

    # project_id = '5daa044a69d4f3002a16ea93'
    # project = fw.get_project(project_id)
    #
    # yaml_file = "/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/UM_MetadataImport/demo_yaml.yaml"
    # excel_file = "/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/UM_MetadataImport/PreClinical_UploadExample.xlsx"
    #
    # main(project, yaml_file, excel_file)
