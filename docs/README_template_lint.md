##Template_lint.py 

_This script checks for syntax errors in CPT templates. Below are a list of checks._ 

	- Trailing whitespaces
	- Check for valid release_runner commands. 
	- Check expected options for certain release_runner commands. Example -superpod v_SUPERPOD
	- Checks that remote commands are enclosed in double quotes.
	- Checks that release runner option "sudo_cmd"  has all the required options.
	- Ignores empty lines and lines with leading hyphens. 
	- Checks if lines begin with valid command either Exec: or release_runner.pl
	
_Usage: template_lint.py -t \<template_name\>_
```
	************* Template search.template
	E: 1: Unrecognized command expecting "release_runner.pl or Exec:"

	Global evaluation
	-----------------
	Total number of Errors/Warnings: 1
	Your template has been rated at 9.33/10