import os
import re
from multiprocessing import Process

try:
  from SimpleHTTPServer import SimpleHTTPRequestHandler as Handler
  from SocketServer import TCPServer as Server
except ImportError:
  from http.server import BaseHTTPRequestHandler as Handler
  from http.server import HTTPServer as Server

import Generate_HTML
import Processing
import logging

# over write Handler class for 3 GET cases:
#	(a) web/Select
#	(b) web/start with POST json and csv
#	(c) web/results for javascript with json output
#	(d) web/assests
class Custom_Http(Handler):
    def _set_headers(self):
        self.send_response(200)
        regex = re.search(".(css|json|png)+$",self.path)
        
        if regex is None:
            self.send_header('Content-type', 'text/html')
        elif regex.group(1) =='css':
            self.send_header('Content-type', 'text/css')
        elif regex.group(1) =='data':
            self.send_header('Content-type', 'application/json')
        elif regex.group(1) =='png':
            self.send_header('Content-type', 'image/png')
        else:
            self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        regex = re.search('^/([A-Z,a-z,0-9])+', self.path)
        if regex is None:
            self.wfile.write("<html><body><h1>Error Invalid URL</h1></body></html>")
        else:
            if regex.group(0) == "/start":
                logging.info('called start')  # will not print anything
                self.wfile.write(Generate_HTML.html_LoadHistoric())
            elif regex.group(0) == "/startStream":
                print("Start Streaming Historic Data")
                Generate_HTML.start_historic(self.path);
            	self.wfile.write("<html><body><h1>Started Streaming</h1></body></html>")
            elif regex.group(0) == "/results":
                f = open("Results.html",'rb')
                self.wfile.write(f.read())
            elif regex.group(0) == "/data":
                self.wfile.write(Generate_HTML.Retrieve_Result())
            elif regex.group(0) == "/assets":
                regex_file = re.search('^/assets/([A-Z,a-z,0-9/.-]+)', self.path)
                print (regex_file.group(1))
                try:
                    f = open("./assets/" + regex_file.group(1),'rb')
                    self.wfile.write(f.read())
                except:
                    print("Failed to find File")
                    self.wfile.write("<html><body><h1>File Does not Exist</h1></body></html>")
            else:
                print regex.group(0)
                self.wfile.write("<html><body><h1>Error Invalid URL</h1></body></html>")
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        self._set_headers()
        self.wfile.write("<html><body><h1>POST!</h1></body></html>")
		
		




if __name__ == '__main__':
    # Read port selected by the cloud for our application
    PORT = int(os.getenv('PORT', 8000))

    # start Thread with actual computation 
    thread = Process(target = Processing.start, args = ())
    thread.start()
        
        
    # Change current directory to avoid exposure of control files
    os.chdir('static')

    httpd = Server(("", PORT), Custom_Http)


    try:
      print("Start serving at port %i" % PORT)
      httpd.serve_forever()
    except KeyboardInterrupt:
      pass
    httpd.server_close()
    thread.terminate()
