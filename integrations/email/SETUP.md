# Gmail Integration Setup Guide

This guide will help you set up Gmail API integration for sending and receiving emails through the networking CRM.

## Prerequisites

- A Google account with Gmail
- Python 3.8 or higher
- The networking CRM application installed (see main README.md)

## Step 1: Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen:
     - Choose "External" (unless you have a Google Workspace)
     - Fill in the required fields (App name, User support email, Developer contact)
     - Add scopes: `https://www.googleapis.com/auth/gmail.send` and `https://www.googleapis.com/auth/gmail.readonly`
     - Add test users (your email address) if in testing mode
   - Application type: Choose "Desktop app" (recommended) or "Web application"
   - Name: "Networking CRM"
   - **IMPORTANT - Authorized redirect URIs:** Add `http://localhost:8080/` (exact match required)
     - For Desktop app type: Add `http://localhost:8080/` to the "Authorized redirect URIs" field
     - For Web application type: Add `http://localhost:8080/` to the "Authorized redirect URIs" field
   - Click "Create"

5. Download the credentials:
   - Click the download icon next to your OAuth client
   - Save the JSON file (you'll need the `client_id` and `client_secret` from it)

## Step 2: Configure Environment Variables

Add the following to your `.env` file in the project root:

```env
# Gmail OAuth Credentials
GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8080/
```

**Note:** The redirect URI must match exactly what you registered in Google Cloud Console. The default is `http://localhost:8080/`.

**Important:** Never commit your `.env` file to version control. The `.env.example` file should not contain actual credentials.

## Step 3: Install Dependencies

Make sure you have installed the required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`

## Step 4: Authenticate with Gmail

1. Start the application:
   ```bash
   python main.py
   ```

2. The first time you try to send an email or sync messages, the application will:
   - Open a browser window for Google OAuth authentication
   - Ask you to sign in with your Google account
   - Request permission to send emails and read your Gmail
   - Save the authentication token to `integrations/email/token.json`

3. After authentication, you won't need to authenticate again unless the token expires or is revoked.

## Step 5: Test the Integration

### Send an Email

1. Open the CRM web interface
2. Click on a contact to view details
3. Go to the "Messages" tab
4. Click "Send Email"
5. Fill in the subject and body
6. Click "Send Email"

### Sync Incoming Emails

1. In the contact's Messages tab, click "Sync Email"
2. The system will fetch recent emails from Gmail
3. Messages will be matched to contacts by email address
4. New messages will appear in the Messages tab

## Troubleshooting

### "Gmail integration not configured" Error

- Check that `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` are set in your `.env` file
- Verify the credentials are correct (no extra spaces or quotes)
- Restart the application after updating `.env`

### OAuth Authentication Fails / "redirect_uri_mismatch" Error

- **Most common issue:** The redirect URI in Google Cloud Console doesn't match what the app is using
- **Solution:** 
  1. Go to Google Cloud Console > APIs & Services > Credentials
  2. Click on your OAuth 2.0 Client ID
  3. Under "Authorized redirect URIs", make sure `http://localhost:8080/` is listed (exact match required)
  4. If using a different port, update both:
     - The redirect URI in Google Cloud Console
     - The `GMAIL_REDIRECT_URI` in your `.env` file
- Make sure you've enabled the Gmail API in Google Cloud Console
- Check that your OAuth consent screen is configured (especially for external users)
- If in testing mode, make sure your email is added as a test user
- The redirect URI must match exactly (including trailing slash): `http://localhost:8080/`

### "Token expired" or Authentication Required Again

- Delete `integrations/email/token.json`
- Restart the application and authenticate again
- If the issue persists, check that your OAuth credentials are still valid in Google Cloud Console

### Emails Not Syncing

- Make sure you've clicked "Sync Email" button
- Check that incoming emails have matching email addresses in your contacts
- Verify the Gmail API is enabled and you have the correct scopes
- Check server logs for error messages

### Permission Denied Errors

- Make sure you granted all requested permissions during OAuth
- Revoke access in [Google Account Settings](https://myaccount.google.com/permissions) and re-authenticate
- Verify the OAuth scopes include both `gmail.send` and `gmail.readonly`

## Security Notes

- Keep your `client_secret` secure and never commit it to version control
- The `token.json` file contains sensitive authentication data - keep it secure
- Regularly review and revoke unused OAuth tokens in Google Account Settings
- For production, use environment-specific OAuth credentials

## Advanced Configuration

### Custom Redirect URI

If you need to use a different port (e.g., if 8080 is already in use), you can:

1. **Update your `.env` file:**
   ```env
   GMAIL_REDIRECT_URI=http://localhost:YOUR_PORT/
   ```

2. **Update Google Cloud Console:**
   - Go to APIs & Services > Credentials
   - Click on your OAuth 2.0 Client ID
   - Update the "Authorized redirect URIs" to match (e.g., `http://localhost:YOUR_PORT/`)
   - Save the changes

**Important:** The redirect URI in your `.env` file must match exactly what's registered in Google Cloud Console (including the trailing slash).

### Multiple Gmail Accounts

The system supports multiple Gmail accounts under one Google Cloud project. This allows you to send emails from different accounts (e.g., taylor@mavnox.com and taylorjwalshe@gmail.com) using the same OAuth credentials.

#### Setting Up Multiple Accounts

1. **Configure OAuth Consent Screen for Multiple Users:**
   - Go to Google Cloud Console > APIs & Services > OAuth consent screen
   - If your app is in "Testing" mode:
     - Click "ADD USERS" under "Test users"
     - Add **all email addresses** you want to use (e.g., taylor@mavnox.com AND taylorjwalshe@gmail.com)
     - Click "SAVE"
   - If your app is in "Production" mode:
     - All Google accounts can use the app (no need to add test users)
     - However, you may need to verify your app domain first

2. **Verify Redirect URI is Correct:**
   - Go to APIs & Services > Credentials
   - Click on your OAuth 2.0 Client ID
   - Under "Authorized redirect URIs", ensure `http://localhost:8080/` is listed
   - The redirect URI must match exactly (including trailing slash)

3. **Configure Environment Variables:**
   Add all accounts you want to use to your `.env` file:
   ```env
   # Gmail OAuth Credentials (same for all accounts)
   GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GMAIL_CLIENT_SECRET=your_client_secret_here
   GMAIL_REDIRECT_URI=http://localhost:8080/
   
   # List all Gmail accounts you want to use (comma-separated)
   GMAIL_ACCOUNTS=taylor@mavnox.com,taylorjwalshe@gmail.com
   ```

4. **Authenticate Each Account:**
   - Start the application: `python main.py`
   - The first time you try to send from each account, you'll be prompted to authenticate
   - Sign in with the specific account you want to use (e.g., taylorjwalshe@gmail.com)
   - Grant permissions when prompted
   - Each account's token will be saved separately: `token_taylor_mavnox_com.json` and `token_taylorjwalshe_gmail_com.json`

5. **Using Different Accounts:**
   - When sending an email, select the account from the "From Account" dropdown
   - Each account maintains its own authentication token
   - If authentication fails for an account, you'll be prompted to re-authenticate

#### Troubleshooting Multiple Account Issues

**"Access blocked: This app's request is invalid" / "redirect_uri_mismatch" Error:**

This usually happens when:
- The account you're trying to authenticate with is not added as a test user (if app is in Testing mode)
- The redirect URI doesn't match what's registered in Google Cloud Console

**Solution:**
1. **Add the account as a test user:**
   - Go to Google Cloud Console > APIs & Services > OAuth consent screen
   - Scroll to "Test users" section
   - Click "ADD USERS"
   - Add the email address (e.g., taylorjwalshe@gmail.com)
   - Click "SAVE"
   - Wait a few minutes for changes to propagate

2. **Verify redirect URI matches exactly:**
   - Go to APIs & Services > Credentials
   - Click on your OAuth 2.0 Client ID
   - Under "Authorized redirect URIs", check that `http://localhost:8080/` is listed
   - In your `.env` file, ensure `GMAIL_REDIRECT_URI=http://localhost:8080/` (with trailing slash)

3. **Delete old token and re-authenticate:**
   - Delete the token file for the account: `integrations/email/token_taylorjwalshe_gmail_com.json`
   - Restart the application
   - Try sending an email from that account again
   - You'll be prompted to authenticate - make sure to sign in with the correct account

**"Error 400: redirect_uri_mismatch" specifically:**

- The redirect URI in your `.env` file must **exactly match** what's in Google Cloud Console
- Check for trailing slashes, port numbers, and protocol (http vs https)
- Common mistake: `http://localhost:8080` vs `http://localhost:8080/` (missing trailing slash)
- The redirect URI in Google Cloud Console should be: `http://localhost:8080/` (with trailing slash)

**Switching Between Accounts:**

- Each account has its own token file: `token_{sanitized_email}.json`
- To switch accounts, just select a different account from the dropdown when sending
- If an account's token expires, you'll be prompted to re-authenticate automatically

## Next Steps

Once Gmail integration is working:
- **Read the Deliverability Guide**: See `DELIVERABILITY-GUIDE.md` for best practices on email deliverability, warmup strategies, and avoiding spam filters
- Set up SMS integration (see `integrations/sms/SETUP.md`)
- Configure automated email syncing (future feature)
- Set up email templates for common outreach scenarios

## Deliverability and Best Practices

For comprehensive guidance on:
- Understanding email authentication warnings
- Best practices for high deliverability
- Whether you need inbox warmup services
- How to avoid spam filters
- Free alternatives to paid warmup tools

See **[DELIVERABILITY-GUIDE.md](./DELIVERABILITY-GUIDE.md)** for detailed information.
