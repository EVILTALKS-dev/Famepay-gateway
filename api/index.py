from http.server import BaseHTTPRequestHandler
import imaplib
import email
import re
import json
from email.policy import default
from urllib.parse import unquote
import time

ADMIN_LINK = "t.me/EVILTALKS"
CHANNEL_LINK = "t.me/ETOFFICIALS"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        start = time.time()
        path = unquote(self.path)
        parts = path.strip('/').split('/')
        
        if len(parts) < 4:
            self._send({"error": "Invalid URL"}, 400)
            return
        
        gmail_user = parts[1]
        gmail_pass = parts[2].replace(' ', '')
        utr = parts[3].upper()
        
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_pass)
            mail.select("inbox")
            
            # ── ONLY LAST 100 EMAILS ──
            status, data = mail.search(None, "ALL")
            if status != "OK" or not data[0]:
                self._send({"verified": False, "message": "No emails"}, 200)
                return
            
            ids = data[0].split()[-100:]  # Fastest!
            
            for eid in reversed(ids):
                _, msg_data = mail.fetch(eid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw, policy=default)
                body = self._get_body(msg)
                
                if utr in body.upper():
                    amount = self._extract_amount(body)
                    mail.logout()
                    self._send({
                        "verified": True,
                        "utr": utr,
                        "amount": amount,
                        "message": "Payment verified",
                        "Admin": ADMIN_LINK,
                        "Channel": CHANNEL_LINK,
                        "time": round(time.time() - start, 2)
                    }, 200)
                    return
            
            mail.logout()
            self._send({
                "verified": False,
                "utr": utr,
                "message": "UTR not found in last 100 emails",
                "Admin": ADMIN_LINK,
                "Channel": CHANNEL_LINK,
                "time": round(time.time() - start, 2)
            }, 200)
            
        except Exception as e:
            self._send({
                "verified": False,
                "utr": utr,
                "error": str(e),
                "Admin": ADMIN_LINK,
                "Channel": CHANNEL_LINK
            }, 200)
    
    def _send(self, data, code):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def _get_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() in ("text/plain", "text/html"):
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                pass
        return body
    
    def _extract_amount(self, text):
        match = re.search(r"₹\s*(\d+\.?\d*)", text)
        return float(match.group(1)) if match else None
