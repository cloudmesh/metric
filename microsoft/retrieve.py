import requests

class AK_API:
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
        query = {}
        
        key = self.get_credentials()
        query['author'] = self.get_author()
        
        url = "https://westus.api.cognitive.microsoft.com/academic/v1.0/evaluate?expr=Composite(AA.AuN=='{author}')&attributes=Ti,Y,CC,AA.AuN,AA.AuId".format(**query)
        
        headers = {
            'Ocp-Apim-Subscription-Key': key,
        }       
        
        print 'Performing query for author: {author}.'.format(**query)
        r = requests.get(url, headers = headers)
        
        print 'Saving result'
        with open('result.json', 'w+') as f:
            f.write(r.content)
            
        print 'Complete.'
        
if(__name__ == '__main__'):
    a = AK_API()
    a.evaluate()
