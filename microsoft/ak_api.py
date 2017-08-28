'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate <year> [--count=<count> --start=<start>]
  ak_api.py range <start> <end>
  ak_api.py extended <year> [--count=<count> --start=<start> --offset=<offset>]
  ak_api.py january <year> [--count=<count>]
  ak_api.py match <filename> [--count=<count>, --start=<start>]
  ak_api.py journals
  ak_api.py xsede
  ak_api.py bridges
  ak_api.py fields [--count=<count> --start=<start>]
  ak_api.py citations <filename>

Options:
  year:     year to retrieve publications for
  count:    number of entities to retrieve per call
  start:    month/year to begin on
  end:      month/year to end on
'''

import time, json, re, calendar, string, os.path, ConfigParser, sys
import requests, pymongo, numpy, mlpy
from docopt import docopt
from doc_parse import DocParser

class AK_API:
    db_name = 'microsoft'
    
    def __init__(self):
        self.mongo_connect()
        DocParser(__doc__).parse_doc(self)
    
    def mongo_connect(self):
        '''Connect to MongoDB
        '''
        opts = {}
        opts['port'] = int(self.get_config_option('mongo', 'port'))
        
        print 'Connecting to MongoDB on port {port} ...'.format(**opts)
        
        self.client = pymongo.MongoClient(**opts)
        self.db = self.client[self.db_name]
        
        collection_names = self.db.collection_names()
        
        # create indexes
        if('publications' not in collection_names):
            self.db.publications.create_index('Id', unique = True)
            
        if('extended' not in collection_names):
            self.db.extended.create_index('Id', unique = True)
            
        if('fields' not in collection_names):
            self.db.fields.create_index('Id', unique = True)
            
        if('journals' not in collection_names):
            self.db.journals.create_index('JId', unique = True)
            
        if('xsede' not in collection_names):
            self.db.xsede.create_index('Id', unique = True)

    def get_credentials(self):
        '''Get API key
        Returns:
            (string) -- API Key
        '''
        print 'Getting API key ...'
        
        key = self.get_config_option('api', 'key')

        if(not key):   
            key = raw_input('What is your API key? ')
            
        return key
        
    def get_config_option(self, section, option):
        '''Get configuration item
        Args:
            section (str): config section
            option (str): item in section
        Return:
            str: config item
        '''
        
        if(os.path.isfile('ak_api.cfg')):
            config = ConfigParser.SafeConfigParser()
            config.readfp(open('ak_api.cfg'))
            option = config.get(section, option)
            return option
        else:
            print 'Unable to locate configuration file.'
            return None
        
    def evaluate(self, year, count = 100000, start = 0, offset = 0):
        '''Perform GET request to API "evaluate" command
        Args:
            year (str) -- year to update
            count (int) -- results per call
            start (int) -- month to start on (0 being January)
        '''
        count = int(count)
        key = self.get_credentials()
        attributes = 'Id,Ti,L,Y,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.CId,C.CN,RId'
        
        if(start == 0):
            self.january(year, count, attributes)
            start = 1
        
        for m in xrange(int(start), 12):
            date = {}
            date['year'] = year
            date['month'] = str(m + 1) if m > 8 else '0' + str(m + 1)
            date['day'] = calendar.monthrange(int(year), m + 1)[1]
            print "Getting results for {year}-{month} ...".format(**date)
            expr = "D=['{year}-{month}-01','{year}-{month}-{day}']".format(**date)         
            self.retrieve_pubs(year, count, offset, key, attributes, self.add_pubs, expr = expr)
            offset = 0
            
    def range(self, start, end, count = 100000):
        '''Wrapper for evaluate, by year
        Args:
            start (int) -- year to start
            end (int) -- year to end
            count (int) -- results per call
        '''
        for year in xrange(int(start), int(end) + 1):
            self.evaluate(year, count = count)
        
    def extended(self, year, count = 999, start = 0, offset = 0):
        '''Get extended metadata
        Args:
            year (str) -- year to update
            count (int) -- results per call
            start (int) -- month to start on (0 being January)
        '''
        count = int(count)
        key = self.get_credentials()
        
        if(start == 0):
            self.january(year, count, 'E')
            start = 1
        
        for m in xrange(int(start), 12):
            date = {}
            date['year'] = year
            date['month'] = str(m + 1) if m > 8 else '0' + str(m + 1)
            date['day'] = calendar.monthrange(int(year), m + 1)[1]
            expr = "D=['{year}-{month}-01','{year}-{month}-{day}']".format(**date)
            print "Getting results for {year}-{month} ...".format(**date)            
            self.retrieve_pubs(year, count, offset, key, 'E', self.add_extended, expr = expr)
            offset = 0
            
    def january(self, year, count = 100000, attributes = '', offset = 0):
        '''Get publications for January of given year, by title
        Args:
            year (str) -- year to retrieve
            count (int) -- number of results per call
        '''
        count = int(count)
        key = self.get_credentials()
        attributes = attributes if attributes else 'Id,Ti,L,Y,D,CC,ECC,AA.AuN,AA.AuId,AA.AfN,AA.AfId,AA.S,F.FId,F.FN,J.JId,J.JN,C.CId,C.CN,RId'
        
        for l in string.lowercase:
            print "Retrieve January publications for {year} starting with {letter} ...".format(letter = l, year = year)
            expr = "And(Ti='{letter}'...,D=['{year}-01-01','{year}-01-31'])".format(letter = l, year = year)
            self.retrieve_pubs(year, count, offset, key, attributes, self.add_pubs, expr = expr)
            offset = 0
        
    def bridges(self):
        '''Get bridges publications
        '''
        print "Matching Bridges publications ..."

        matches = []
        with open('bridges.txt') as f:
            for row in f.readlines():
                bid, title = row.strip().split('|')
                
                pub = self.db.publications.find_one({'Ti': self.convert_title(title)})
                if(pub):
                    matches.append(bid + '|' + str(pub['Id']) + '|' + str(pub['CC']) + '\n')
                    
        with open('bridges_ms.txt', 'w+') as f:
            f.writelines(matches)
        
        print "Complete."
        
    def retrieve_pubs(self, year, count, offset, key, attributes, hook, expr = ''):
        '''Get publications from via API
        Args:
            year (str) -- year
            attributes (str) -- paper entity attributes to retrieve
            start (int) -- month to start on
            callback (function) -- function to handle results 
        '''
        offset = int(offset)
        data = {}
        data['expr'] = expr
        data['attributes'] = attributes
        data['count'] = count
        retries = 0
        max_retries = 100
        wait_time = 30
    
        while(True):
            if(retries >= max_retries):
                sys.exit("Retry limit exceed. Exiting.")
                
            data['offset'] = offset
            
            # add parameters to url
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print "Getting items from {} to {} ...".format(offset + 1, offset + count)
            
            try:
                r = requests.get(url, headers = headers)              
            except requests.exceptions.ChunkedEncodingError:
                print "Connection reset. Trying again ..."
                continue
            
            try:
                result = r.json()
            except:
                print "Error. Did not receive JSON. Retrying ..."
                retries += 1
                time.sleep(wait_time)
                continue

            if('error' in result):
                print "Server error. Retrying ..."
                retries += 1
                print result['error']
                time.sleep(wait_time)
                continue
                
            if(r.status_code == 500):
                print "Server error. Retrying ..."
                retries += 1
                time.sleep(wait_time)
                continue
            
            entities = [e for e in result['entities'] if e]
            
            print "{} results retrieved".format(len(entities))
            
            if(len(entities) == 0):
                print "0 found. Retrying ..."
                time.sleep(wait_time)
                retries += 1
                continue
            
            if(len(entities)):
                hook(entities)
                offset += count
                
                if(len(entities) < count):
                    break
            else:
                break
        
    def add_pubs(self, pubs):
        '''Add publication data to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB ...'
        
        bulk = self.db.publications.initialize_unordered_bulk_op()
        
        for pub in pubs:
            bulk.find({'Id': pub['Id']}).upsert().replace_one(pub)
        try:
            bulk.execute()
        except pymongo.errors.BulkWriteError as bwe:
            print bwe.details
            
    def add_extended(self, pubs):
        '''Add extended metadata to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB ...'
        
        bulk = self.db.extended.initialize_unordered_bulk_op()
        
        for pub in pubs:
            bulk.find({'Id': pub['Id']}).upsert().replace_one(pub)
        try:
            bulk.execute()
        except pymongo.errors.BulkWriteError as bwe:
            print bwe.details
        
    def fields(self, count = 100000, start = 0):
        '''Add field of study parents
        Warning:
            Microsoft has duplicate entries for any given field name, field names from FieldsOfStudy.txt do not match current field names retrieved from API
        '''
        print 'Getting parent fields ...'
        
        with open('FieldsOfStudy.txt') as f:
            fields = {}
            for row in f.readlines():
                fid, fname = row.split('\t')
                # replace em dash with minus
                fname = re.sub('\xe2\x80\x93', '-', fname)
                fields[fid] = fname.strip().lower()
            
            # reverse fields dict
            ids = dict(zip(fields.values(), fields.keys()))

        # cache tree
        with open('FieldOfStudyHierarchy.txt') as f:
            children = {}
            for row in f.readlines():
                ci, cl, pi, pl, p = row.split()
                
                if(pl == 'L0' and pi not in children):
                    children[pi] = {'parents': [], 'level': 'L0'}
                
                child = children.get(ci)
                if(child):
                    child['parents'].append({'id': pi, 'prob': float(p)})
                else:
                    children[ci] = {'parents': [{'id': pi, 'prob': float(p)}], 'level': cl}
                
        # build branches
        for child, branch in children.iteritems(): 
            for parent in branch['parents']:
                if(parent['id'] in children):
                    parent['pointer'] = children[parent['id']]
                    
            # remove parents with no pointer
            branch['parents'] = [p for p in branch['parents'] if 'pointer' in p]
        
        # get probabilities            
        def get_prob(parent, probs = []):
            '''recursive function for tree traversal through fields of study hierarchy
            '''
            for parent in parent['pointer']['parents']:
                new_prob = parent['prob'] * probs[-1][1] if probs else float(parent['prob'])
                probs.append((parent['id'], new_prob))
                get_prob(parent, probs)
                
            return probs
            
        parents = {}
        for child, branch in children.iteritems():
            # check if the "child" is a top-level parent
            if(children[child]['level'] == 'L0'):
                top = (child,)
            else:
                probs = []
                for parent in branch['parents']:
                    probs.extend(get_prob(parent, [(parent['id'], parent['prob'])]))
                
                # determine best probability
                top = (None, 0)
                for prob in probs:
                    pid, probability = prob
                    if(children[pid]['level'] == 'L0' and probability > top[1]):
                        top = prob
            
            parents[child] = fields.get(top[0])
        
        records = self.db.publications.find()
        total = records.count()
        fos = []
        
        for i, record in enumerate(records):
            sys.stdout.write("\r{}/{}".format(i, total))
            sys.stdout.flush()
            
            if('F' in record):
                for field in record['F']:
                    fid = field['FId']
                    field_name = field['FN']                   
                    old_field_id = ids.get(field_name)
        
        self.db.fos.insert_many(fos)    
        print 'Complete.'
        
    def journals(self):
        print "Getting records ..."
        records = self.db.publications.find({}, {'Id': 1, 'CC': 1, 'J': 1})
    
        print "Analyzing journals ..."
        journals = {}
        counter = 0
        count = records.count()
        for record in records:
            counter += 1
            sys.stdout.write('\r' + str(counter) + '/' + str(count))
            sys.stdout.flush()
            
            if('J' in record):
                pid = record['Id']
                
                extended = self.db.extended.find_one({'Id': pid})
                
                if(extended and 'E' in extended):
                    extended_parsed = json.loads(extended['E'])
                    
                    if('I' in extended_parsed and 'V' in extended_parsed):
                        jid = record['J']['JId']
                        volume = extended_parsed['V']
                        issue = extended_parsed['I']
                        
                        cc = record['CC']
                        
                        if(jid in journals):
                            journal = journals[jid]
                            
                            if(volume in journal['volumes']):
                                if(issue in journal['volumes'][volume]['issues']):
                                    journal['volumes'][volume]['issues'][issue]['citations'].append(cc)
                                else:
                                    journal['volumes'][volume]['issues'][issue] = {'citations': [cc]}
                            else:
                                journal['volumes'][volume] = {'issues': {issue: {'citations': [cc]}}}
                        else:
                            journals[jid] = {'JId': jid, 'volumes': {volume: {'issues': {issue: {'citations': [cc]}}}}}
                        
        print
        print "Converting journals to MongoDB-friendly format..."
        
        insert = []                
        for journal in journals.values():
            volumes = []
            for vid, volume in journal['volumes'].items():
                issues = []
                for iid, issue in volume['issues'].items():
                    issue.update({'issue': iid})
                    issues.append(issue)
                
                volume['issues'] = issues
                volume.update({'volume': vid})
                volumes.append(volume)
                
            journal['volumes'] = volumes
            insert.append(journal)
        
        print "Inserting journals into database ..."                    
        self.db.journals.insert_many(journals.values(), ordered = False)
        
    def citations(self, filename):
        citations = []
        with open(filename) as f:       
            for row in f.readlines():
                if('|' not in row):
                    continue
                    
                pid, mid = row.strip().split('|', 1)
                pub = self.db.publications.find_one({'Id': int(mid)})
                if(pub and 'CC' in pub):
                    citations.append(pid + '|' + str(pub['CC']) + '\n')
        
        new_file = '{0}_citations.{1}'.format(*filename.split('.'))
        print "Saving file {}".format(new_file)
        with open(new_file, 'w+') as f:
            f.writelines(citations)       
        
    def xsede(self):    
        print "Gathering XD publications ..."
        ids = set()
        with open('pubs_xup_ms.txt') as f:
            for row in f.readlines():
                ids.add(int(row.strip().split('|')[1]))
            
        with open('pubs_report_ms.txt') as f:
            for row in f.readlines():
                ids.add(int(row.strip().split('|')[1]))
        
        xsede = []
        total = len(ids)
        for i, xid in enumerate(ids):
            sys.stdout.write("\r{}/{}".format(i + 1, total))
            sys.stdout.flush()

            pub = self.db.publications.find_one({'Id': xid})
            extended = self.db.extended.find_one({'Id': xid})
            
            xd = {}
            xd['Id'] = pub['Id']
            xd['CC'] = pub['CC']
            
            if(extended and 'E' in extended):
                ext = json.loads(extended['E'])
                pub_volume = ext.get('V')
                pub_issue = ext.get('I')
            
                if('J' in pub and pub_volume and pub_issue):
                    journal = self.db.journals.find_one({'Id': pub['J']['JId']})
                    
                    ref_volume = next((v for v in journal['volumes'] if v['volume'] == pub_volume), None)
                    ref_issue = next((i for i in ref_volume['issues'] if i['issue'] == pub_issue), None)
                    citations = ref_issue['citations']
                    citations.remove(xd['CC'])
                    
                    xd['PACC'] = numpy.mean(citations)
            xsede.append(xd)
        
        print
        print "Inserting into Mongo ..." 
        try:          
            self.db.xsede.insert_many(xsede, ordered = False)
        except pymongo.errors.BulkWriteError:
            print "Ignoring duplicate entries."
        
        print "Complete."
        
    def match(self, filename, count = 100, start = 0):
        count = int(count)
        start = int(start)
        
        pubs = []
        with open(filename) as f:       
            for row in f.readlines():
                if('|' not in row):
                    continue
                    
                pid, title = row.strip().split('|', 1)
                pubs.append((pid, title))    
                
        pubs_iter = map(None, *(iter(pubs),) * count)
        pubs_iter = pubs_iter[start:]
        current = start
        
        for cur_pubs in pubs_iter:
            print "Getting matches {} - {}".format(current * count + 1, current * count + count)
            elastic_matches = []
            for pub in [p for p in cur_pubs if p]:
                pid, title = pub
                
                ti = MSString(title, decode = 'ISO-8859-1', encode = 'utf-8')

                data = {}
                data['size'] = 1                
                data['query'] = {}
                data['query']['match'] = {'Ti': ti.to_string()}
                
                r = requests.get('http://localhost:9200/microsoft/publications/_search', data = json.dumps(data))
                
                top = next(iter(r.json()['hits']['hits'] or []), None)

                if(top):
                    top['title'] = ti.to_string()
                    top['id'] = pid
                    elastic_matches.append(top)
                
            print "Filtering matches ..."
            min_lcs = .9
            sub_boost = .2
            matches = []
            for match in elastic_matches:
                #TODO: remove duplicates
                matched = False
                xd_title = MSString(match['title']).convert()
                ms_title = MSString(match['_source']['Ti'], encode = 'utf-8').convert()
                
                lcs_len, _ = self.string_lcs(xd_title, ms_title)
                shorter = min(xd_title, ms_title, key = len)
                longer = max(xd_title, ms_title, key = len)
                shorter_rate = float(lcs_len) / len(shorter)
                longer_rate = float(lcs_len) / len(longer)
                
                # give bost to substrings
                boost = sub_boost if shorter_rate == 1.0 else 0
                
                # exact match
                if(xd_title == ms_title):
                    matched = True
                # lcs (proportionally) greater than minimum lcs
                elif(longer_rate + boost >= min_lcs):
                    matched = True
                else:            
                    print xd_title
                    print ms_title
                    print lcs_len
                    print longer_rate
                    print
                    
                if(matched):
                    matches.append(match['id'] + '|' + str(match['_source']['Id']) + '\n')
             
            print "{} / {} matches found.".format(len(matches), count)
            mode = 'a' if current > 0 else 'w+'
            print filename.split('.')
            new_file = '{0}_ms.{1}'.format(*filename.split('.'))
            print "Updating file {}...".format(new_file)
            with open(new_file, mode) as f:
                f.writelines(matches)
                
            current += 1

        print "Complete."
        
    def string_lcs(self, x, y):
        int_x = [ord(l) for l in x]
        int_y = [ord(l) for l in y]
        return mlpy.lcs_std(int_x, int_y)        
        
class MSString:
    def __init__(self, ms_string, encode = '', decode = ''):
        ms_string = ms_string.decode(decode) if decode else ms_string
        ms_string = ms_string.encode(encode) if encode else ms_string
        
        ms_string = ms_string.replace('-', ' ')
        ms_string = ms_string.replace('/', ' ')
        ms_string = ms_string.replace('+', ' ')
        ms_string = str(ms_string).translate(None, string.punctuation)
        self.ms_string = ms_string.lower()
        
    def convert(self):
        # remove whitespace
        self.ms_string = self.ms_string.translate(None, string.whitespace)
        # remove non-printable characters
        self.ms_string = ''.join(s for s in self.ms_string if s in string.printable)
        return self.ms_string
        
    def to_string(self):
        return self.ms_string            

if(__name__ == '__main__'):
    a = AK_API()
