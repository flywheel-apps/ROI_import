
import logging

from utils import flywheel_helpers as fh
from utils.ROI_Template import ROI
import utils.fwobject_utils as fu

log = logging.getLogger("__main__")


def get_handle_from_row(series):
    start_dict = {
        'x': panda_pop(series, 'X_min'),
        'y': panda_pop(series, 'Y_min'),
        'active': panda_pop(series, 'active'),
        'highlight': panda_pop(series, 'highlight')
    }
    print(start_dict)
    end_dict = {
        'x': panda_pop(series, 'X_max'),
        'y': panda_pop(series, 'Y_max'),
        'active': panda_pop(series, 'active'),
        'highlight': panda_pop(series, 'highlight')
    }

    bounding_dict = {
        "height": panda_pop(series, 'height'),
        "left": panda_pop(series, 'left'),
        "top": panda_pop(series, 'top'),
        "width": panda_pop(series, 'width')
    }

    textbox_dict = {
        "allowedOutsideImage": panda_pop(series, 'allowedOutsideImage'),
        "drawnIndependently": panda_pop(series, 'drawnIndependently'),
        "hasBoundingBox": panda_pop(series, 'hasBoundingBox'),
        "hasMoved": panda_pop(series, 'hasMoved'),
        "movesIndependently": panda_pop(series, 'movesIndependently'),
        "boundingBox": bounding_dict
    }

    handle_dict = {'start': start_dict,
                   'end': end_dict,
                   'initialRotation': panda_pop(series, 'initialRotation'),
                   'textBox': textbox_dict
                   }

    if 'Handle' in series:
        log.warning('Column name <Handle> is reserved.  Data will not be uploaded.')
        series.pop('Handle')

    return handle_dict



def panda_pop(series, key):
    if key in series:
        return series.pop(key)
    else:
        return None


def get_roi_from_row(series, file):
    handle = get_handle_from_row(series)
    id_dict = fu.get_uids_from_filename(file)

    for k in id_dict.keys():
        panda_pop(series, k)

    roi_dict = {'Handle': handle}
    roi_dict.update(id_dict)
    roi_dict.update(series)
    
    roi = ROI()
    roi.roi_from_dict(**roi_dict)
    return (roi)



def save_df_to_csv(df, output_dir):
    output_path = output_dir/'Data_Import_Status_report.csv'
    df.to_csv(output_path, index=False)