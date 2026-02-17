# Twilio SMS Integration - Setup Requirements

## ✅ What's Already Built

The Twilio SMS integration is **fully implemented** and ready to use. The following components are in place:

1. **Twilio Client** (`integrations/sms/twilio_client.py`)
   - SMS sending functionality
   - Inbound SMS webhook handling
   - Phone number validation and normalization
   - Error handling

2. **API Endpoints** (`contacts/api.py`)
   - `POST /api/messages/send-sms` - Send SMS to a contact
   - `POST /api/messages/inbound-sms` - Receive SMS via Twilio webhook

3. **Frontend Integration** (`contacts/static/index.html`)
   - Send SMS modal in contact details
   - Message history display
   - SMS character limit (1600 chars)

4. **Message Storage** (`contacts/message_storage.py`)
   - Stores all SMS messages in SQLite database
   - Links messages to contacts
   - Tracks message direction (inbound/outbound)

## 🔑 What You Need to Provide

To activate the Twilio integration, you need to provide **3 pieces of information** from your Twilio account:

### 1. Twilio Account SID
- **Where to find it:** Twilio Console Dashboard (https://console.twilio.com/)
- **Format:** Starts with `AC` followed by 32 characters
- **Example (placeholder):** `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Twilio Auth Token
- **Where to find it:** Twilio Console Dashboard (same page as Account SID)
- **Format:** 32-character string
- **Example:** `your_auth_token_here_32_chars`
- **⚠️ Security:** Keep this secret! Never commit to git.

### 3. Twilio Phone Number
- **Where to find it:** Twilio Console > Phone Numbers > Manage > Active numbers
- **Format:** E.164 format with country code (e.g., `+1234567890`)
- **Example:** `+15551234567`
- **Note:** This is the number that will send SMS messages

## 📝 Setup Steps

### Step 1: Create/Login to Twilio Account

1. Go to [twilio.com](https://www.twilio.com) and sign up (or log in)
2. Verify your phone number (required for trial accounts)
3. Get a Twilio phone number:
   - Go to "Phone Numbers" > "Manage" > "Buy a number"
   - Choose a number (free trial numbers available)
   - Note the phone number in E.164 format

### Step 2: Get Your Credentials

1. Go to [Twilio Console Dashboard](https://console.twilio.com/)
2. Your **Account SID** and **Auth Token** are displayed on the dashboard
3. Copy both values

### Step 3: Add to Environment Variables

Add these three lines to your `.env` file in the project root:

```env
# Twilio SMS Credentials
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+15551234567
```

**Important:**
- Replace the example values with your actual credentials
- The phone number must include the `+` and country code
- Never commit your `.env` file to git (it's already in `.gitignore`)

### Step 4: Restart the Server

After adding the credentials, restart your server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python main.py
# or
python3 main.py
```

### Step 5: Test the Integration

1. Open the CRM in your browser: `http://localhost:8000`
2. Click on a contact that has a phone number
3. Go to the "Messages" tab
4. Click "Send Text"
5. Enter a test message
6. Click "Send Text"

**For Trial Accounts:**
- You can only send SMS to verified phone numbers
- Add recipient numbers in Twilio Console under "Phone Numbers" > "Verified Caller IDs"

## 🔔 Optional: Set Up Inbound SMS (Webhook)

To receive SMS messages, you need to configure a webhook:

1. In Twilio Console, go to "Phone Numbers" > "Manage" > "Active numbers"
2. Click on your phone number
3. Under "Messaging", find "A MESSAGE COMES IN"
4. Set the webhook URL to: `https://your-domain.com/api/messages/inbound-sms`
   - For local development, use [ngrok](https://ngrok.com/) to expose your server
   - Example: `https://abc123.ngrok.io/api/messages/inbound-sms`
5. Set HTTP method to `POST`
6. Click "Save"

**Note:** Inbound SMS will automatically be linked to contacts if the phone number matches.

## ✅ Verification Checklist

- [ ] Twilio account created
- [ ] Twilio phone number obtained
- [ ] Account SID copied
- [ ] Auth Token copied
- [ ] All three values added to `.env` file
- [ ] Server restarted
- [ ] Test SMS sent successfully

## 🆘 Troubleshooting

### "Twilio integration not configured" Error
- Check that all three environment variables are set in `.env`
- Verify no extra spaces or quotes around values
- Restart the server after updating `.env`

### "Invalid phone number format" Error
- Phone numbers must be in E.164 format: `+[country code][number]`
- Example: `+1234567890` (US number)
- The system will try to normalize, but E.164 format is recommended

### SMS Not Sending
- Check Twilio account balance (trial accounts have limits)
- Verify recipient number is correct
- For trial accounts, verify the recipient number in Twilio Console
- Check Twilio Console logs for error messages

## 📚 Additional Resources

- **Full Setup Guide:** See `integrations/sms/SETUP.md` for detailed instructions
- **Twilio Documentation:** https://www.twilio.com/docs
- **Twilio Console:** https://console.twilio.com/

## 🎯 Next Steps After Setup

Once SMS is working:
1. Test sending SMS to a contact
2. (Optional) Set up webhook for inbound SMS
3. Start using SMS for outreach and follow-ups
4. Monitor message history in the contact's Messages tab
