import csv
import requests
import jinja2

html_file = 'report.html'

fos_url = 'https://raw.githubusercontent.com/cloudmesh/metric/master/report/data-fos.csv'
org_url = 'https://raw.githubusercontent.com/cloudmesh/metric/master/report/data-org.csv'

def csv_to_json(req):
    reader = csv.DictReader(req.splitlines())
    json = []
    for row in reader:
        json.append(row)
        
    return json
    
fos = csv_to_json(requests.get(fos_url).text)
org = csv_to_json(requests.get(org_url).text)

loader = jinja2.FileSystemLoader(searchpath = 'templates/')
env = jinja2.Environment(loader = loader)

template = env.get_template('report.html')

out = template.render(fos = fos, org = org)

with open(html_file, 'w+') as f:
    f.write(out)
