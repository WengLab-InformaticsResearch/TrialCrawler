'''
6/16/2020
Jiaqi Tang
'''
import re,math,argparse,sys
import urllib.request
import xml.etree.ElementTree as pxml
import logging
import random
import pickle
from os import listdir
from pickle import UnpicklingError



def download_web_data (url):
    try:
        req = urllib.request.Request(url, headers={ 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'})
        con = urllib.request.urlopen(url)
        html = con.read().decode('utf-8')
        con.close()
        return html
    except Exception as e:
        #log.error ('%s: %s' % (e, url))
        return None



def get_clinical_trials (file_name):	
	url = 'http://clinicaltrials.gov/ct2/crawl'
	html = download_web_data (url)
	pages = re.findall('href="/ct2/crawl/(\d+)"', str(html))
	lnct = set()
	for p in pages:
		html = None
		while html is None:
			html = download_web_data ('%s/%s' % (url, p))
		ct = re.findall(r'href="/ct2/show/(NCT\d+)"', html)
		lnct |= set(ct)

	with open(file_name, 'w') as f:
		for item in lnct:
			f.write("%s\n" % item)

def get_ecriteria (nct):
	url = 'http://clinicaltrials.gov/show/%s?displayxml=true' % nct
	try:
		txml = None
		while txml is None:
			txml = pxml.fromstring (download_web_data(url))
		ec = txml.find ('eligibility')
		details = set()
		# gender
		val = ec.find('gender')
		if val is not None:
			t = val.text.lower().strip()
			if ('both' not in t) and ('n/a' not in t):
				details.add ('gender = ' + t)
		# minimum age
		val = ec.find('minimum_age')
		if val is not None:
			t = val.text.lower().strip()
			amin = _check_age ('minimum age = ' + t)
			if amin:
				details.add (amin)
		# maximum age
		val = ec.find('maximum_age')
		if val is not None:
			t = val.text.lower().strip()
			amax = _check_age ('maximum age = ' + t)
			if amax:
				details.add (amax)
		# free-text criteria
		d = ec.find ('criteria')
		ectxt = d.find ('textblock')
		if ectxt is not None:
			ectxt = ectxt.text.encode('utf-8').strip()
		#log.info(details)

		return (details, ectxt)
	except Exception as e:
		return (set(), None)


# private functions

# check the age format
def _check_age (age):
	try:
		val = int(age[age.rfind(' '):].strip())
		return age
	except ValueError:
		if 'year' in age:
			return age[:age.rfind('y')].strip()
		if 'month' in age:
			return _format_age (age[:age.rfind('m')].strip(), float(12))
		if 'week' in age:
			return _format_age (age[:age.rfind('w')].strip(), float(52))
		if 'day' in age:
			return _format_age (age[:age.rfind('d')].strip(), float(365))
		return None
		

# format the age tag
def _format_age (age, div):
	val = int(age[age.rfind(' '):])
	if 'maximum' in age:
		return 'maximum age = %d' % math.ceil(val/div)
	if 'minimum' in age:
		return 'minimum age = %d' % math.floor(val/div)
	return None

# write an object (list, set, dictionary) to a serialized file
def write_obj (filename, data, logout = True):
	try:
		pickle.dump(data, open(filename, 'wb'))
		return True
	except Exception as e:
		if logout is True:
			log.error(e)
		return False





def trial_scrape (nct_filename,dout = './output/'):
	'''get ec

	Args:
		nct_filename: filename for nctid
		dout: location for saving ec data
	'''
    # get the list of clinical trials
    print('downloading the list of clinical trials')
    lnct = [line.strip() for line in open(nct_filename)]
    print('LOAD ALL NCT ID INFORMATION!')

    if len(lnct) == 0:
        print(' --- not found any clinical trials - interrupting')
        return
    print(' --- found %d clinical trials ' % len(lnct))

   
    # get the eligibility criteria
    print('downloading the eligibility criteria for %d trials' % len(lnct))

    #save nct_ec and lnct_ec from web
    existing_nct_list=listdir(dout)
    cur_count=0
    while cur_count<len(lnct):
        nct=lnct[cur_count]
        cur_count+=1
        new_name=nct+'.pkl'
        if new_name not in existing_nct_list:
            ec = get_ecriteria (nct)
            if ec[1] is not None:                
                write_obj(dout+nct+'.pkl',ec)


def combine_all_ec(filepath):
	existing_nct_list=listdir(filepath)
	nct_ec = {}
	for name in existing_nct_list:
		nct=name.split('.')[0]
		file=open(filepath+name, 'rb')
		try:
			p_t=pickle.load(file)
			file.close()
			nct_ec[nct] = p_t.decode('utf-8')
		except UnpicklingError:
			ec = ctgov.get_ecriteria (nct)
			nct_ec[nct]=ec[1].decode('utf-8')
		write_obj (filepath+'nctec-mining.pkl', nct_ec)

if __name__=="__main__":
	#file for nct_id
    filename=('data/nct_id.txt')
    get_clinical_trials(filename)
    print('All NCTID Downloaded!')
    trial_scrape('data/nct_id.txt','data/')
    print('task completed\n')

