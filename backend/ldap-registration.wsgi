#!/usr/bin/env python

# Add the program directory to the path
import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cgi import parse_qs, escape
from simplejson import loads, dumps
from urls import urls

def url_comparator(parts, urls):
    if parts[0] in urls:
        if isinstance(urls[parts[0]], dict):
            if len(parts) > 1:
                return url_comparator(parts[1:], urls[1:])
            else:
                return None, None
        else:
            return urls[parts[0]], parts[1:]
    else:
        return None, None

def application(environ, start_response):
    # the environment variable CONTENT_LENGTH may be empty or missing
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0

    # Build the request class
    request = Request()

    request_body = environ['wsgi.input'].read(request_body_size)
    if environ['REQUEST_METHOD'] == 'POST':
        # POST is QUERY_STRING formatted data
        request.post = parse_qs(request_body)
    elif environ['REQUEST_METHOD'] == 'PUT':
        # PUT is JSON formatted data
        request.put = loads(request_body)

    request.get = parse_qs(environ.get('QUERY_STRING'))
    request.start_response = start_response
    request.method = environ['REQUEST_METHOD']
    request.environ = environ

    # Go to the proper handler function
    url_parts = environ.get('PATH_INFO').split('/')
    if len(url_parts) < 2:
        status = '404 NOT FOUND'
        return request.response_json({'success': False, 'msg': 'Specify an item to retrieve'}, status=status)

    func, remaining_url_parts = url_comparator(url_parts[1:], urls)

    if func != None:
        request.url_parts = remaining_url_parts
        return func(request)
    else:
        status = '404 NOT FOUND'
        return request.response_json({'success': False, 'msg': 'Handler for %s not found' % environ.get('PATH_INFO')}, status=status)

class Request:
    get = {}
    post = {}
    put = {}
    start_response = None
    url_parts = []
    method = None
    environ = {}

    def response_json(self, obj, status='200 OK'):
        response_body = dumps(obj)

        response_headers = [('Content-Type', 'application/json'),
                            ('Content-Length', str(len(response_body)))]

        self.start_response(status, response_headers)

        return [response_body]



# Be a wsgi server if we run standalone
if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('localhost', 8051, application)
    httpd.serve_forever()


