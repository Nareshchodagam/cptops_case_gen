# CPTOPS GUS BASE

_Pre-reqs_

If your using your personal credentials you will need to create the creds.config for GUS API access.

	Login to ops-sysmgt1-1-sfm.ops.sfdc.net and execute the following. Copy the output file 
	to the bin directory of case_gen
		
			svn co https://vc-commit/subversion/tools/automation/scripts/sr/skyGus Gus
			python Gus/creds_setup.py
		
	Syntax of file should be as follows.
 	---------------------------------------------------------------------
 	
			[GUS]
			username = 
			client_secret = 
			client_id =
			api_ver = v29.0
			
			[LOGIN]
			oauthURL = https://gus.salesforce.com/services/oauth2/token
			
If you are using keys from Vaultczar you will need to create the vaultscreds.config file. Place
this file in your bin directory of case_gen. The syntax is below. 

			[GUS]
			api_ver = v29.0
			
			[Session]
			savedsession = savedsession
			[LOGIN]
			oauthURL = https://gus.salesforce.com/services/oauth2/token
			
			[VAULT]
			keydir = {Directory locations of your keys}
			vault = cpt-ops
			servera = https://ops-vaultczar1-1-crz.ops.sfdc.net
			serverb = https://ops-vaultczar2-1-crz.ops.sfdc.net
			port = 8443
		
Follow the below instructions to obtain your keys.
 
[How to obtain keys from Vaultczar](https://sites.google.com/a/salesforce.com/security/services/secrets-service/downloading-secrets-service-keys)

_Using gus_cases.py_

Gus cases creation uses two json files to create the details of a case. 

_details_example.json_

This template is responsible for the overall creation of the case within GUS. You can modify this template with details exclusive to the type of case
you wanting to create. 


_implementation_example.json_

This template is responsible for the implementation planner portion of the case. You can modify this template with details on how all the implementation steps
created for a given case should contain. 


_Example of using gus_cases.py_

	Usage:
	
	    This script provides a few different functions:
	    - create a new change case
	    - attach a file to a case
	    - update case comments
	    - create a new incident record
	
	    Creating a new change case:
	    gus_cases.py -T change -f file with change details -i implan -s "subject to add" -k json for the change
	
	    Example:
	    gus_cases.py -T change -f templates/oracle-patch.json -i output/plan_implementation.txt
	            -s "CHI Oracle : shared-nfs SP3 shared-nfs3{2|3}-{1|2}"
	            -k templates/shared-nfs-planer.json -l shared-nfs-sp3.txt
	
	
	Options:
	  -h, --help            show this help message and exit
	  -c CASEID, --case=CASEID
	                        The caseId of the case to attach the file
	  -f FILENAME, --filename=FILENAME
	                        The name of the file to attach
	  -l HOSTLIST, --hostlist=HOSTLIST
	                        The hostlist for the change
	  -L, --logicalHost     Create Logical host connectors
	  -V VPLAN, --vplan=VPLAN
	                        The verification plan for the change
	  -i IPLAN, --iplan=IPLAN
	                        The implementation plan for the change
	  -k IMPLANNER, --implanner=IMPLANNER
	                        The implementation planner json for the change
	  -p FILEPATH, --filepath=FILEPATH
	                        The path to the file to attach
	  -s SUBJECT, --subject=SUBJECT
	                        The subject of the case
	  -r ROLE, --role=ROLE  The host role of the case
	  -d DESC, --description=DESC
	                        The description of the case
	  -T CASETYPE, --casetype=CASETYPE
	                        The type of the case
	  -S STATUS, --status=STATUS
	                        The status of the case
	  -D DC, --datacenter=DC
	                        The data center of the case
	  -P PRIORITY, --priority=PRIORITY
	                        The priority of the case : Sev[1..4]
	  -C CATEGORY, --category=CATEGORY
	                        The category of the case
	  -b SUBCATEGORY, --subcategory=SUBCATEGORY
	                        The subcategory of the case
	  -A, --submit          Submit the case for approval
	  --inst=INST           List of comma separated instances
	  --infra=INFRA         Infrastructure type
	  -n, --new             Create a new case. Required args :
	                        Category, SubCategory, Subject, Description, DC,
	                        Status and Prioriry.
	                        -n -C Systems -b SubCategory Hardware -s Subject 'DNS
	                        issue 3' -d 'Mail is foobar'd, DSET Attached.' -D ASG
	                        -S New -P Sev3
	  -a, --attach          Attach a file to a case
	  -t COMMENT, --comment=COMMENT
	                        text to add to a case comment
	  -y, --yaml            patch details via yaml file
	  -u, --update          Required if you want to update a case
	  -v                    verbosity



