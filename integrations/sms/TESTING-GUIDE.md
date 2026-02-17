# Twilio SMS Testing Guide

## Testing Your SMS Integration

### Option 1: Use Your Own Phone Number (Recommended for Testing)

**For Trial Accounts:**
1. Go to [Twilio Console](https://console.twilio.com/) > "Phone Numbers" > "Verified Caller IDs"
2. Click "Add a new Caller ID"
3. Enter your phone number (the one you want to receive test SMS)
4. Twilio will send you a verification code via SMS or call
5. Enter the verification code
6. Once verified, you can send SMS to this number from your CRM

**Steps to Test:**
1. Add a contact in your CRM with your verified phone number
2. Open the contact details
3. Go to the "Messages" tab
4. Click "Send Text"
5. Enter a test message like "Testing SMS integration"
6. Click "Send Text"
7. You should receive the SMS on your phone within seconds

### Option 2: Use Twilio's Test Credentials (For Development)

Twilio provides test credentials that don't actually send SMS but validate your code:

**Test Account SID:** `ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`  
**Test Auth Token:** (found in Twilio Console > Account > API Keys & Tokens > Test Credentials)

**Note:** Test credentials don't actually send SMS - they just validate your API calls. For real testing, use Option 1.

### Option 3: Use a Second Phone Number

If you have access to another phone number:
1. Verify that number in Twilio Console
2. Use it as the recipient for testing
3. This is useful for testing the full flow without using your own number

## Troubleshooting Test Sends

### "Invalid phone number format"
- Make sure the phone number is in E.164 format: `+[country code][number]`
- Example: `+15551234567` (US number)
- The system will try to normalize, but E.164 is recommended

### "Trial account limitation"
- Trial accounts can only send to verified phone numbers
- Verify the recipient number in Twilio Console first
- Or upgrade to a paid account

### "Message not received"
- Check Twilio Console > Monitor > Logs for delivery status
- Verify the phone number is correct
- Check your Twilio account balance (trial accounts have limits)
- Make sure the recipient number is verified (for trial accounts)

### "Twilio integration not configured"
- Verify all three environment variables are set in `.env`:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_FROM_NUMBER`
- Restart the server after updating `.env`

## Verifying Success

After sending a test SMS, you should see:
1. ✅ Success message in the CRM UI
2. ✅ Message appears in the contact's Messages tab
3. ✅ SMS received on the recipient phone
4. ✅ Message SID logged in server logs
5. ✅ Message stored in the database (`data/messages.db`)

## Next Steps After Testing

Once SMS is working:
1. Test sending to different phone numbers
2. Test receiving SMS (if webhook is configured)
3. Verify messages are stored correctly
4. Check that `last_contact_date` is updated
5. Test with contacts that have different phone number formats
