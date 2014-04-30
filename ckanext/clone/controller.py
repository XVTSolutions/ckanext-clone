
import sys
import os
import datetime
from operator import itemgetter

import pylons
import ckan

import ckan.lib.helpers as h
import ckan.plugins as plugins
from ckan.lib.base import BaseController
from ckan.lib.helpers import dataset_link, dataset_display_name
from ckan.lib.helpers import flash_error, flash_success, flash_notice
from ckan.logic.validators import package_name_exists
from ckan.logic.converters import convert_package_name_or_id_to_id as convert_to_id
from ckanext.review.model import get_package_review, add_package_review, update_package_review

class CloneController(BaseController):
    """
    ckanext-clone controller
    """

    def bad_url(self):
        flash_notice('please form URL in this format: http://<your_website>/clone/<dataset_name>')
        #return plugins.toolkit.render('bad_url.html')
        return plugins.toolkit.render('index.html')

    def index(self, id):
        
        context = {
                   'model': ckan.model,
                   'session': ckan.model.Session,
                   'user': plugins.toolkit.c.user or plugins.toolkit.c.author,
                   'auth_user_obj': plugins.toolkit.c.userobj,
                   }
        data_dict = {'id': id}
        
        if ckan.plugins.toolkit.request.method == 'POST':
            #clone dataset and redirect to edit screen
            
            try:
                plugins.toolkit.check_access('package_create', context)
                #plugins.toolkit.check_access('package_update', context, data_dict)
            except plugins.toolkit.NotAuthorized:
                plugins.toolkit.abort(401, plugins.toolkit._('Unauthorized to clone this package'))
                
            #get current package...
            pkg_dict = plugins.toolkit.get_action('package_show')(None, data_dict)
            
            #update necessary fields
            title = ckan.plugins.toolkit.request.params.getone('title')
            name = ckan.plugins.toolkit.request.params.getone('name')
            dt = datetime.datetime.now()
            pkg_dict['title'] = title
            pkg_dict['name'] = name
            pkg_dict['metadata_created'] = dt
            pkg_dict['metadata_modified'] = dt
            original_id = pkg_dict['id'];

            del pkg_dict['id']
            del pkg_dict['revision_id']
            del pkg_dict['revision_timestamp']
            
#             if pkg_dict['type'] == 'dataset-suspended':
#                 pkg_dict['type'] = 'dataset'
#                 if 'suspend_reason' in pkg_dict:
#                     del pkg_dict['suspend_reason'] 
                
#             if 'extras' in pkg_dict:
#                 extras = [kvp for kvp in pkg_dict['extras'] if not kvp['value'] == '']
#                 if extras :
#                     pkg_dict['extras'] = extras 
#                 else:
#                     del pkg_dict['extras']
                
                                      
            #create a new one based on existing one...
            try:
                pkg_dict_new = plugins.toolkit.get_action('package_create')(context, pkg_dict)
                #if package already has a review date set, return it...
                if pkg_dict.get('next_review_date'):
                    package_review = get_package_review(ckan.model.Session, pkg_dict_new['id'])
                    if package_review:
                        package_review.next_review_date = pkg_dict.get('next_review_date')
                        update_package_review(context['session'], package_review)
                    else:
                        add_package_review(context['session'], pkg_dict_new['id'], pkg_dict.get('next_review_date'))
            except plugins.toolkit.ValidationError as ve:
                plugins.toolkit.c.pkg_dict = plugins.toolkit.get_action('package_show')(context, data_dict)
                plugins.toolkit.c.pkg = context['package']
                plugins.toolkit.c.resources_json = h.json.dumps(plugins.toolkit.c.pkg_dict.get('resources', []))
                
                vars = {
                    'errors': ve.error_dict,
                    'data': { 
                             'title' : title,
                             'name': name
                             }
                    }
    
                return plugins.toolkit.render("index2.html", extra_vars = vars)
            
            ckan.plugins.toolkit.redirect_to(controller="package", action="edit", id=pkg_dict_new['id'])
        else :
       
            try:
                plugins.toolkit.c.pkg_dict = plugins.toolkit.get_action('package_show')(context, data_dict)
                plugins.toolkit.c.pkg = context['package']
                plugins.toolkit.c.resources_json = h.json.dumps(plugins.toolkit.c.pkg_dict.get('resources', []))
            except plugins.toolkit.ObjectNotFound:
                plugins.toolkit.abort(404, plugins.toolkit._('Dataset not found'))
            except plugins.toolkit.NotAuthorized:
                plugins.toolkit.abort(401, plugins.toolkit._('Unauthorized to read package %s') % id)
                
            vars = {
                    'errors': {},
                    'data': { 
                             'title' : '',#plugins.toolkit._('Clone of {dataset}').format(dataset=plugins.toolkit.c.pkg_dict['title'])',
                             'name': ''
                             }
                    }
    
            return plugins.toolkit.render("index2.html", extra_vars = vars)
