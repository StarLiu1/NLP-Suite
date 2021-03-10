# Written by Roberto Franzosi November 2019
# edited by Cynthia Dong
# The script includes several types of document converters:
#   pdf --> txt
#   docx --> txt
#   tsv --> csv

import sys

import GUI_IO_util
import IO_files_util
import GUI_util
import IO_libraries_util
import IO_user_interface_util

if IO_libraries_util.install_all_packages(GUI_util.window,"file_type_converter_util",['os','__main__','tkinter','docx','pdfminer','striprtf'])==False:
    sys.exit(0)

import os
import io

import csv
import tkinter as tk
import tkinter.messagebox as mb
# pip install pdfminer.six --user (since it may ask for permission) rather than pip install pdfminer
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter 
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter
from pdfminer.layout import LAParams
from docx import Document #pip install python-docx
from os.path import splitext
from striprtf.striprtf import rtf_to_text

# https://pdfminersix.readthedocs.io/en/latest/
# https://pypi.org/project/pdfminer/#description
# https://towardsdatascience.com/pdf-preprocessing-with-python-19829752af9f
# fileName contains full path
def pdf_converter(window,fileName, inputDir, outputDir,openOutputFiles):

    if len(inputDir)>0:
        msgbox_subDir = tk.messagebox.askyesnocancel("Process sub-directories", "Do you want to process for files in subdirectories?")
        if msgbox_subDir:
            inputDocs = IO_files_util.getFileList_SubDir(fileName,inputDir,'.pdf')
            # check the extension
            inputDocs = [f for f in inputDocs if f[:2] != '~$' and f[-4:]=='.pdf']
        else:
            inputDocs = [os.path.join(inputDir,f) for f in os.listdir(inputDir) if f[:2]!='~$' and f[-4:]=='.pdf']

    elif len(fileName)>0:
        if fileName[:2] != '~$' and fileName[-4:]=='.pdf':
            inputDocs=[fileName]
        else:
            tk.messagebox.showinfo("pdf converter","The input file " + fileName + " is not of type pdf.\n\nPlease, select a pdf type file (or directory) for input and try again.")
            return
    else:
        tk.messagebox.showinfo("pdf converter","No input filename or directory specified.\n\nPlease, select a pdf type file or directory for input and try again.")
        return
    if len(inputDocs) == 0:
        tk.messagebox.showinfo("Warning","There are no pdf files in the input directory.\n\nPlease, select a diffearent directory (or pdf type file) for input and try again.")
        return

    mb.showwarning(title='Warning', message='The Python pdf to text converter used here (pdfminer) is UNLIKELY to covert successfully multiple-column, full-page newspaper articles, with multiple headings and pictures. pdfminer CAN convert multiple-column documents with a simpler layout (e.g., journal articles) and does very well with full-page books/documents.\n\nFor more information on what pdfminer can do, see https://pdfminer-docs.readthedocs.io/programming.html.\n\nPLEASE, MAKE SURE TO CHECK THE CONVERTED OUTPUT FILE. IF YOU PLAN TO PARSE THE TXT OUTPUT VIA STANFORD CORENLP, YOU SHOULD CONSIDER CLEANING YOUR OUTPUT FROM COPYRIGHT MATERIAL AND BIBLIOGRAPHICAL REFERENCES, SINCE SUCH TEXTUAL ELEMENTS DO NOT HAVE COMPLETE SENTENCES.')

    numberOfDocs=len(inputDocs)
    for docNum, doc in enumerate(inputDocs):
        head, tail = os.path.split(doc)
        print('Processing file ' + str(docNum+1) + "/" + str(numberOfDocs) + " " + tail)
        with open(doc, 'rb') as fp:
            rsrcmgr = PDFResourceManager()
            retstr = io.StringIO()
            codec = 'utf-8'
            laparams = LAParams()
            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
            # Create a PDF interpreter object.
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            # Process each page contained in the document.
            if inputDir=="":
                inputDir=os.path.dirname(fileName)
            common = os.path.commonprefix([doc, inputDir])
            relativePath = os.path.relpath(doc, common)
            output_fileName=os.path.join(outputDir, relativePath[:-4] + ".txt")
            if not os.path.exists(os.path.dirname(output_fileName)):
                try:
                    os.makedirs(os.path.dirname(output_fileName))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            f = open(output_fileName, "w+", encoding = "utf-8")
            for page in PDFPage.get_pages(fp):
                interpreter.process_page(page)
                data = retstr.getvalue()
            f.write(data)

            f.close()
    IO_user_interface_util.timed_alert(window, 700, 'pdf converter ', 'Finished running pdf converter at', True, str(numberOfDocs) + ' files were successfully converted from pdf to txt format and saved in directory ' + os.path.dirname(output_fileName))
    if openOutputFiles and len(fileName)>0:
        IO_files_util.openFile(window, output_fileName)

