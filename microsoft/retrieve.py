import time
import requests

class AK_API:
    starting_year = 2005
    offset = 20000

    def get_credentials(self):
        '''Get API key
        Returns:
            (string) -- API Key
        '''
        key = raw_input('What is your API key? ')
        return key
        
    def get_author(self):
        '''Get author name for query
        Returns:
            (string) -- author name, lowercase
        '''
        author = raw_input('What is the name of the author to search for? ')
        return author.lower()
        
    def evaluate(self):
        '''Perform GET request to API "evaluate" command
        '''        
        key = self.get_credentials()       
        current_year = time.strftime("%Y")
        count = 0
        
        while(True):
            url = 'https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?'
            
            data = {}
            data['expr'] = 'Y=[{starting_year},{current_year}]'.format(starting_year = self.starting_year, current_year = current_year)
            data['attributes'] = 'Ti,Y,CC,AA.AuN,AA.AuId,AA.AfN,F.FN,J.JN'
            data['count'] = self.offset
            data['offset'] = count * self.offset
            
            # add parameters to url
            for k, v in data.iteritems():
                url += k + '=' + str(v) + '&'
            
            headers = {
                'Ocp-Apim-Subscription-Key': key,
            }       
            
            print 'Getting items at {number} ...'.format(number = count * self.offset)
            r = requests.get(url, headers = headers)
            
            if('error' in r.json()):
                print r.json()['error']
                return
            
            print 'Saving current result ...'
            with open('result' + str(count) + '.json', 'w+') as f:
                f.write(r.content)
                
            count += 1
            
        print 'Complete.'
        
if(__name__ == '__main__'):
    a = AK_API()
    a.evaluate()
