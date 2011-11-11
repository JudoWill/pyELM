__author__ = 'will'
import re
import csv
from mechanize import Browser
from multiprocessing import Pool
from BeautifulSoup import BeautifulSoup
from itertools import groupby, tee, izip
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



def SubmitELMServer(input_tup):
    """Submits a query to the ELM webtool and returns a HTML of the response"""

    input_name, input_seq = input_tup
    browser = Browser()
    base_url = 'http://elm.eu.org/'

    try:
        browser.open(base_url)
        browser.select_form(nr=0)
        browser['sequence'] = input_seq
        oresp = browser.submit()
        nhtml = oresp.read()
        soup = BeautifulSoup(nhtml)
        tag = soup.find('meta', attrs = {'http-equiv':'REFRESH'})
        loc = tag['content'].find('URL=')
        nurl = base_url+tag['content'][loc+4:]

        dataresp = browser.open(nurl)
        return input_name, dataresp.read()
    except:
        return input_name, None



def fasta_iter(fasta_file):

    with open(fasta_file) as handle:
        header = None
        for key, lines in groupby(handle, lambda x: x.startswith('>')):
            if key:
                header = lines.next().strip()[1:]
            else:
                seq = ''.join(x.strip() for x in lines)
                yield header, seq

def extract_numbers(instr):
    return [int(x) for x in re.findall('(\d+)', instr)]

def process_fasta_file(fasta_file, out_file, num_processes):

    pool = Pool(processes = num_processes)

    outgen = pool.imap(SubmitELMServer, fasta_iter(fasta_file), chunksize=2*num_processes)

    with open(out_file, 'w') as handle:
        writer = csv.writer(handle, delimiter = '\t')
        writer.writerow(['Header', 'ELM', 'Start', 'End', 'Match'])
        for name, html in outgen:
            if html:
                out = ReadData(html)
                logging.warning('%s had %i matches' % (name, len(out)))
                for elm, pos in out:
                    out = [name, elm] + extract_numbers(pos[0]) + [pos[1]]
                    writer.writerow(out)
            else:
                logging.warning('%s had no ELMs' % name)

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Web ELM Parser')
    parser.add_argument('-i', '--input_file',
                        dest = 'ifile',
                        type=str,
                        help = 'Input File Path')
    parser.add_argument('-o', '--output_file',
                        dest = 'ofile',
                        type=str,
                        default = 'elm_results.txt',
                        help = 'Output File Path')
    parser.add_argument('-t', '--threads',
                        dest = 'threads',
                        default = 10,
                        type = int,
                        help = 'Number of Threads to use for the ELM server')

    args = parser.parse_args()


    process_fasta_file(args.ifile, args.ofile, args.threads)