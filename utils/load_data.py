import pandas as pd
import logging

log = logging.getLogger(__name__)


def load_excel_dataframe(excel_path, firstrow_spec, sheets_spec=0):
    # This function is not used in this version of the gear, but will be used in the future.
    # First iteration only supports single sheet import, but sheet can be specified.
    df = pd.read_excel(excel_path, header=firstrow_spec - 1, sheet_name=sheets_spec)
    df.columns = df.columns.str.lower()
    df = df.where(pd.notnull(df), None)
    return df


def load_text_dataframe(df_path, firstrow_spec, delimiter_spec):
    """Loads a plain text (non-excel style) delimited file into a numpy dataframe

    Args:
        df_path (Pathlike): The path of the file that will be made into a dataframe
        firstrow_spec (integer): The row in the CSV file that contains the headers of
            the columns.  Data is assumed to be below this row.
        delimiter_spec (string): The type of delimiter used in this file.

    Returns:
        df (pandas.DataFrame): The delimited text file, imported to dataframe format.

    """
    df = pd.read_table(df_path, delimiter=delimiter_spec, header=firstrow_spec - 1)
    # df.columns = df.columns.str.lower()
    df = df.where(pd.notnull(df), None)

    return df


def validate_df(df, object_col):

    if object_col == "" or object_col is None:
        log.info("No object column specified, assuming column 1")
        object_col = df.keys()[0]
        log.info(f"Using column {object_col}")

    if object_col not in df:
        log.error(f"Specified column {object_col} not found in CSV file")
        raise Exception("Column not in CSV")

    series = df[object_col]
    if len(series) != series.nunique():
        log.error(
            f"Non-unique object names in mapping column.  Filenames must be unique."
        )
        raise Exception("Object Mappings Must Be Unique")

    return object_col


# def load_yaml(yaml_path):
#     with open(yaml_path) as file:
#         import_dict = yaml.load(file, Loader=yaml.FullLoader)
#
#     for key in import_dict:
#         import_dict[key] = mc.mapping_object(import_dict[key])
#
#     return import_dict


# df_path = '/Users/davidparker/Downloads/Data_Entry_2017_test.csv'
# delimiter_spec = ','
# firstrow_spec = 1
# df = pd.read_table(df_path, delimiter=delimiter_spec, header=firstrow_spec-1)
# output = '/Users/davidparker/Desktop/test_json_export.json'
# df.to_json(output, orient="index")
