from http.server import BaseHTTPRequestHandler
import imaplib
import email
import re
import json
from datetime import datetime, timedelta
from email.policy import default
from urllib.parse import unquote

# ── CONFIG ──────────────────────────────────────────────
ADMIN_LINK = "t.me/EVILTALKS"
CHANNEL_LINK = "t.me/ETOFFICIALS"

class handler(BaseHTTPRequestHandler):
    """
    Vercel Serverless Function Handler
    GET /api/{GMAIL_ID}/{GMAIL_PASSWORD}/{UTR}
    """
    
    def do_GET(self):
        # ── Parse path ──────────────────────────────────
        path = unquote(self.path)
        parts = path.strip('/').split('/')
        
        # Expected: ["api", "GMAIL_ID", "GMAIL_PASSWORD", "UTR"]
        if len(parts) < 4:
            self._send_json({
                "error": "Invalid URL. Use: /api/GMAIL_ID/GMAIL_PASSWORD/UTR",
                "Admin": ADMIN_LINK,
                "Channel": CHANNEL_LINK
            }, 400)
            return
        
        gmail_user = parts[1]
        gmail_pass = parts[2].replace(' ', '')  # remove spaces
        utr_number = parts[3].upper()
        
        # ── Validate ─────────────────────────────────────
        if not gmail_user or not gmail_pass or not utr_number:
            self._send_json({
                "error": "Missing parameters. Format: /api/GMAIL_ID/GMAIL_PASSWORD/UTR",
                "Admin": ADMIN_LINK,
                "Channel": CHANNEL_LINK
            }, 400)
            return
        
        # ── Check Gmail ──────────────────────────────────
        result = self._check_gmail_for_utr(gmail_user, gmail_pass, utr_number)
        
        # ── Add Admin & Channel ──────────────────────────
        result["Admin"] = ADMIN_LINK
        result["Channel"] = CHANNEL_LINK
        
        self._send_json(result, 200)
    
    def _send_json(self, data, status_code):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def _check_gmail_for_utr(self, gmail_user, gmail_pass, utr_number, search_days=7):
        """Search Gmail for emails containing a specific UTR"""
        try:
            # ── Connect to Gmail IMAP ────────────────────
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_pass)
            mail.select("inbox")
            
            # ── Search emails from last N days ────────────
            since_date = (datetime.now() - timedelta(days=search_days)).strftime("%d-%b-%Y")
            search_criteria = f'(SINCE "{since_date}")'
            
            status, data = mail.search(None, search_criteria)
            if status != "OK" or not data[0]:
                mail.logout()
                return {
                    "verified": False,
                    "utr": utr_number,
                    "message": f"No emails found in last {search_days} days"
                }
            
            email_ids = data[0].split()
            
            # ── Search in reverse (latest first) ──────────
            for eid in reversed(email_ids[-50:]):
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK":
                    continue
                
                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email, policy=default)
                
                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ("text/plain", "text/html"):
                            try:
                                body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            except Exception:
                                pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                
                # ── Search UTR in email ──────────────────
                if utr_number in body.upper():
                    amount = self._extract_amount(body)
                    mail.logout()
                    return {
                        "verified": True,
                        "utr": utr_number,
                        "amount": amount,
                        "message": "Payment verified successfully"
                    }
            
            mail.logout()
            return {
                "verified": False,
                "utr": utr_number,
                "message": f"UTR {utr_number} not found in recent emails"
            }
        
        except imaplib.IMAP4.error as e:
            error_msg = str(e).lower()
            if "invalid credentials" in error_msg or "authentication" in error_msg:
                return {
                    "verified": False,
                    "utr": utr_number,
                    "error": "Gmail login failed — check App Password (remove spaces)"
                }
            return {
                "verified": False,
                "utr": utr_number,
                "error": f"IMAP error: {str(e)}"
            }
        except Exception as e:
            return {
                "verified": False,
                "utr": utr_number,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def _extract_amount(self, text):
        """Extract INR amount from email body"""
        patterns = [
            r"₹\s*(\d+\.?\d*)",
            r"Rs\.?\s*(\d+\.?\d*)",
            r"INR\s*(\d+\.?\d*)",
            r"amount.*?(\d+\.?\d*)",
            r"credited.*?(\d+\.?\d*)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except Exception:
                    pass
        return None
