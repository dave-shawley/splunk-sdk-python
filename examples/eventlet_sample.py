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

# A sample that demonstrates a custom HTTP handler for the Splunk service,
# as well as showing how you could use the Splunk Python SDK with coroutine
# based systems like Eventlet.

#### Main Code

import sys, datetime
import urllib
from time import sleep

import splunk
from utils import parse, error

# Placeholder for a specific implementation of `urllib2`,
# to be defined depending on whether or not we are running
# this sample in async or sync mode.
urllib2 = None

def _spliturl(url):
    scheme, part = url.split(':', 1)
    host, path = urllib.splithost(part)
    host, port = urllib.splitnport(host, 80)
    return scheme, host, port, path

def main(argv):
    global urllib2

    # Parse the command line args.
    opts = parse(argv, {}, ".splunkrc")

    # We have to see if we got either the "sync" or
    # "async" command line arguments.
    allowed_args = ["sync", "async"]
    if len(opts.args) == 0 or opts.args[0] not in allowed_args:
        error("Must supply either of: %s" % allowed_args, 2)

    # Note whether or not we are async.
    is_async = opts.args[0] == "async"

    # If we're async, we'' import `eventlet` and `eventlet`'s version
    # of `urllib2`. Otherwise, import the stdlib version of `urllib2`.
    #
    # The reason for the funky import syntax is that Python imports
    # are scoped to functions, and we need to make it global. 
    # In a real application, you would only import one of these.
    if is_async:
        urllib2 = __import__('eventlet.green', globals(), locals(), 
                            ['urllib2'], -1).urllib2
    else:
        urllib2 = __import__("urllib2", globals(), locals(), [], -1)


    # Create and store the `urllib2` HTTP implementation.
    http = Urllib2Http()
    opts.kwargs["http"] = http

    # Create the service and log in.
    service = splunk.client.Service(**opts.kwargs)
    service.login()

    # Record the current time at the start of the
    # "benchmark".
    oldtime = datetime.datetime.now()

    def do_search(query):
        # Create a search job for the query.
        job = service.jobs.create(query, exec_mode="blocking")

        # In the async case, eventlet will "relinquish" the coroutine
        # worker, and let others go through. In the sync case, we will
        # block the entire thread waiting for the request to complete.
        return job.results()

    # We specify many queries to get show the advantages
    # of paralleism.
    queries = [
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
        'search * | head 100',
    ]

    # Check if we are async or not, and execute all the
    # specified queries.
    if is_async:
        import eventlet

        # Create an `eventlet` pool of workers.
        pool = eventlet.GreenPool(16)

        # If we are async, we use our worker pool to farm
        # out all the queries. We just pass, as we don't
        # actually care about the result.
        for results in pool.imap(do_search, queries):
            pass
    else:
        # If we are sync, then we just execute the queries one by one,
        # and we can also ignore the result.
        for query in queries:
            do_search(query)
    
    # Record the current time at the end of the benchmark,
    # and print the delta elapsed time.
    newtime = datetime.datetime.now()
    print "Elapsed Time: %s" % (newtime - oldtime)
    

##### Custom `urllib2`-based HTTP handler

class Urllib2Http(splunk.binding.HttpBase):
    def request(self, url, message, **kwargs):
        # Add ssl/timeout/proxy information.
        kwargs = self._add_info(**kwargs)
        timeout = kwargs['timeout'] if kwargs.has_key('timeout') else None

        # Split the URL into constituent components.
        scheme, host, port, path = _spliturl(url)
        body = message.get("body", "")

        # Setup the default headers.
        head = { 
            "Content-Length": str(len(body)),
            "Host": host,
            "User-Agent": "http.py/1.0",
            "Accept": "*/*",
        }

        # Add in the passed in headers.
        for key, value in message["headers"]: 
            head[key] = value

        # Note the HTTP method we're using, defaulting
        # to `GET`.
        method = message.get("method", "GET")

        handlers = []

        # Check if we're going to be using a proxy.
        if (self.proxy):
            # If we are going to be using a proxy, then we setup
            # an `urllib2.ProxyHandler` with the passed in 
            # proxy arguments.
            proxy = "%s:%s" % self.proxy
            proxy_handler = urllib2.ProxyHandler({"http": proxy, "https": proxy})
            handlers.append(proxy_handler)
        
        opener = urllib2.build_opener(*handlers)

        # Unfortunately, we need to use the hack of 
        # "overriding" `request.get_method` to specify
        # a method other than `GET` or `POST`.
        request = urllib2.Request(url, body, head)
        request.get_method = lambda: method

        # Make the request and get the resposne
        response = None
        try:
            response = opener.open(request)
        except Exception as e:
            response = e

        # Normalize the response to something the SDK expects, and 
        # return it.
        response = splunk.binding.HttpBase.build_response(
            response.code, 
            response.msg,
            dict(response.headers),
            response)

        return response

if __name__ == "__main__":
    main(sys.argv[1:])

