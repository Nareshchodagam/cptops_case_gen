Computedeploy RPM creation guide. 
====================================

The current rpm is being created using fpm (effing package management). Documentation regarding 
the software can be found here https://github.com/jordansissel/fpm. 

FPM doesnt work well on the MacOS due to the requirement of rpm-build to be installed. 

Future documentation will have instructions for both fpm and rpm-build.

Creating RPM using FPM
-----------------------
Prerequisite
VirtualBox 

Puppetdev vagrant server - https://git.soma.salesforce.com/isd/piab/wiki/Puppet-Development-VM

FPM software installed. 
	
	Steps:
		- Clone the PIAB repository https://git.soma.salesforce.com/isd/piab/wiki/Puppet-Development-VM
		- Edit the ~/git/piab/Vagrantfile with the below line. This will sync you home directory to the VM. 
			dev.vm.synced_folder  "/Users/mgaddy/git",   "/git", :mount_options => ["uid=#{uid}","gid=#{uid}"], create: true
		- Start the Puppetdev vm 
			vagrant up puppetdev
			vagrant ssh puppetdev
		- Execute the creation script within the puppetdev vm. Script will clone repo, copy directories and create rpm. 
			/git/case_gen/rpm/fpm_create.sh -v MM_DD 
		
		- Once completed you can test the rpm within the VM and even commit the new rpm to GIT.
		
		
			
		

