'''Retrieval/handler for Microsoft Knowledge API

Usage:
  ak_api.py evaluate <year> [--count=<count> --start=<start>]
  ak_api.py extended <year> [--count=<count> --start=<start>]
  ak_api.py january <year> [--count=<count>]
  ak_api.py compare [--count=<count>]
  ak_api.py bridges
  ak_api.py elastic
  ak_api.py parents [--count=<count> --start=<start>]
  ak_api.py citations [--update]

Options:
  year:     year to retrieve publications for
  count:    number of entities to retrieve per call
  start:    month to begin on
'''

import time, json, re, calendar, string, os.path, ConfigParser
from difflib import SequenceMatcher
import requests, pymongo, numpy
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
        
        # create indexes
        if('publications' not in self.db.collection_names()):
            self.db.publications.create_index('Id', unique = True)
            
        if('extended' not in self.db.collection_names()):
            self.db.extended.create_index('Id', unique = True)
            
        if('fields' not in self.db.collection_names()):
            self.db.fields.create_index('Id', unique = True)

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
        
    def evaluate(self, year, count = 100000, start = 0):
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
            self.retrieve_pubs(year, count, key, attributes, self.add_pubs, expr = expr)
        
    def extended(self, year, count = 999, start = 0):
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
            self.retrieve_pubs(year, count, key, 'E', self.add_extended, expr = expr)
            
    def january(self, year, count = 100000, attributes = ''):
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
            self.retrieve_pubs(year, count, key, attributes, self.add_pubs, expr = expr)
            
    def compare(self):
        print "Matching records ..."
        
        def get_matches(f):
            ids = []
            for row in f.readlines():
                if('|' not in row):
                    continue
                    
                pid, title = row.strip().split('|', 1)
                
                title = title.decode('ISO-8859-1').encode('utf-8')
                title = self.convert_title(title)
                
                record = self.db.publications.find_one({'Ti': title})
                
                if(record and record['Y'] <= 2013):
                    ids.append(str(pid) + '|' + str(record['Id']) + '\n')
            return ids
        
        with open('pubs_xup.txt') as f:       
            ids = get_matches(f)
            
        with open('pubs_report.txt') as f:
            ids.extend(get_matches(f))
        
        print "Saving file ..."
        
        print 'Until 2013 only: ' + str(len(ids))

        with open('xd_ms.txt', 'w+') as f:
            f.writelines(ids)
        
        print "Complete."
        
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
        
    def retrieve_pubs(self, year, count, key, attributes, hook, expr = ''):
        '''Get publications from via API
        Args:
            year (str) -- year
            attributes (str) -- paper entity attributes to retrieve
            start (int) -- month to start on
            callback (function) -- function to handle results 
        '''
        offset = 0
        data = {}
        data['expr'] = expr
        data['attributes'] = attributes
        data['count'] = count
        retries = 0
        max_retries = 5
    
        while(True):
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
            
            result = r.json()

            if('error' in result):
                print result['error']
                return
                
            if(r.status_code == 500):
                if(retries < max_retries):
                    print "Server error. Retrying ..."
                    retries += 1
                    continue
                    
                print "Server error. Exiting."
                return
            
            entities = [e for e in result['entities'] if e]
            
            print "{} results retrieved".format(len(entities))
            
            if(len(entities) == 0):
                if(retries < max_retries):
                    print "0 found. Retrying ..."
                    retries += 1
                    continue
                else:
                    print "O found. Max retries exceeded. Exiting."
                    return
            
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
        
        try:
            self.db.publications.insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
            
    def add_extended(self, pubs):
        '''Add extended metadata to MongoDB
        Args:
            pubs (dict) -- of publications, from json
        '''
        print 'Saving current result in MongoDB ...'
        
        try:
            self.db.extended.insert_many(pubs, ordered = False)
        except pymongo.errors.BulkWriteError:
            print 'Ignoring duplicate entries.'
            
    def citations(self, update = False):
        '''Get citation counts
        '''        
        if(update):
            print "Updating citation count ..."
            citations = []
            pubs = self.db.publications.find({}, {'_id': 0, 'CC':1})
            
            for pub in pubs:
                citations.append(pub['CC'])
                
            self.db.meta.update({'_id': 'publications'}, {'$set': {'citations': {'total': sum(citations), 'mean': numpy.mean(citations)}}}, upsert = True)
            
        print self.db.meta.find_one({'_id': 'publications'})
        
    def parents(self, count = 100000, start = 0):
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
        records.skip(int(start) * int(count))    
        progress = int(start)
        while records.alive:
            print "Initializing MongoDB bulk insert for records {} - {} ...".format(progress * count + 1, progress * count + int(count))
            progress += 1
                   
            bulk = self.db.fields.initialize_unordered_bulk_op()
            
            counter = 0
            for record in records:
                counter += 1
                if('F' in record):
                    top_fields = []
                    for field in record['F']:
                        if('FN' in field):
                            field_name = field['FN']                   
                            field_id = ids.get(field_name)
                                    
                            if(field_id):
                                parent = parents.get(field_id)
                                if(parent and parent not in top_fields):
                                    top_fields.append(parent)
                                             
                    bulk.insert({'Id': record['Id'], 'fields': top_fields})
                    
                if(counter >= int(count)):
                    print "Executing MongoDB bulk insert ..."
                    try:
                        bulk.execute()
                    except pymongo.errors.BulkWriteError:
                        print "Ignoring Duplicates."
                        
                    break
            
        print 'Complete.'
        
    def convert_title(self, title):
        '''Convert title to match MS naming scheme
        Args:
            title (str) -- title to convert
        Returns:
            (str) -- converted
        '''
        title = title.replace('-', ' ')
        title = title.replace('/', ' ')
        title = title.replace('+', ' ')
        title = str(title).translate(None, string.punctuation)
        return title.lower()
        
    def elastic(self):
        print "Querying elastic server ..."
        
        score_threshold = 30
        lcs_threshold = .25

        potential_matches = []
        counter = 0
        with open('pubs_xup.txt') as f:
            for row in f.readlines():
                if('|' not in row):
                    continue
                    
                pid, title = row.strip().split('|', 1)
                title = title.decode('ISO-8859-1').encode('utf-8')
                title = self.convert_title(title)

                data = {}
                data['size'] = 1
                
                data['query'] = {}
                data['query']['bool'] = {}
                data['query']['bool']['must'] = {}
                data['query']['bool']['must']['match'] = {
                    'Ti': {
                        'query': title,
                        'minimum_should_match': '50%'
                    }
                }
                
                data['query']['bool']['should'] = {}
                data['query']['bool']['should']['match_phrase'] = {
                    'Ti': {
                        'query': title,
                        'slop': 2
                    }
                }
                
                r = requests.get('http://localhost:9200/microsoft/publications/_search', data = json.dumps(data))
                
                top = next(iter(r.json()['hits']['hits'] or []), None)

                if(top):
                    top['title'] = title
                    potential_matches.append(top)
        
        print "Filtering matches ..."
        matches = []
        for match in potential_matches:
            #TODO: remove duplicates
            xd_title = match['title']
            ms_title = match['_source']['Ti']
            score = match['_score']
            s = SequenceMatcher(None, xd_title, ms_title) #FIXME: should spaces be added to junk?
            
            # get lcs, compare with longer of the two #FIXME: is this the best way?
            lcs = s.find_longest_match(0, len(xd_title), 0, len(ms_title))[2] / max(len(xd_title), len(ms_title))
            
            if(xd_title.replace(' ', '') == ms_title.replace(' ', '')):
                matches.append(match)
            elif(score >= score_threshold and lcs >= lcs_threshold):
                matches.append(match)
        
        matches = sorted(matches, reverse = True, key = lambda m: m['_score'])
        
        for match in matches:
            print match['title']
            print match['_source']['Ti']
            print match['_score']
            print
            
        print str(len(matches)) + " matches."

if(__name__ == '__main__'):
    a = AK_API()
