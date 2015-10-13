#!/usr/bin/python
"""
Linter script that checks release_runner templates for syntax errors based on Compute Deploy standards
"""
import re
import sys
import argparse
import os
import lint_checker as lc
from common import Common
common = Common()

def file_check(file):
    global _linenum
    global _pass_checks
    global _failed_checks
    global _total_lines_chk
    global _error_line
    _error_line = {}
    _linenum = 0
    _failed_checks = 0
    _pass_checks = 0
    _total_lines_chk = 0
    ignore_lines = re.compile(r'^\-.*|^\s+')
    if not os.path.exists(file):
        print "%s does not exists." % (file)
        sys.exit(1)   
    file_data = open(file).readlines()
    report.write("\n************* Template %s \n" % (args.file_name))
    for line in file_data:
        _linenum += 1
        if not ignore_lines.match(line):
            _total_lines_chk += 1
            value = cmd_check(line)
            if value != 0:
                _error_line[_linenum] = line
            _failed_checks = _failed_checks + value
    summary()

def cmd_check(line):
    cmd_type = re.compile(r'Exec:|release_runner.pl')
    cmd = cmd_type.match(line)
    cmd_check_fail = 0
    value = 0
    try:
        if cmd.group() == 'release_runner.pl':
            value = runner_cmds(line)
        elif cmd.group() == 'Exec:':
            pass
            #exec_cmds(line)
    except AttributeError:
        value += 1
        err_tracker("E", 'Unrecognized command expecting "release_runner.pl or Exec:"\n')
    cmd_check_fail = cmd_check_fail + value
    return cmd_check_fail
        
def runner_cmds(line):
    runner_cmds_fail = 0
    options_parser = re.compile(r'(-[a-zA-Z_0-9]+)(?:\s+|$)([\"\'].+[\"\']|(?!-)\S+)?')
    result = "None"
    rr_option = options_parser.finditer(line) 
    while result == "None":
        try:
            match_value = rr_option.next()
            (command, options) = match_value.groups()
            if command in lc.default_cmd:
                if options != lc.default_cmd[command]:
                    runner_cmds_fail += 1
                    err_tracker('E', "Expecting %s value for the command option %s\n" % (lc.default_cmd[command], command))
            elif command in lc.valid_cmd:
                if options == None and command in lc.require_options:
                    runner_cmds_fail += 1
                    err_tracker('E', "%s missing command parameters.  Usage: %s \"%s\"\n" % (command, command, lc.require_options[command]))
                elif command not in lc.require_options and options != None:
                    runner_cmds_fail += 1
                    err_tracker('E', "Illegal parameter \"%s\" specified after %s\n" % (options, command))
            if command not in lc.valid_cmd:
                runner_cmds_fail += 1
                err_tracker('E', "%s is not an valid command option\n" % command)
        except StopIteration:
            result = "End"
    val = syntax_checker(line)
    runner_cmds_fail = runner_cmds_fail + val
    return runner_cmds_fail

def syntax_checker(line):
    syntax_checker_fail = 0
    option_checker = re.compile(r'-forced_host|-invdb_mode')
    sudo_checker = re.compile(r'-forced_host|-c\s+sudo_cmd|-m\s+\".+\"')
    space_checker = re.compile(r'\s\s{1,3}')
    if not option_checker.search(line):
        syntax_checker_fail += 1
        err_tracker('W', "Expecting option \"-invdb_mode or -forced_host\"\n")
    if space_checker.search(line):
        syntax_checker_fail += 1
        err_tracker('E', "One or more trailing whitespaces found\n")
    return syntax_checker_fail

def err_tracker(err_code, msg):
    report.write("%s: %d: %s" % (err_code, _linenum, msg))
          

def summary():
    total_checks = 5 * _total_lines_chk
    template_score = 10.0 - ((float(5 * _failed_checks) / total_checks) * 10)
    report.write("\n\nDefinition\n")
    report.write("------------\n")
    report.write("E=Error\nW=Warning\n")
    if args.verbose:
        report.write("\nLines with errors\n")
        report.write("---------------------\n")
        for key,value in sorted(_error_line.iteritems()):
            report.write("%d: %s" % (key, value))
    report.write("\nGlobal evaluation\n")
    report.write("-----------------\n")
    report.write("Total number of Errors/Warnings: %d" % _failed_checks)
    report.write("\nYour template has been rated at %.2f/10\n" % template_score)
           
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Template syntax checker: Program to check syntax of release_runner templates.")
    parser.add_argument('-t', '--template', metavar='<Template Name>', dest='file_name', required=True)
    parser.add_argument('-v', '--verbose', help='Verbose output for errors.', action='store_true', dest='verbose')
    args = parser.parse_args()
    report = open(args.file_name + ".report", 'w')
    if os.path.isfile(args.file_name):
        file_check(args.file_name)
    elif os.path.isfile(common.templatedir + "/" + args.file_name):
        file = common.templatedir + "/" + args.file_name
        file_check(file)
    else:
        print "Cannot locate filename %s." % (args.file_name)
        sys.exit(1)
    report.close()
    with open(args.file_name + ".report", 'r') as fin:
        print fin.read()
    os.remove(args.file_name + ".report")
