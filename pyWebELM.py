__author__ = 'will'
import re
import os
from mechanize import Browser
from multiprocessing import Pool
from BeautifulSoup import BeautifulSoup
import logging
import argparse



class Annot():
    def __init__(self, NAME, START_POS, END_POS, TYPE):
        self.name = NAME
        self.start = START_POS
        self.end = END_POS
        self.type = TYPE

    def __eq__(self, VAL):
        return self.name == VAL.name

    def __str__(self):
        this_str = self.name + '\t'
        this_str += str(self.start) + '\t'
        this_str += str(self.end)

        return this_str


class Protein():
    def __init__(self, REF_PROT, AA_SEQ):
        self.aa_seq = AA_SEQ
        self.ref_prot = REF_PROT
        self.annot = []
        #self.neighbors = []

    def HasAnnot(self, ANNOT_NAME):
        """
        Checks to see if this Protein has requested ELM
        """
        return Annot(ANNOT_NAME, None, None, None) in self.annot


    def AnnotELMs(self, CACHE_DIR, FORCE_DL = 0):
        """
        Makes a call to CheckELM and ReadData to annotate the ELMs on this
        protein.  Saves the downloaded .html file to CACHE_DIR to speed up
        future retrievals.
        FORCE_DL == 0
            Will only process the cached data and NEVER make a server request.
        FORCE_DL == 1
            Will process cached data if present and will make a server request
            if the data is absent in the cache.
        FORCE_DL == 2
            Will ALWAYS make a server request and will overwrite the cached
            data.

        """

        if FORCE_DL == 0:
            self.annot = ReadData(CACHE_DIR + self.ref_prot + '.html')
            logging.info('File Read\t ' + self.ref_prot)
            #this_string = string.join(self.elm_annot())
            #logging.info()
            return


        file_present = (self.ref_prot + '.html') in os.listdir(CACHE_DIR)
        want_retrieve = FORCE_DL >= 1
        force_retrive = FORCE_DL >= 2

        if force_retrive | (want_retrieve and not file_present):
            try:
                CheckELM(self.aa_seq, CACHE_DIR + self.ref_prot + '.html')
            except:
                logging.warning('Could not retrive\t ' + self.ref_prot)

        self.annot = ReadData(CACHE_DIR + self.ref_prot + '.html')
        logging.info('File Read\t ' + self.ref_prot)


def ReadData(html):

    outresults = []
    robj = re.compile(r'<b>(.*?)</b>')
    soup = BeautifulSoup(html)
    charttag = soup.find('map', attrs={'name':'ELMchart'})
    for tag in charttag.findAll(lambda tag:tag['href'].startswith('#')):
        desc = tag['alt']
        outresults.append((desc[:desc.find(':')], robj.findall(desc)))

    return outresults



def SubmitELMServer(input_seq):
    """Submits a query to the ELM webtool and returns a HTML of the response"""

    browser = Browser()
    base_url = 'http://elm.eu.org/'

    browser.open(base_url)
    browser.select_form(nr=0)
    browser['sequence'] = input_seq
    oresp = browser.submit_form()
    nhtml = oresp.read()
    soup = BeautifulSoup(nhtml)
    tag = soup.find('meta', attrs = {'http-equiv':'REFRESH'})
    loc = tag['content'].find('URL=')
    nurl = base_url+tag['content'][loc+4:]

    dataresp = browser.open(nurl)
    return dataresp.read()






if __name__ == '__main__':

    parser = argparse.ArgumentParser('Web ELM Parser')
    parser.add_argument('-i', '--input_file',
                        dest = 'INPUT_FASTA_FILE',
                        type=str,
                        help = 'Input File Path')
    parser.add_argument('-o', '--output_file',
                        dest = 'OUTPUT_FILE',
                        type=str,
                        default = 'elm_results.txt',
                        help = 'Output File Path')
    parser.add_argument('-t', '--threads',
                        dest = 'NUM_THREADS',
                        default = 10,
                        type = 'int',
                        help = 'Number of Threads to use for the ELM server')

    args = parser.parse_args()


