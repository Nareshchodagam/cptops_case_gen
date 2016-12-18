# CPT Case Generation

# Introduction

This repo contains code used by CPT to create implementation plans based of role templates (templates dir) using build_plan.py. This repo also
contains scripts to interact with GUS to create Changes, Incidents or User Stories.

# Summary of Code

- build_plan.py - Creates implementation plans.
- gus_cases.py - Creates GUS changes or incidents.
- gus\_cases\_vault.py - Creates GUS changes or Incidents for those using the Secret Services keys.
- gen\_podlist.py - Builds hostlists files used to use with gen_cases.py.
- close\_gus\_cases.py - Interacts with GUS to change the status of GUS cases. 
- gen\_cases.py - Outputs command strings for  build\_plan.py and gus\_cases.py. 

# Directory layout

- docs - Contains additional documentation and sample commands for above code. 
- hostlists - Contains hostlist files used by gen_cases.py.
- templates - Contains all the templates used by build_plan.py. 
- modules - Contains modules used by internal code. 
- GUS - Submodule for cptops\_gus\_base libraries. 
- idbhost - Submodule for cptops\_idbhost module. Used by build\_plan.py.

# Installation
# Setup (Long way)
- Clone repos. 

	> git clone -b master --recursive git@git.soma.salesforce.com:CPT/cptops_case_gen cptops_case_gen
	> git clone -b master git@git.soma.salesforce.com:CPT/cptops_gus_base cptops_gus_base
	
- Install GUS libraries and add idbhost to pythonpath. 

	> cd cptops_gus_base ; python setup.py install
	> export PYTHONPATH:<dir_location>/cptops_case_gen/idbhost

- Create creds.config or vaultscreds.config file. Follow these [instructions](https://git.soma.salesforce.com/CPT/cptops_gus_base)


# Set (short way)

Use the CPTIAB docker image [here](https://git.soma.salesforce.com/CPT/cptops_cptiab).


# Docs and Examples. 

[gus_case](docs/gus_creation.md)

[build_plan](docs/build_plan_README.md)



	
	

	


