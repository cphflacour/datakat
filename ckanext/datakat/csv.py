import os
import pylons
import inspect
import losser.losser
import re
from collections import OrderedDict
from ckan.logic import get_action
from ckan.controllers.admin import AdminController
import ckan.lib.helpers as h

class CsvExportController(AdminController):
    """This controller exports datasets to a CSV file. Requires sysadmin role to download as private datasets are also included"""

    def _absolute_path(self, relative_path):
        """Return an absolute path given a path relative to this Python file."""
        return os.path.join(os.path.dirname(os.path.abspath(
            inspect.getfile(inspect.currentframe()))), relative_path)

    def transform(self, results):
        """Prepares JSON values for CSV export."""
        for result in results:

            if result['maintainer'] and result['maintainer_email']:
                result['maintainer'] = '"' + result['maintainer'] + '" <' + result['maintainer_email'] + '>'

#            if result['bydata'] and result['bydata_email']:
            try:
                result['bydata'] = '"' + result['bydata'] + '" <' + result['bydata_email'] + '>'
            except:
                pass

            if result['notes']:
                result['notes'] = result['notes'].replace('"','')

            result['tags'] = [tag['display_name'] for tag in result['tags']]

            if result['organization']:
                result['organization'] = result['organization']['title']

            result['link'] = h.url_for(controller='package', action='read', id=result['name'], _external=True)
                
        #Handle extra fields
        try: 
            for elem in result['extras']:
                key = elem['key']
            value = elem['value']
            if key != "":
                result[key] = value
        except Exception as e:
            pass
            
        #losser format for all resources: "Resourcer": {pattern": ["^resources$", "url"]}
        #Check if some data comes from the geoserver
        for res in result['resources']:
            url = res['url']
            #result['geoserver'] = url
            if re.search('http://wfs-kbhkort.kk.dk/k101/ows?',url):
                result['geoserver'] = "true"

    def download(self):
        """Uses package_search action to get all datasets in JSON format and transform to CSV"""
        context = {
            'ignore_capacity_check': True #Includes private datasets
        }
        search_results = get_action('package_search')(context, {'rows': 1000000})
        results = search_results['results']

        self.transform(results)

        #Load CSV columns from JSON file
        columns = self._absolute_path('columns.json')

        csv_string = losser.losser.table(results, columns, csv=True, pretty=False)

        pylons.response.headers['Content-Type'] = 'text/csv;charset=utf-8'
        pylons.response.headers['Content-Disposition'] = 'attachment; filename="data_report.csv"'
        return csv_string