if __name__ == '__main__':
    pdf_converter(sys.argv[1], sys.argv[2], sys.argv[3])


# https://www.geeksforgeeks.org/python-working-with-docx-module/
# docx files all have the full path embedded
# Document Converter (docx ---> txt)'
# ONLY WORKS WITH DOCX; THERE ARE NO LIBRARIES TO CONVERT DOC DOCUMENTS

def docx_converter(window,fileName,inputdirectory,outputdirectory,openOutputFiles):
    textFilename=''
    if len(inputdirectory)>0:
        msgbox_subDir = tk.messagebox.askyesnocancel("Process sub-directories",
                                                     "Do you want to process for files in subdirectories?")
        if msgbox_subDir:
            inputDocs = IO_files_util.getFileList_SubDir(fileName,inputdirectory,'.docx')

            inputDocs = [f for f in inputDocs if os.path.basename(f)[:2] != '~$' and (f[-5:] == '.docx' or f[-4:] == '.doc')]
        else:
            inputDocs = [os.path.join(inputdirectory,f) for f in os.listdir(inputdirectory) if f[:2]!='~$' and (f[-5:]=='.docx' or f[-4:]=='.doc')]
    elif len(fileName)>0:
        if fileName[:2] != '~$' and fileName[-5:]=='.docx':
            inputDocs=[fileName]
        else:
            tk.messagebox.showinfo("docx converter","The input file " + fileName + " is not of type docx.\n\nPlease, select a docx type file for input and try again.")
            return
        inputDocs=[fileName]
    else:
        tk.messagebox.showinfo("docx converter","No input filename or directory specified. The program will exit.")
        return
    if len(inputDocs) == 0:
        tk.messagebox.showinfo("Warning","There are no docx files in the input directory. The program will exit.")
        return
    numberOfDocs=len(inputDocs)

    for docNum, doc in enumerate(inputDocs):
        head, tail = os.path.split(doc)
        print('Processing file ' + str(docNum+1) + "/" + str(numberOfDocs) + " " + tail)
        fileExtension=doc.split(".")[-1]
        #fileExtension = os.path.splitext(doc)[1]
        if fileExtension =="docx":

            document = Document(doc)
            common = os.path.commonprefix([doc, inputdirectory])
            relativePath = os.path.relpath(doc, common)
            textFilename = os.path.join(outputdirectory, os.path.splitext(relativePath)[0] + ".txt")
            # TODO: if the subdirectory doesn't exist in output directory, create it
            if not os.path.exists(os.path.dirname(textFilename)):
                try:
                    os.makedirs(os.path.dirname(textFilename))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            with open(textFilename,"w", encoding="utf-8",errors='ignore') as textFile:
                for para in document.paragraphs:
                    textFile.write(para.text+'\n') #line of texts
    if openOutputFiles and len(fileName)>0:
        IO_files_util.openFile(window, textFilename)

def csv_converter(window,fileName,inputDir,outputDir,openOutputFiles):
    if fileName!='':
        if fileName[:2] != '~$' and fileName[-4:]=='.csv':
            inputDocs=[fileName]
        else:
            tk.messagebox.showinfo("csv converter","The input file " + fileName + " is not of type csv.\n\nPlease, select a csv type file for input and try again.")
            return
        inputDocs=[fileName]
    else:
        if inputDir!='':
            tk.messagebox.showinfo("csv converter","No input filename. The csv converter works only on a single csv file, rather than a whole directory. Please, select an input csv file and try again.")
            return
        else:
            tk.messagebox.showinfo("csv converter","No input filename. Please, select an input csv file and try again.")
            return
        tk.messagebox.showinfo("csv converter","The function is still under construction.\n\nSorry!")
        return
        # TODO add a REMINDER that if they need to use some of the csv fields as filters,
        #   they need to use first the Data manager to extract specific fields by specific values
        #   for instance, in the csv output of the gender annotator, you may want to extract all the sentences
        #       WHERE the gender is Male and/or Female for separate analysis
        # TODO Check headers if Sentence is present and export sentences
        # TODO If Document ID present, loop through all documents
        #   ask the user if they want to export the Document (i.e., filename) adding it before each document sentence
        #   If the values of Document ID > 1  further ask if they want to create separate files or a single merged file
        #   Could further ask if they want to embed the filename in special symbols (e.g., <@ @>, as in <@filename@>
        #       so that the files can also be easily split

