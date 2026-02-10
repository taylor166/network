# Twilio SMS Integration Setup Guide

This guide will help you set up Twilio SMS integration for sending and receiving text messages through the networking CRM.

## Prerequisites

- A Twilio account (sign up at [twilio.com](https://www.twilio.com))
- A Twilio phone number (you'll get one when you sign up)
- Python 3.8 or higher
- The networking CRM application installed (see main README.md)

## Step 1: Create a Twilio Account

1. Go to [twilio.com](https://www.twilio.com) and sign up for a free account
2. Verify your phone number (required for trial accounts)
3. Get your Account SID and Auth Token:
   - Go to the [Twilio Console Dashboard](https://console.twilio.com/)
   - Your Account SID and Auth Token are displayed on the dashboard
   - Keep these secure - they're your API credentials

## Step 2: Get a Twilio Phone Number

1. In the Twilio Console, go to "Phone Numbers" > "Manage" > "Buy a number"
2. Choose a number (you can get a free trial number)
3. Note the phone number (e.g., `+1234567890`) - this is your `TWILIO_FROM_NUMBER`

**Note:** Trial accounts have limitations:
- Can only send SMS to verified phone numbers
- Limited number of messages
- Upgrade to a paid account for production use

## Step 3: Configure Webhook for Inbound SMS (Optional but Recommended)

To receive SMS messages, you need to configure a webhook:

1. In Twilio Console, go to "Phone Numbers" > "Manage" > "Active numbers"
2. Click on your phone number
3. Under "Messaging", find "A MESSAGE COMES IN"
4. Set the webhook URL to: `https://your-domain.com/api/messages/inbound-sms`
   - For local development, use a tool like [ngrok](https://ngrok.com/) to expose your local server
   - Example: `https://abc123.ngrok.io/api/messages/inbound-sms`
5. Set HTTP method to `POST`
6. Click "Save"

**For Local Development:**
- Use ngrok or similar tool to create a public URL
- Update the webhook URL when your ngrok URL changes
- Or test inbound SMS manually using the Twilio Console

## Step 4: Configure Environment Variables

Add the following to your `.env` file in the project root:

```env
# Twilio SMS Credentials
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890
```

Replace:
- `your_account_sid_here` with your Twilio Account SID
- `your_auth_token_here` with your Twilio Auth Token
- `+1234567890` with your Twilio phone number (include the `+` and country code)

**Important:** Never commit your `.env` file to version control. The `.env.example` file should not contain actual credentials.

## Step 5: Install Dependencies

Make sure you have installed the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `twilio` (Twilio Python SDK)

## Step 6: Test the Integration

### Send an SMS

1. Open the CRM web interface
2. Click on a contact to view details
3. Go to the "Messages" tab
4. Click "Send Text"
5. Enter your message (SMS has a 1600 character limit)
6. Click "Send Text"

**Note:** For trial accounts, you can only send to verified phone numbers. Add the recipient's phone number in Twilio Console under "Phone Numbers" > "Verified Caller IDs".

### Receive an SMS (If Webhook Configured)

1. Send a text message to your Twilio phone number
2. The message will be received via webhook
3. It will appear in the contact's Messages tab (if the phone number matches a contact)

## Troubleshooting

### "Twilio integration not configured" Error

- Check that `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_FROM_NUMBER` are set in your `.env` file
- Verify the credentials are correct (no extra spaces or quotes)
- Restart the application after updating `.env`

### "Invalid phone number format" Error

- Phone numbers must be in E.164 format: `+[country code][number]`
- Example: `+1234567890` (US number)
- Make sure the contact's phone number includes country code
- The system will try to normalize phone numbers, but it's best to store them in E.164 format

### SMS Not Sending

- Check your Twilio account balance (trial accounts have limits)
- Verify the recipient phone number is correct
- For trial accounts, make sure the recipient number is verified in Twilio Console
- Check Twilio Console logs for error messages
- Verify your `TWILIO_FROM_NUMBER` is correct and active

### Inbound SMS Not Working

- Verify the webhook URL is configured correctly in Twilio Console
- Make sure your server is accessible (use ngrok for local development)
- Check that the webhook endpoint is receiving requests (check server logs)
- Verify the phone number in the incoming message matches a contact's phone number
- Check Twilio Console > Monitor > Logs for webhook delivery status

### "Trial account" Limitations

- Trial accounts can only send to verified phone numbers
- Upgrade to a paid account to send to any phone number
- Trial accounts have message limits - check your usage in Twilio Console

## Security Notes

- Keep your `TWILIO_AUTH_TOKEN` secure and never commit it to version control
- Regularly review your Twilio usage and costs
- Set up usage alerts in Twilio Console to avoid unexpected charges
- For production, use environment-specific Twilio credentials

## Phone Number Format

The system expects phone numbers in E.164 format:
- ✅ `+1234567890` (US number)
- ✅ `+441234567890` (UK number)
- ❌ `123-456-7890` (will be normalized if possible)
- ❌ `(123) 456-7890` (will be normalized if possible)

The system will attempt to normalize phone numbers, but it's recommended to store contacts' phone numbers in E.164 format in Notion.

## Advanced Configuration

### Multiple Twilio Numbers

Currently, the system uses one Twilio phone number. To use a different number:
- Update `TWILIO_FROM_NUMBER` in your `.env` file
- Update the webhook URL in Twilio Console if needed
- Restart the application

### Custom Webhook URL

If you're running the server on a different domain:
- Update the webhook URL in Twilio Console
- Make sure the endpoint `/api/messages/inbound-sms` is accessible
- Use HTTPS in production (required by Twilio)

### Message Length Limits

- SMS messages are limited to 1600 characters (Twilio's limit)
- Longer messages will be split into multiple SMS (charges apply per segment)
- Consider using email for longer messages

## Cost Considerations

- Twilio charges per SMS sent and received
- Check Twilio pricing: https://www.twilio.com/sms/pricing
- Set up usage alerts in Twilio Console
- Monitor your usage regularly

## Next Steps

Once SMS integration is working:
- Set up email integration (see `integrations/email/SETUP.md`)
- Configure automated follow-up reminders
- Set up SMS templates for common outreach scenarios
