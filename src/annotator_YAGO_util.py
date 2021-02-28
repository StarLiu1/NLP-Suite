import sys
import GUI_util
import IO_libraries_util

if IO_libraries_util.install_all_packages(GUI_util.window,"annotator_YAGO_util.py",['os','re','tkinter','subprocess','time','pandas','string','SPARQLWrapper','stanza','fuzzywuzzy'])==False:
    sys.exit(0)

import os
import string
allpunks = string.punctuation + '1' + '2' + '3' + '4' + '5' + '6' + '7' + '8' + '9' + '0'
from SPARQLWrapper import SPARQLWrapper, JSON, XML
sparql = SPARQLWrapper("https://yago-knowledge.org/sparql/query")
import pandas as pd
import re
from re import split
import stanza
stanza.download('en')
stannlp = stanza.Pipeline(lang='en', processors='tokenize,ner,mwt,pos,lemma')
from fuzzywuzzy import fuzz
import time

import IO_files_util
import GUI_util
import IO_user_interface_util
import IO_csv_util

##
time1=[]
##
word_bag=[]
##global dataframe
dict={}
sentID=[]
phrase=[]
link=[]
ont=[]


# This is the main function
def YAGO_annotate(inputFile, inputDir, outputDir, annotationTypes,color1,colorls):
    filesToOpen = []
    numberOfAnnotations = len(annotationTypes)
    if numberOfAnnotations==0:#when want everything annotated, should not select any classes.
        categories=['schema:Thing','owl:Class']
        if colorls == []:
            colorls = ['red', 'blue']
    else:
        categories=[]
        for anntype in annotationTypes:
            if anntype=="Emotion":
                  categories.append("yago:Emotion")
            elif anntype in ["BioChemEntity","Gene","Taxon","MolecularEntity"]:
                  categories.append("bioschemas:"+anntype)
            else:
                  categories.append("schema:"+anntype)


    # loop through every txt file and annotate via request to YAGO
    files = IO_files_util.getFileList(inputFile, inputDir, '.txt')
    nFile = len(files)
    if nFile == 0:
        return
    IO_files_util.timed_alert(GUI_util.window, 2000, 'Analysis start', 'Started running YAGO annotator at', True,
                        '\nAnnotating types: ' + str(categories) + " with associated colors: " + str(colorls))
    i=0
    for file in files:
            splittedHtmlFileList = []
            i = i + 1
            print("Processing file " + str(i) + "/" + str(nFile) + " " + file)
            listOfFiles=[file]
            subFile = 0
            for doc in listOfFiles:
                subFile = subFile + 1
                subFilename = os.path.join(outputDir,"NLP_YAGO_annotated_" + str(os.path.split(doc)[1]).split('.txt')[0]+str(subFile) + "_" + str(len(listOfFiles))+ '.html')
                splittedHtmlFileList.append(subFilename)
                print("   Processing split-file " + str(subFile) + "/" + str(len(listOfFiles)) + " " + doc)
                contents = open(doc, 'r', encoding='utf-8', errors='ignore').read()
                contents =' '.join(contents.split()) #reformat content
                contents = contents.replace('\0', '')  # remove null bytes
                contents = contents.replace('\'', '')  # remove quotation marks
                contents = contents.replace('\"', '')
                contents = contents.replace("\\", '')
                contents = contents.replace("/", ' or ')

                IO_user_interface_util.timed_alert(GUI_util.window, 7000, 'YAGO pre-processing and running-time estimation',
                                                   'The YAGO annotator is pre-processing your file and estimating the time required to annotate your file.\n\nThis may take several minutes. Please, be patient.',
                                                   False,'',True)

                if numberOfAnnotations==0: # default annotation, when no annotation was selected by user
                    html_content=annotate_default(contents,categories,color1,"blue") # TODO should be colorls
                else:
                    html_content=annotate_multiple(contents,categories,color1,colorls)
                time_diff=time.time()-time1[len(time1)-1]
                print("Annotation for the current document took: " + str(time_diff//60) + " mins and " + str(time_diff%60) + " secs")
                with open(subFilename, 'w+', encoding='utf-8', errors='ignore') as f:
                    f.write(html_content)
                f.close()

            if subFile > 0:
                # outFilename here is the combined html file from the splitted files
                outFilename = os.path.join(outputDir,"NLP_YAGO_annotated_" + str(os.path.split(file)[1]).split('.txt')[0]+ '.html')
                with open(outFilename, 'w+', encoding="utf-8", errors='ignore') as outfile:
                    for htmlDoc in splittedHtmlFileList:
                        with open(htmlDoc, 'r', encoding="utf-8", errors='ignore') as infile:
                            for line in infile:
                                outfile.write(line)
                        infile.close()
                        os.remove(htmlDoc)  # delete temporary split html file from output directory
                outfile.close()
            filesToOpen.append(outFilename)
            # print(outFilename)
            # TODO Sentence ID must start from1 rather than CS 0
            df = pd.DataFrame(list(zip(sentID,phrase,link,ont)),columns=['Sentence ID', 'Token','html','Ontology class'])
            # TODO in the output csv file the html url one should be able to click on it and open the website
            #   in IO_csv_util there is a function def dressFilenameForCSVHyperlink(fileName) that does that for a regular file
            csvname = outFilename.replace(".html","_")+str(annotationTypes).replace("[", "").replace("]", "").replace("'", "").replace(",", "_")
            df.to_csv((csvname+".csv"),index=False)
            filesToOpen.append(csvname+".csv")
    IO_files_util.timed_alert(GUI_util.window, 3000, 'Analysis end', 'Finished running YAGO annotator at', True)
    return filesToOpen

def estimate_time(parsed_doc,num_cats,word_bag):
    print("Computing the estimated time for query...")
    a=[word.lemma for sent in parsed_doc.sentences for word in sent.words]
    num1=len(word_bag)#saves the original size of word bag
    word_bag=list(set(a+word_bag))
    num2=len(word_bag)-num1#maximum possible number of additional words to be queried
    est=num2/5+num2*(num_cats-1)/2+len(a)/15
    time1.append(time.time())

    IO_user_interface_util.timed_alert(GUI_util.window, 7000, 'YAGO annotator',
        'Estimated time of YAGO query for the current document is: ' + str(est//60)+' mins and '+str(round(est%60,2))+' secs.\n\n'\
        '   Number of tokens in document: ' +str(len(a)) +'\n'\
        '   Number of tokens to be queried: ' +str(num2) +'\n'\
        '   Number of ontology classes: ' + str(num_cats) +'\n',
        False,'',True)

    return

# the function processes YAGO in default mode when no combination of ontology class and color have been selected by the user
def annotate_default(contents,cats,color1,color2):
    html_str='<html>\n<body>\n<div>\n'
    tA1 = ['<span style=\"color: ' + color1 + '\">', '</span> ']
    tA2 = ['<a style=\"color:' + color2 + '\" href=\"', '\">', '</a> ']
    doc = stannlp(contents)
    estimate_time(doc, len(cats),word_bag)
    for sent_id in range(len(doc.sentences)):
        sent=doc.sentences[sent_id]
        #sent_ner=nerdoc.sentences[sent_id]
        prev_og = ""
        prev_tr = ""
        pos=True
        for i in range(len(sent.words)):
            word=sent.words[i]
            pos=True
            if((word.pos=="VERB")or (word.pos=="DET")or(word.pos=="ADP")or (word.pos=="PRON") or (word.pos=="AUX")):
                pos=False

            #word_ner=sent_ner.tokens[i]
            #if((word.id==1 and word_ner.ner!="o")|(word.id!=1 and (word.text[0]).isupper())):
            if(word.xpos=="NNP"or word.xpos=="NNPS"):
                prev_tr=prev_tr+word.lemma+" "
                prev_og=prev_og+word.text+" "
            elif(word.id==1):##update html string with current token
                html_str=update_html(html_str,str(word.text),str(word.lemma),cats,tA1,tA2,pos,sent_id,color1,color2)
            else:##update html string with prev[:-1] and then curr token
                html_str = update_html(html_str, prev_og[:-1], prev_tr[:-1],cats, tA1, tA2,pos,sent_id,color1,color2)
                html_str= update_html(html_str,str(word.text),str(word.lemma),cats,tA1,tA2,pos,sent_id,color1,color2)
                prev_og=""
                prev_tr=""
        if(((sent.words[len(sent.words)-1]).text[0]).isupper()):##check if last token of a sent is uppercase
            html_str=update_html(html_str, prev_og[:-1], prev_tr[:-1],cats, tA1, tA2,pos,sent_id,color1,color2) ##update prev[:-1]
    html_str=html_str+'\n</div>\n</body>\n</html>'
    return html_str

# the function processes YAGO when the user has selected multiple combinations of ontology class and color
def annotate_multiple(contents,cats,color1,colorls):
    html_str = '<html>\n<body>\n<div>\n'
    tA1 = ['<span style=\"color: ' + color1 + '\">', '</span> ']
    doc = stannlp(contents)
    estimate_time(doc, len(cats),word_bag)
    for sent_id in range(len(doc.sentences)):
        sent = doc.sentences[sent_id]
        prev_og = ""
        prev_tr = ""
        pos=True
        for i in range(len(sent.words)):
            word = sent.words[i]
            pos = True
            if ((word.pos == "VERB") or (word.pos == "DET") or (word.pos == "ADP") or (word.pos == "PRON") or (word.pos == "AUX")):
                pos = False
            if (word.xpos == "NNP" or word.xpos == "NNPS"):
                prev_tr = prev_tr + word.lemma + " "
                prev_og = prev_og + word.text + " "
            elif (word.id == 1):  ##update html string with current token
                html_str = update_html_colorful(html_str, str(word.text), str(word.lemma), cats, tA1, colorls, pos, sent_id,color1)
            else:  ##update html string with prev[:-1] and then curr token
                html_str = update_html_colorful(html_str, prev_og[:-1], prev_tr[:-1], cats, tA1, colorls, pos, sent_id,color1)
                html_str = update_html_colorful(html_str, str(word.text), str(word.lemma), cats, tA1, colorls, pos, sent_id,color1)
                prev_og = ""
                prev_tr = ""
        if (((sent.words[len(sent.words) - 1]).text[0]).isupper()):  ##check if last token of a sent is uppercase
            html_str = update_html_colorful(html_str, prev_og[:-1], prev_tr[:-1], cats, tA1, colorls,pos,sent_id,color1)  ##update prev[:-1]
    html_str = html_str + '\n</div>\n</body>\n</html>'
    return html_str

def search_dict(phrase_tr,phrase_og,sent_id,curr_html,tA1):
    if (phrase_tr in dict.keys()):
        values = dict[phrase_tr]
        if (values[0] == ""):##searched for, without annotation
            return (curr_html + tA1[0] + phrase_og + tA1[1])
        else:##searched for, without annotation
            sentID.append(sent_id)
            phrase.append(phrase_og)
            link.append(values[0])
            ont.append(values[1])
            tA2 = ['<a style=\"color:' + values[2] + '\" href=\"', '\">', '</a> ']
            return (curr_html + tA2[0] + values[0] + tA2[1] + phrase_og + tA2[2])
    else:
        return ""


def update_html(curr_html,phrase_og,phrase_tr,cats,tA1,tA2,pos,sent_id,color1,color2):
    sr=search_dict(phrase_tr,phrase_og,sent_id,curr_html,tA1)
    if(sr!=""):
        return sr
    if(eligible(phrase_tr)and pos):
        query_s = form_query_string(phrase_tr, cats)
        yago_results_df = obtain_results_df(query_s)
        if ("1" in yago_results_df.columns):
            temp = yago_results_df["1"]
            temp = list(temp[temp.notna()])
            if(len(temp)==1 and fuzz.ratio((split("_Q[0-9]+",[str(x).split("/")[-1:][0] for x in temp][0]))[0],phrase_tr)<42):##without annotation
                updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
            elif(len(temp)==1):##with annotation
                sentID.append(sent_id)
                phrase.append(phrase_og)
                link.append(str(temp[0]))
                ont.append("schema:Thing")
                dict.update({phrase_tr: [str(temp[0]), "schema:Thing",color2]})
                return (curr_html + tA2[0] + str(temp[0]) + tA2[1] + phrase_og + tA2[2])
            else:
                temp = select_best_link(temp, phrase_tr)  ##sort by levenstein's distance
                if (temp == ""):##without annotation
                    updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
                else:##with annotation
                    sentID.append(sent_id)
                    phrase.append(phrase_og)
                    link.append(str(temp))
                    ont.append("schema:Thing")
                    dict.update({phrase_tr: [str(temp), "schema:Thing",color2]})
                    return (curr_html +tA2[0] + str(temp) + tA2[1] + phrase_og + tA2[2])
        else:##without annotation
            updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
    else:##without annotation
        updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
    dict.update({phrase_tr: ["", "",color1]})
    return updated_html


def update_html_colorful(curr_html,phrase_og,phrase_tr,cats,tA1,color_ls,pos,sent_id,color1):
    sr=search_dict(phrase_tr,phrase_og,sent_id,curr_html,tA1)
    if(sr!=""):
        return sr
    if(eligible(phrase_tr)and pos):
        for cat_id in range(len(cats)):
            color2=color_ls[cat_id]
            tA2 = ['<a style=\"color:' + color2 + '\" href=\"', '\">', '</a> ']
            query_s = form_query_string(phrase_tr, [cats[cat_id]])
            yago_results_df = obtain_results_df(query_s)
            if ("1" in yago_results_df.columns):
                temp = yago_results_df["1"]
                temp= list(temp[temp.notna()])
                if(len(temp)==1 and fuzz.ratio((split("_Q[0-9]+",[str(x).split("/")[-1:][0] for x in temp][0]))[0],phrase_tr)<42):##without annotation
                    updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
                elif(len(temp)==1):##with annotation
                    sentID.append(sent_id)
                    phrase.append(phrase_og)
                    link.append(str(temp[0]))
                    ont.append(str(cats[cat_id]))
                    dict.update({phrase_tr: [str(temp[0]), str(cats[cat_id]),color2]})
                    return (curr_html + tA2[0] + str(temp[0]) + tA2[1] + phrase_og + tA2[2])
                else:
                    temp=select_best_link(temp,phrase_tr)##rank by levenstein's distance
                    if(temp==""):##without annotation
                        updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
                    else:##with annotation
                        sentID.append(sent_id)
                        phrase.append(phrase_og)
                        link.append(str(temp))
                        ont.append(str(cats[cat_id]))
                        dict.update({phrase_tr: [str(temp), str(cats[cat_id]),color2]})
                        return (curr_html +tA2[0] + str(temp) + tA2[1] + phrase_og + tA2[2])
            else:##without annotation
                updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
    else:##without annotation
        updated_html = curr_html + tA1[0] + phrase_og + tA1[1]
    dict.update({phrase_tr: ["", "",color1]})##only those without annotation will get to this line
    return updated_html

def select_best_link(temp,phrase_tr):
    temp0 = [str(x).split("/")[-1:][0] for x in temp]
    temp1 = [split("_Q[0-9]+", l)[0] for l in temp0]
    for i in range(len(temp0)): ##check if there is an exact match
        if(temp0[i].lower().replace("_"," ")==phrase_tr.lower()):
            return temp[i]
    scores = [fuzz.ratio(phrase_tr, y) for y in temp1]
    if(max(scores)>42):
        return temp[scores.index(max(scores))]
    else:
        return ""

def form_query_string(phrase, ont_ls):

        query_body = ''
        query_s = 'PREFIX owl: <http://www.w3.org/2002/07/owl#>' + '\n' \
                  + 'PREFIX schema: <http://schema.org/>' + '\n' \
                  + 'PREFIX bioschemas: <http://bioschemas.org/>'+ '\n' \
                  + 'PREFIX yago: <http://yago-knowledge.org/resource/>' + '\n' \
                  + 'PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>' + '\n' \
                  + 'PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>' + '\n' \
                  + 'SELECT DISTINCT'
        #repeat = len(phrase.split())
        #reg = "[A-Za-z0-9-]+(_)" * repeat
        #reg = reg[:-3]  # remove the last (_)
        #reg = reg + "(($)|(_Q[0-9]+))"
        query_s = query_s + '?' + 'w1'
        query_body = query_body + 'OPTIONAL{{?' + 'w1 '+ 'rdfs:label' + " \"" + phrase+ "\"" + '@en}UNION{?' + 'w1 ' + 'schema:alternateName' + " \"" + phrase + "\"" + '@en}.'
        for ont in ont_ls:
            query_body = query_body + '{?' + 'w1' + ' rdfs:subClassOf* ' + str(ont) + '}UNION' + '{?' + 'w1'  + ' rdf:type ' + str(ont) + '} UNION'
        query_body = query_body[:-5]+ "}."
        #' FILTER regex(STR(?' + 'w1' + '), ' + "\"/" + reg + "\"," + "\"i\"" + ")}."
        #" FILTER (lang(?w1)='en')}. "
        query_s = query_s + "\nWHERE { "
        query_s = query_s + query_body
        query_s = query_s + "}"
        return query_s


def eligible(phrase):
    if([x for x in phrase if (not (x in allpunks)) ]!=[] and len(phrase)>2 and phrase.lower()!="not"):
        return True
    else:
        return False

def obtain_results_df(querystring):
    sparql.setQuery(querystring)
    sparql.setReturnFormat(JSON)
    results=sparql.query().convert()
    results_df = pd.json_normalize(results['results']['bindings'])
    cols=[col for col in results_df.columns if col[-5:]!='.type']
    results_df=results_df[cols]
    results_df=results_df.rename(columns=lambda x:str(int(re.search('w(.*).value',x).group(1))))
    return results_df

# YAGO_annotate('C:\\Users\\angel\PycharmProjects\BINLP\src\Three_Littles_Pigs.txt','','C:\\Users\\angel\PycharmProjects\BINLP\src',[],'blue',['green'])