#!/usr/bin/python
#
#
from common import Common
import json
import urllib2
import sys
import os
import logging
import itertools
import re
from aptsources.distinfo import Template

common = Common()

global _templatesuffix
class Buildplan_helper:
    
    
    def __init__(self, resource, fields, cidblocal):
        """
           get = any idb "allhosts?"  
        """
        self.cidblocal = cidblocal
        self.idb_resource = resource
        self.fields = fields
        self.cache={}
        #setting as separate list to preserve order
        self._suffixlist = ['.dr.standby','.dr','.standby','']
        self._templatesuffix= {
                 
                    (True, 'STANDBY') : self._suffixlist[0],
                    (False, 'PRIMARY') : self._suffixlist[1],
                    (True, 'STANDBY') : self._suffixlist[2],
                    (False, 'PRIMARY') : self._suffixlist[3]
                            
                }
    
    def gen_request(self,reststring, dc, cidblocal=True, debug=False):
        """
          build request for idb
        """
        
        # Build the API URL
        dc = dc.lower()
        if cidblocal:
            # CIDB URL is slightly different, so it needs to be cut up and
            # reassembled.
            url =  "https://cidb1-0-sfm.data.sfdc.net/cidb-api/%s/1.03/" % dc    + reststring              
            url = os.popen('java -jar ' + common.cidb_jar_path + '/cidb-security-client-0.0.3.jar ' + common.cidb_jar_path + '/keyrepo "' + url + '"').read()
        else:
            url = "https://inventorydb1-0-%s.data.sfdc.net/api/1.03/" % dc + reststring

        print url
        logging.debug(url)

        # Send the request.
        r = urllib2.urlopen(url)
        # use the data.
        data = json.load(r)
        if debug:
            logging.debug(data)
            logging.debug(data['total'])
        if data['total'] == 1000:
            raise Exception('idb record limit of 1000, you may be missing records')
        print str(data['total']) + ' records returned'
        print
        return data
    
        
    def cacher(self,current_obj, arglist):
    # loop through fields from left to right caching ibased on JacksonId if they point to a json object returning if they are cached
        for arg in arglist:
            if type(current_obj[arg]) is unicode:
                current_obj = self.cache[current_obj[arg]]
            else:
                current_obj = current_obj[arg]
            self.cache[current_obj['@' + arg + 'JacksonId']] = current_obj
        
        return current_obj
        
    def check_cache(self,current_obj,argstring):
        """
            cache and return parent values or return current row values
        """
  
        arglist=argstring.split('.')

        try:
            if len(arglist) > 1:
                return self.cacher(current_obj,arglist[:-1])[arglist[-1]]
            else:    
                return current_obj[arglist[-1]]
        except:
            logging.debug (  "Field" + argstring + ' does not exist in row: ' + str(current_obj) )
            raise
        
        
    def row_test_regex(self,row,regexfilters):
        """
          test a row for regexfilters checking against corresponding idb field
          evaluate
        """
    
        retval=True
        for key in self.fields:
            idbfield = self.fields[key]
            if idbfield in regexfilters and not re.match(regexfilters[idbfield], row[key]):     
                logging.debug( 'regex ' + regexfilters[idbfield] + ' does not match ' + idbfield + ':' + row[key] )
                retval = retval and False
        
        return retval
    
    
    
    
    def apply_regexfilters(self,regexfilters,unfilteredlist):
        """
        regexfilters : dict of key value pairs containing regexes to be applied to each of the fields.values()  
        """
        results = []
        for key in regexfilters:
            assert key in self.fields.values(), "regexfilter not specified as field"
            
        for row in unfilteredlist:
            if self.row_test_regex(row,regexfilters):
                results.append( row )
            
        return results
        
        
        
    def get_uri_list(self, idbfilters):
        """
        construct list of reststrings  using dict idbfilters
        """
    
        requestlist = []
        results=[]
        fields = self.fields
        assert len(fields) > 0, "Error: No fields specified"
        assert len(idbfilters.keys()) > 0, "Error no filters specified" 
        
        #convert each to list if string assigned
        for key,val in idbfilters.items():
            idbfilters[key] = [val] if not isinstance(val,list) else val
            
        
        for key in idbfilters:
            assert (isinstance(idbfilters[key], list) and len(idbfilters[key][0]) > 0), "idbfilter " + key + " must have at least one value"
            requestlist.append([(key,val) for val in idbfilters[key] ])
            
        requestlist.append([('fields', ','.join(fields.values()))] )
      
        for clauses in itertools.product(*requestlist):
            reststring = self.idb_resource + '&'.join(['='.join(clause) for clause in clauses ])
            results.append(reststring)
    
        logging.debug( results )
        return results
        
    
    def get_hosts_from_idbquery(self,datacenters,idbfilters,regexfilters):
        """
           datacenters: tuple of 3 character datacenter ids eg : was,chi,tyo ..
           idbfilters : dict of key = valid target fieldname, value = tuple of values  
           
        """
        assert len(datacenters) > 0, "Error no datacenters specified" 
        
        results = []
        reststring_list = self.get_uri_list(idbfilters)
        for dc in datacenters:    
            for reststring in reststring_list:
                current=self.gen_request(reststring,dc)
                if current['total'] > 0:
                    for jsonresult in current['data']:
                        logging.debug( jsonresult )
                        row={}
                        row['datacenter']=dc
                        for key in self.fields:
                            row[key] = self.check_cache(jsonresult,self.fields[key])    
                            results.append(row)
                else:
                    logging.debug( 'no values for: ' + reststring )
    
     
        return self.apply_regexfilters(regexfilters, results)
    

    def set_default_fields(self,res):
        """
         apply grouping defaults majorset, minorset, datacenter, superpod, rolename taken from hostname
         this allows up to do majorset minorset grouping and can be applied to hosts where we have no idbdata
         
        """
        newres=[]
        for row in res:
            # minorset never present so put it i
            row['minorset'] = row['hostname'].split('-')[2]
            row['majorset'] = ''.join([s for s in row['hostname'].split('-')[1] if s.isdigit()])
        
        
            if 'superpod' not in row.keys():
                row['superpod'] = 'none'
            if 'datacenter' not in row.keys():
                row['datacenter'] = row['hostname'].split('-')[4]
            if 'role' not in row.keys():
                row['role'] = ''.join([s for s in row['hostname'].split('-')[1] if not s.isdigit()])
            if 'cluster' not in row.keys():
                row['cluster'] =  row['hostname'].split('-')[0] 
            
            newres.append(row)
        
        
        return newres
    
    
                               
    def get_groupeddata_old(self,res,group,node=''):
        """
          group hosts into Dict hierarchy or a flat list based on top (usually DC), middlegroup (arbitrary grouping from user and ) optionally node, usually hostname
          which pints to the 'row' dict the contents of which can be summarized
          
        """
    
        groupeddata={}
        
        top=group.pop()
    
        for row in res: 
            assert top in row.keys(), top + " needs to be in row :" + str(row.keys())
            if len(node) > 0:     
                assert node in row.keys(), node + " needs to be in row :" + str(row.keys())
                
            tg_ident=(row[top],)           
            rg_ident = ()
            for field in group:
                assert field in row.keys(), field + " needs to be in row :" + str(row.keys())
                rg_ident = rg_ident + (row[field],)
            
            
            if tg_ident not in groupeddata.keys():
                groupeddata[tg_ident]={}
            if rg_ident not in groupeddata[tg_ident].keys():
                groupeddata[tg_ident][rg_ident] = {}   
            #
            if len(node) > 0: 
                groupeddata[tg_ident][rg_ident][row[node]] = row
        return groupeddata
    
    
    def prep_idb_plan_info(self,dcs,idbfilters,regexfilters,groups,templateid):
        """
        entry point function for generating an idb based plan
        """
        
        results = self.get_hosts_from_idbquery(dcs,idbfilters,regexfilters)
                      
        results = self.set_default_fields(results)
        
        if templateid.lower()=='AUTO'.lower():
            #if AUTO group by idb template values
            groups[:0]=[['role','dr','failoverstatus']]
        
        
        groupedhosts = self.get_groupeddata(results,groups)
        
            
        writeplan = self._apply_templates(groupedhosts,templateid)
       
        
        return writeplan
      
    def _remove_missing_templates(self,writeplan):
        """
          remove those plans which are not in templates directory and warn for them
        """
        assert len(writeplan.keys())>0, "no data available to write plans"
        missingplans=[]
        for templateid in writeplan.keys():
            template_file = common.templatedir + "/" + str(templateid) + ".template"
            if not os.path.isfile(template_file ):
                print "WARNING : " + template_file + " is not in place. Corresponding hosts will be skipped"
                missingplans.append(templateid)
        
        #clean up missing plans        
        for templateid in missingplans:
            del writeplan[templateid]
        return writeplan
        
    
    def _apply_templates(self,groupedhosts,templateid):   
        """
        take a structure of idb values groupedhosts, grouped by idb template values  (role, dr, failverstatus)
        assert for idb values corresponding to template
        check for template files warning where not present
        return a structure grouped by autogenerated template or initial templateid
        
        """  
        
        writeplan={}
        
        if templateid.upper()!='AUTO':
            writeplan[templateid] = groupedhosts
        else:
            print groupedhosts.keys()
            
            for templatevals in groupedhosts.keys():
                assert templatevals[1:] in self._templatesuffix.keys(), "template idb identifer " + str(templatevals) + " not defined in in " + str(self._templatesuffix)  
                templateid= templatevals[0] + self._templatesuffix[templatevals[1:]]
                logging.debug ( 'derived templateid ' + templateid )
                writeplan[templateid] = groupedhosts[templatevals]
       
        
        self._remove_missing_templates(writeplan)
            
        return writeplan
     
        
        
    def get_groupeddata(self,res,groups):
        """
          group hosts into hierarchical dict based on arbitrary groups of valid fields
          summarizing specified fields at each level
          
        """  
        #global currentnode
        currentnode={}
        for row in res:
            currentnode=self.get_groupeddata_row(row, groups, currentnode)
        
                
                
        return currentnode 
        
    def get_groupeddata_row(self,row,groups,currentnode,groupcount=0):
        """
          recursively get nested groups per row and feed back to get_groupeddata
          
        """   
        
        if groupcount==len(groups):
            currentnode=row
        else:    
            tmp_ident = ()
        
            for field in groups[groupcount]:
                assert field in row.keys(), field + " needs to be in row :" + str(row.keys())
                tmp_ident = tmp_ident + (row[field],)
                    
            if tmp_ident not in currentnode.keys():
                currentnode[tmp_ident] = {}
            currentnode[tmp_ident] = self.get_groupeddata_row(row, groups, currentnode[tmp_ident],groupcount+1)
                
        
        return currentnode
        
                
        
       
                
            