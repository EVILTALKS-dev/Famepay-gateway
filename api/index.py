from http.server import BaseHTTPRequestHandler
import imaplib
import email
import re
import json
from email.policy import default
from urllib.parse import unquote
import time

# ── CONFIG ──────────────────────────────────────────────
ADMIN_LINK = "t.me/EVILTALKS"
CHANNEL_LINK = "t.me/ETOFFICIALS"

class handler(BaseHTTPRequestHandler):
    """
    Vercel Serverless Function Handler
    GET /api/{GMAIL_ID}/{GMAIL_PASSWORD}/{UTR}
    """
    
    def do_GET(self):
        start_time = time.time()
        
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
        result = self._fast_check_gmail(gmail_user, gmail_pass, utr_number)
        
        # ── Add Admin & Channel ──────────────────────────
        result["Admin"] = ADMIN_LINK
        result["Channel"] = CHANNEL_LINK
        result["time_taken_sec"] = round(time.time() - start_time, 2)
        
        self._send_json(result, 200)
    
    def _send_json(self, data, status_code):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def _fast_check_gmail(self, gmail_user, gmail_pass, utr_number):
        """
        Fastest possible Gmail search:
        1. First search recent 500 emails (quick hit)
        2. If not found, search ALL (but optimized)
        """
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_pass)
            mail.select("inbox")
            
            # ── STEP 1: Quick search (last 500 emails) ──
            status, data = mail.search(None, "ALL")
            if status != "OK" or not data[0]:
                mail.logout()
                return {
                    "verified": False,
                    "utr": utr_number,
                    "message": "No emails found"
                }
            
            email_ids = data[0].split()
            total = len(email_ids)
            
            # Search last 500 first (fastest)
            batch_size = 500
            start_idx = max(0, total - batch_size)
            recent_ids = email_ids[start_idx:]
            
            # Check recent emails
            result = self._search_in_ids(mail, recent_ids, utr_number, "recent")
            if result:
                mail.logout()
                return result
            
            # ── STEP 2: If not found, search remaining ──
            if total > batch_size:
                older_ids = email_ids[:start_idx]
                # Batch process older emails (500 per batch)
                for i in range(0, len(older_ids), batch_size):
                    batch = older_ids[i:i+batch_size]
                    result = self._search_in_ids(mail, batch, utr_number, "older")
                    if result:
                        mail.logout()
                        return result
            
            mail.logout()
            return {
                "verified": False,
                "utr": utr_number,
                "message": f"UTR {utr_number} not found in any email"
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
    
    def _search_in_ids(self, mail, ids, utr_number, label):
        """Search UTR in a batch of email IDs"""
        for eid in reversed(ids):  # latest first within batch
            try:
                status, msg_data = mail.fetch(eid, "(RFC822)")
                if status != "OK" or not msg_data or not msg_data[0]:
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email, policy=default)
                
                # Get body fast
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ("text/plain", "text/html"):
                            try:
                                body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                # Early break if found
                                if utr_number in body.upper():
                                    break
                            except Exception:
                                pass
                else:
                    try:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                
                # Check UTR
                if utr_number in body.upper():
                    amount = self._extract_amount(body)
                    return {
                        "verified": True,
                        "utr": utr_number,
                        "amount": amount,
                        "message": f"Payment verified successfully ({label})"
                    }
            except Exception:
                continue
        
        return None
    
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
