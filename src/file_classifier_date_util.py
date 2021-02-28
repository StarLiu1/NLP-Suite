# written by Zhangyi Pan May 2020
# edited by Yi Wang and Roberto Franzosi August 2020
import sys
import GUI_util
import IO_libraries_util

if IO_libraries_util.install_all_packages(GUI_util.window,"file_classifier_date_util.py",['os','tkinter','shutil'])==False:
    sys.exit(0)

import os
from datetime import datetime, timedelta
import pandas as pd
import tkinter as tk
import tkinter.messagebox as mb
import shutil

import IO_files_util
import IO_csv_util
import IO_user_interface_util

def create_timedelta(date_distance_value, date_type):
    if date_type == 'day':
        return timedelta(days=date_distance_value)
    elif date_type == 'month':
        return timedelta(days=date_distance_value*30)
    else:
        return timedelta(days=date_distance_value*365)

# input_first_dir is the source dir containing a list of files
# input_sec_dir is the target directory containing a set of subdirs
def classifier(input_first_dir, input_sec_dir,output_dir_path,openOutputFiles, date_format,date_separator,date_position,date_distance_value, date_type):
    IO_user_interface_util.timed_alert(GUI_util.window, 2000, 'Analysis start',
                                       'Started running the File Classifier by embedded date at', True,
                                       'You can follow the Classifier in command line.')
    result = mb.askyesno("Output option","Would you like to copy the SOURCE files to the TARGET subdirectories?",default='no')
    folders = []
    filesToOpen = []
    nDocs=0
    nCopies=0
    nDateErrors=0
    duration = create_timedelta(int(date_distance_value), date_type)
    # split duration that returns such values as 5 days, 0:00:00
    splitDuration=str(duration).split(",", 1)[0]
    
    # find all dirs in 2
    for i in os.scandir(input_sec_dir):
        if i.is_dir():
            folders.append(i.path)
    data = []
    # get
    for ungrouped in os.listdir(input_first_dir):
        nDocs=nDocs+1
        nTargetDocs=0
        print("\nProcessing folder: ",os.path.basename(os.path.normpath(ungrouped)))
        print("\n   Processing file: " + str(ungrouped))
        # IO_util.timed_alert(GUI_util.window, 5000, 'file classifier', 'Processing file: ' + str(ungrouped))

        fname, file_ext = os.path.splitext(ungrouped)
        date, date_str = IO_files_util.getDateFromFileName(fname, date_separator, date_position, date_format)
        if date_str == '':
            nDateErrors=nDateErrors+1
            data.append([IO_csv_util.dressFilenameForCSVHyperlink(input_first_dir + os.sep + ungrouped), '','Error in Date Format! Source File not copied',splitDuration])
            continue
        for folder in folders:
            print('   Processing subfolder: ' + str(folder))
            early = datetime.max.date()
            for file in os.listdir(folder):
                filename, file_extension = os.path.splitext(file)
                if file_extension != '':
                    nTargetDocs=nTargetDocs+1
                    dt,dt_str = IO_files_util.getDateFromFileName(filename, date_separator, date_position, date_format)
                    if dt_str!='':
                        if dt < early:
                            early = dt
                        if abs(early - date) < duration:
                            if result == True:
                                nCopies=nCopies+1
                                shutil.copy(input_first_dir+os.sep+ungrouped, folder+os.sep+ungrouped)
                                data.append([IO_csv_util.dressFilenameForCSVHyperlink(input_first_dir + os.sep + ungrouped), IO_csv_util.dressFilenameForCSVHyperlink(folder), 'Successfully Copied!', splitDuration])
                            else:
                                data.append([IO_csv_util.dressFilenameForCSVHyperlink(input_first_dir + os.sep + ungrouped), IO_csv_util.dressFilenameForCSVHyperlink(folder), 'Processed but did not copy!', splitDuration])
    output_filename = IO_files_util.generate_output_file_name('', input_first_dir, output_dir_path, '.csv')
    filesToOpen.append(output_filename)
    df = pd.DataFrame(data, columns= ['Source_file_path', 'Target_directory','File_status','Date_range'])
    df.to_csv(output_filename,index=False)

    print("\n\nNumber of SOURCE input documents processed:",nDocs)
    print("Number of TARGET input documents processed:",nTargetDocs)
    print("Number of TARGET input sub-directories:",len(folders))
    print("Number of SOURCE documents COPIED to TARGET sub-directories:",nCopies)
    print("Number of finenames with wrong embedded date:",nDateErrors,'\n\n')
    
    mb.showwarning("Warning", "Results of the classifier script:\n\n"
            + "\nNumber of SOURCE input documents processed: " + str(nDocs)
            + "\nNumber of TARGET input documents processed: " + str(nTargetDocs)
            + "\nNumber of TARGET input sub-directories: "  + str(len(folders))
            + "\nNumber of SOURCE documents COPIED: " + str(nCopies)
            + "\nNumber of finenames with wrong embedded date: "  + str(nDateErrors))

    if openOutputFiles==True:
        IO_files_util.OpenOutputFiles(GUI_util.window, openOutputFiles, filesToOpen)
        filesToOpen=[] # to avoid opening twice here and in calling fuunction

    return filesToOpen