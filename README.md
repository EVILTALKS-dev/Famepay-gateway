```markdown
# FamePay Payment Gateway API

> Simple Vercel-based API to verify FamePay UPI payments via Gmail IMAP.

## 🔥 Features

- ✅ Verify UPI payments using UTR number
- 🔍 Searches Gmail inbox for payment confirmation emails
- ⚡ Fast response with JSON output
- 🚀 Deploy on Vercel (serverless)
- 🔐 Secure — uses Gmail App Password
- 📦 Zero external dependencies (except requests for testing)

---

## 📦 API Endpoint

```

GET /api/{GMAIL_ID}/{GMAIL_APP_PASSWORD}/{UTR}

```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `GMAIL_ID` | `string` | Your Gmail address (e.g., `your.email@gmail.com`) |
| `GMAIL_APP_PASSWORD` | `string` | Gmail App Password (remove spaces) |
| `UTR` | `string` | UTR number to verify (e.g., `123456789012`) |

---

## 📤 Response Format

### ✅ Success — Payment Verified

```json
{
  "verified": true,
  "utr": "123456789012",
  "amount": 35.07,
  "message": "Payment verified successfully",
  "Admin": "t.me/EVILTALKS",
  "Channel": "t.me/ETOFFICIALS"
}
```

❌ Not Found

```json
{
  "verified": false,
  "utr": "123456789012",
  "message": "UTR 123456789012 not found in recent emails",
  "Admin": "t.me/EVILTALKS",
  "Channel": "t.me/ETOFFICIALS"
}
```

⚠️ Error

```json
{
  "verified": false,
  "utr": "123456789012",
  "error": "Gmail login failed — check App Password (remove spaces)",
  "Admin": "t.me/EVILTALKS",
  "Channel": "t.me/ETOFFICIALS"
}
```

---

🚀 Deploy to Vercel

Prerequisites

· Vercel Account
· Gmail App Password

Steps

1. Clone or create project folder

```bash
mkdir famepay-gateway
cd famepay-gateway
```

2. Create api/index.py — paste the main code
3. Create vercel.json (optional)

```json
{
    "functions": {
        "api/index.py": {
            "runtime": "python3.9"
        }
    },
    "routes": [
        {
            "src": "/api/(.*)",
            "dest": "/api/index.py"
        }
    ]
}
```

4. Create requirements.txt

```
requests==2.31.0
```

5. Deploy

```bash
npm install -g vercel
vercel
```

Follow the prompts — your API will be live at:

```
https://famepaygateway.vercel.app
```

---

🔥 Usage Example

cURL

```bash
curl "https://famepaygateway.vercel.app/api/your.email@gmail.com/hsthcecnesbldzp/123456789012"
```

Python

```python
import requests

url = "https://famepaygateway.vercel.app/api/your.email@gmail.com/hsthcecnesbldzp/123456789012"
response = requests.get(url)
data = response.json()

if data.get("verified"):
    print(f"✅ Payment verified! Amount: ₹{data['amount']}")
else:
    print(f"❌ {data['message']}")
```

JavaScript (Node.js)

```javascript
const response = await fetch(
    "https://famepaygateway.vercel.app/api/your.email@gmail.com/hsthcecnesbldzp/123456789012"
);
const data = await response.json();

if (data.verified) {
    console.log(`✅ Payment verified! Amount: ₹${data.amount}`);
} else {
    console.log(`❌ ${data.message}`);
}
```

---

🛠️ How It Works

1. User makes a UPI payment to your FamePay ID.
2. FamePay sends a confirmation email to your Gmail.
3. Your bot/call hits this API with Gmail credentials and UTR.
4. API connects to Gmail IMAP and searches for the UTR.
5. If found → returns verified: true with amount.
6. If not found → returns verified: false with message.

---

⚠️ Important Notes

Issue Solution
Gmail login fails Use App Password, not regular password. Remove spaces.
No emails found Check that FamePay emails are going to the same Gmail.
Rate limits Gmail IMAP has ~500 requests/hour limit.
Sensitive data Don't expose Gmail credentials in client-side code.

---

🔧 Customization

Change Admin / Channel Links

Edit these lines in api/index.py:

```python
ADMIN_LINK = "t.me/YOUR_ADMIN"
CHANNEL_LINK = "t.me/YOUR_CHANNEL"
```

Change Search Days

```python
result = check_gmail_for_utr(gmail_user, gmail_pass, utr_number, search_days=7)
```

Change 7 to any number of days.

---

📁 Project Structure

```
famepay-gateway/
├── api/
│   └── index.py          # Main API handler
├── vercel.json           # Vercel config (optional)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

🔥 Live Demo

Try it yourself (replace with your credentials):

```
https://famepaygateway.vercel.app/api/your.email@gmail.com/hsthcecnesbldzp/123456789012
```

---

📝 License

MIT — Use freely for educational and commercial purposes.

---

👨‍💻 Developer

Built by @EVILTALKS
Channel: @ETOFFICIALS

---

⭐ Support

If you find this useful, star the repo and share with your network!

---

Made with ❤️ by EVILTALKS
