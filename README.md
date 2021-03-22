# ROI import

## Description

This gear imports OHIF viewer ROI's from a csv into flywheel.

### Instructions:

Files must be in DICOM format.  The flywheel DICOM classifier MUST be run before hand
so that the DICOM headers are copied to the file's flywheel metadata.  File names must
be unique within sessions.  The CSV containing ROI's for import must follow strict
formatting requirements laid out below.


### Limitations:

**1.**   In this version of the gear, files must be uniquely named within sessions, even if
 they are in different acquisitions.  If there are duplicate file names within a
 session, EVEN if they are in different acquisitions, this gear will be unable to upload
 an ROI to any of the files sharing the same name.  
 
**2.**   This gear can only place ROI's on 2D dicom images.

**3.**   This gear can only place rectangular or elliptical ROI's

The CSV columns specify a flywheel object identifier, and ROI information to import.
Column headers must follow the naming schema below for successful import:

## Column Naming Schema:

**NOTE:** These headers ARE CASE SENSITIVE.

They are also sensitive in general, please be careful not to hurt their feelings.


### Flywheel Location Columns:

The columns **Group**, **Project**, **Subject**, and **Session* all indicate where in 
Flywheel the file is that the ROI is being attached to.  

*REQUIRED*:

 - **Group**:  The flywheel *group ID*, which is different from the group NAME.  the 
 group ID is usually a short string of all lowercase letters, and can be found in the 
 flywheel path displayed at the top of the page when viewing a flywheel project. 
 This is highlighted in yellow in the picture below.  This is different from the *Group 
 Name*, which is longer, and can have spaces and capital letters.  In the example
 below, the Group Name is "Scientific Solutions", and the Group ID is "scien".  In this
 case, "scien" would be the correct string to use in the **Group** Column.
 
 - **Project**: The flywheel *Project Label* that the file is in.  This can be found in 
 the flywheel path displayed at the top of the pate when viewing a flywheel project.
 This is highlighted in red in the picture below. 
 
 - **Subject**: The flywheel *Subject Label* of the subject that contains the file.
 
 - **Session**: The flywheel *Session Label* of the session that contains the file.
 
 - **File**: The full name of the file in flywheel to add the ROI to.
 
 *OPTIONAL*:
 - **User Origin**:  The flywheel user ID (email address) of the person who
  created this ROI


![Flywheel Path](https://github.com/flywheel-apps/ROI_import/blob/main/content/fw_project_path.png)


### ROI Columns:

*REQUIRED*:

- **X min**: The minimum X coordinate of the ROI

- **Y min**: The minimum Y coordinate of the ROI

- **X max**: The maximum X coordinate of the ROI

- **Y max**: The maximum Y coordinate of the ROI

- **ROI type**: The type of ROI (Valid types are "EllipticalRoi" and "RectangleRoi")

*OPTIONAL*:

- **location**: the Label (Anatomical Location) of the ROI.   This will be visible in
the OHIF viewer.

- **description**: a short description of the ROI (visible in the OHIF viewer)

- **visible**: True or False, will determine if the ROI renders when loading the image.

Any other columns will be added as metadata in the ROI object.

*FORBIDDEN*:
The following column headers are forbidden and will not be included:

- **Handle**
- **imagePath**
- **_id**

## Inputs & Settings

### Inputs:

 - **csv_file**: The input CSV file to be ingested for ROI Import
  

  
### Config Settings:

#### CSV file properties:

 - **first_row**: The first row that contains data.  By default, the gear assumes row 1.
  The first fow of data MUST be column headers.  Row 1 is always the absolute first row 
  of the file.
 
 - **delimiter**: Flywheel can support tab, space, and comma separated files.  Default 
 is comma.

#### Gear Execution Properties:

 - **gear_log_level**: The level at which the gear will log.  "Info" for normal amounts
 of information, and "Debug" for more detailed logs.

 - **dry_run**: Only log what changes would be made, do not update anything.
 
 - **overwrite**: If checked, the gear will overwrite existing metadata with what's in 
 the CSV.
 
 
## Logging

This gear will log information the help you follow the progress of the metadata ingest.

The log is roughly broken into 3 parts:  First, the configuration settings are logged:

```
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.logging] Log level is INFO
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Destination is analysis=6050f2adf202571f32b8ebb8
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Input file "csv_file" is BoundingBox_ROIs.csv from project=601ae8f9725e16822872021c
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Config "delimiter=,"
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Config "dry_run=False"
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Config "first_row=1"
[ 20210316 18:02:23     INFO flywheel_gear_toolkit.context.context] Config "gear_log_level=INFO"
[ 20210316 18:02:23     INFO __main__] Starting Mapping
```


Following this, each row will generate a report.  For example, given the row:

| Group | Project | Subject | Session | File | X min | X max | Y min | Y max | ROI type |
| ------ | ------ | ------- | ------- | ---- | ----- | ----- | ----- | ----- | -------- |
| samplegroup | sampleproject | samplesubject | samplesession | samplefile | 217.813 | 262.522 | 179.714 | 216.0958 | RectangleRoi |


The output may look like this:

```[ 20210316 18:02:23     INFO __main__] Checking for location samplegroup/sampleproject/samplesubject/samplesession
[ 20210316 18:02:24     INFO __main__] 
==================================================
Setting Metadata For samplefile
--------------------------------------------------
[ 20210316 18:02:24     INFO __main__] Group                           samplegroup
Project                    sampleproject
Subject                    samplesubject
Session                    samplesession
File                          samplefile
X_min                            217.813
X_max                            262.522
Y_min                            179.714
Y_max                           216.0958
ROI_type                    RectangleRoi
Name: 0, dtype: object
{'x': 217.813, 'y': 179.714, 'active': True, 'highlight': False}
[ 20210316 18:02:24     INFO __main__] Found 1.2.826.0.1.3680043.8.498.63173678856387194301553421793092744592 for SeriesInstanceUID
[ 20210316 18:02:24     INFO __main__] Found 1.2.826.0.1.3680043.8.498.59224471754758172653982690197001560242 for SOPInstanceUID
[ 20210316 18:02:24     INFO __main__] Found 1.2.826.0.1.3680043.8.498.94434652629753555598421293048190029954 for StudyInstanceUID
[ 20210316 18:02:24     INFO ROI] Initializing ROI
(179.714, 216.0958)
[ 20210316 18:02:24     INFO __main__] Creating ROI
--------------------------------------------------
STATUS: Success
==================================================
```

This may also contain be some debug information on the ROI that was created, such as
the metadata object printed as a json.

Finally, at the end of the log, a status report will be printed indicating how many rows
were successfully uploaded:

```
===============================================================================
Final Report: 10/11 objects updated successfully
90.9090909090909%
See output report file for more details
===============================================================================
```

## Output

The gear generates an output CSV file called "Data_Import_Status_report.csv".

This file is a copy of the original CSV, with two additional columns:

- 'Gear_Status': The status of the upload for the specified row.  "Success" or "Fail"
- 'Gear_FW_Location': The full fw path to the object modified, specified as: 

`<group>/<project>/<subject>/<session>/<acquisition>/<file>`




