#!/usr/bin/env python3
"""g_oauth_capture.py — listens on 127.0.0.1:8765, catches the OAuth code, saves it, serves a "done" page.
Proven recipe from the 9/14 OAuth restore (skill google-oauth-pkce)."""
import http.server, urllib.parse, json, os, threading

CODE_FILE = '/tmp/g_oauth_code.txt'

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if 'code' in params:
            code = params['code'][0]
            open(CODE_FILE, 'w').write(code)
            body = ('<h1>Code captured - you can close this tab and go tell Zordon!</h1>'
                    '<p>Copy this URL if asked: <code>' + self.path + '</code></p>')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
            print('CODE CAPTURED: ' + code[:20] + '...')
            threading.Thread(target=self.server.shutdown).start()
        elif 'error' in params:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(('<h1>OAuth error: ' + params['error'][0] + '</h1>').encode())
            print('ERROR:', params)
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Waiting for Google redirect...')
    def log_message(self, *a): pass

if __name__ == '__main__':
    srv = http.server.HTTPServer(('127.0.0.1', 8765), Handler)
    print('Listening on 127.0.0.1:8765 (10 min timeout)...')
    srv.timeout = 600
    srv.serve_forever()
    print('done - saved to', CODE_FILE)