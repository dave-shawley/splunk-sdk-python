#!/usr/bin/env python
#
# Copyright 2011 Splunk, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"): you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A command line utility for interacting with Splunk inputs."""

from pprint import pprint # UNDONE

import sys
from urlparse import urlparse

import splunk
from splunk.binding import HTTPError
from splunk.client import connect
from splunk.data import load

from utils import error, parse

def check_status(response, *args):
    if response.status not in args:
        raise HTTPError(response.status, response.reason)

def main():
    opts = parse(sys.argv[1:], {}, ".splunkrc")
    service = connect(**opts.kwargs)

    inputs = service.confs['inputs']
    for input in inputs:
        print "[%s]" % input.name
        entity = input.read()
        for k, v in entity.iteritems():
            print "    %s: %s" % (k, v)
        print
        
if __name__ == "__main__":
    main()


