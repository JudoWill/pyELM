__author__ = 'will'
import re
import os
from mechanize import Browser
from multiprocessing import Pool
from BeautifulSoup import BeautifulSoup
from itertools import groupby, tee
import logging
import argparse




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



def fasta_iter(fasta_file):

    with open(fasta_file) as handle:
        header = None
        for key, lines in groupby(handle, lambda x: x.startswith('>')):
            if key:
                header = lines.next().strip()[1:]
            else:
                seq = ''.join(x.strip() for x in lines)
                yield header, seq


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