def rtf_converter(window,fileName,inputdirectory,outputdirectory,openOutputFiles):
    textFilename=''
    if len(inputdirectory)>0:
        msgbox_subDir = tk.messagebox.askyesnocancel("Process sub-directories",
                                                     "Do you want to process for files in subdirectories?")
        if msgbox_subDir:
            inputRTFs = IO_files_util.getFileList_SubDir(fileName,inputdirectory,'.rtf')

            inputRTFs = [f for f in inputRTFs if os.path.basename(f)[:2] != '~$' and  f[-4:] == '.rtf']
        else:
            inputRTFs = [os.path.join(inputdirectory,f) for f in os.listdir(inputdirectory) if f[:2]!='~$' and  f[-4:]=='.rtf']
    elif len(fileName)>0:
        if fileName[:2] != '~$' and fileName[-4:]=='.rtf':
            inputRTFs=[fileName]
        else:
            tk.messagebox.showinfo("rtf converter","The input file " + fileName + " is not of type rtf.\n\nPlease, select a rtf type file for input and try again.")
            return
        inputRTFs=[fileName]
    else:
        tk.messagebox.showinfo("rtf converter","No input filename or directory specified. The program will exit.")
        return
    if len(inputRTFs) == 0:
        tk.messagebox.showinfo("Warning","There are no rtf files in the input directory. The program will exit.")
        return
    numberOfDocs=len(inputRTFs)

    for docNum, doc in enumerate(inputRTFs):
        head, tail = os.path.split(doc)
        print('Processing file ' + str(docNum+1) + "/" + str(numberOfDocs) + " " + tail)
        fileExtension=doc.split(".")[-1]
        #fileExtension = os.path.splitext(doc)[1]
        if fileExtension =="rtf":
            lines = []#list of each line in the txt files
            fullText = open(doc, 'r', encoding='utf-8',errors='ignore').read()
            # https://stackoverflow.com/questions/60897366/how-to-read-rtf-file-and-convert-into-python3-strings-and-can-be-stored-in-pyth
            # https://stackoverflow.com/questions/44580580/how-to-convert-rtf-string-to-plain-text-in-python-using-any-library
            # https://stackoverflow.com/questions/188545/regular-expression-for-extracting-text-from-an-rtf-string/188877#188877
            text = rtf_to_text(fullText)
            # text=fullText
            common = os.path.commonprefix([doc, inputdirectory])
            relativePath = os.path.relpath(doc, common)
            textFilename = os.path.join(outputdirectory, os.path.splitext(relativePath)[0] + ".txt")
            # TODO: if the subdirectory doesn't exist in output directory, create it
            if not os.path.exists(os.path.dirname(textFilename)):
                try:
                    os.makedirs(os.path.dirname(textFilename))
                except OSError as exc:
                    if exc.errno != errno.EEXIST:
                        raise
            with open(textFilename,"w", encoding="utf-8",errors='ignore') as textFile:
                textFile.write(text)
    if openOutputFiles and len(fileName)>0:
        IO_files_util.openFile(window, textFilename)
    
# the tsv file (fileName) has the full path embedded
# File Converter (tsv --> csv)
def tsv_converter(window,fileName,outputdirectory):
    # read a tab-separated file
    with open(fileName,'r',encoding="utf-8",errors='ignore') as fin:
        cr = csv.reader(fin, delimiter='\t')
        filecontents = [line for line in cr]

    # write comma-separated file (comma is the default delimiter)
    fileName,extension = splitext(fileName)
    with open(fileName+'.csv','w',newline='') as fou:
        cw = csv.writer(fou, dialect = 'excel')
        for item in filecontents:
            cw.writerow(item)
    return fileName+'.csv'