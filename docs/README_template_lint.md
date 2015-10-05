##Template_lint.py 

_This script checks for syntax errors in CPT templates. Below are a list of checks. 

	- Trailing whitespaces
	- Check for valid release_runner commands. 
	- Check expected options for certain release_runner commands. Example -superpod v_SUPERPOD
	- Checks that remote commands are enclosed in double quotes.
	- Checks that release runner option "sudo_cmd"  has all the required options. 
	