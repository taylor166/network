# DNS Setup Guide for mavnox.com Email Authentication

## Current Status

Based on your DNS checks:
- ✅ **DKIM**: Set up correctly (Google's DKIM key is present)
- ❌ **SPF**: Missing - needs to be added
- ❌ **DMARC**: Missing - needs to be added

## How to Add Missing Records

### Step 1: Add SPF Record

**What to add:**
- **Type**: TXT
- **Name/Host**: `@` or `mavnox.com` (depends on your DNS provider)
- **Value**: `v=spf1 include:_spf.google.com ~all`
- **TTL**: 3600 (or default)

**Where to add it:**
1. Log into your domain registrar or DNS provider (wherever you manage DNS for mavnox.com)
2. Find the DNS management section
3. Add a new TXT record:
   - Host/Name: `@` or leave blank (some providers use `@`, others use the domain name)
   - Type: `TXT`
   - Value: `v=spf1 include:_spf.google.com ~all`
   - TTL: 3600 (or default)

**Common DNS providers:**
- **Google Domains/Cloud Identity**: DNS → Custom records → Add TXT record
- **Namecheap**: Domain List → Manage → Advanced DNS → Add TXT record
- **GoDaddy**: DNS Management → Add → TXT record
- **Cloudflare**: DNS → Add record → Type: TXT
- **Route 53**: Hosted zones → mavnox.com → Create record → TXT

**Verify after adding:**
```bash
dig TXT mavnox.com +short
```
Should show both the Google site verification AND the SPF record.

### Step 2: Add DMARC Record

**What to add:**
- **Type**: TXT
- **Name/Host**: `_dmarc`
- **Value**: `v=DMARC1; p=quarantine; rua=mailto:taylor@mavnox.com; pct=100`
- **TTL**: 3600 (or default)

**Where to add it:**
1. Same DNS management interface as above
2. Add a new TXT record:
   - Host/Name: `_dmarc` (important: include the underscore)
   - Type: `TXT`
   - Value: `v=DMARC1; p=quarantine; rua=mailto:taylor@mavnox.com; pct=100`
   - TTL: 3600 (or default)

**DMARC Policy Options:**
- `p=none` - Monitor only (no action, just reports)
- `p=quarantine` - Soft fail (send to spam folder) - **Recommended to start**
- `p=reject` - Hard fail (reject email) - Use after monitoring

**Start with `p=quarantine`** to monitor without being too strict. After a few weeks of good results, you can change to `p=reject`.

**Verify after adding:**
```bash
dig TXT _dmarc.mavnox.com +short
```
Should show the DMARC record.

### Step 3: Wait for Propagation

DNS changes can take:
- **Immediate to 5 minutes**: Most modern DNS providers
- **Up to 24 hours**: Some providers (rare)
- **Usually 5-15 minutes**: Typical propagation time

**Check propagation:**
```bash
# Check SPF
dig TXT mavnox.com +short

# Check DMARC
dig TXT _dmarc.mavnox.com +short
```

### Step 4: Verify Everything is Working

After adding both records, verify with:

```bash
# Should show SPF record
dig TXT mavnox.com +short

# Should show DMARC record
dig TXT _dmarc.mavnox.com +short

# Should show DKIM (already working)
dig TXT google._domainkey.mavnox.com +short
```

**Or use online tools:**
- [MXToolbox SPF Checker](https://mxtoolbox.com/spf.aspx) - Enter `mavnox.com`
- [DMARC Analyzer](https://www.dmarcanalyzer.com/) - Enter `mavnox.com`
- [Google Admin Toolbox](https://toolbox.googleapps.com/apps/checkmx/check) - Comprehensive check

## Expected Results

After setup, your DNS should show:

**SPF:**
```
"v=spf1 include:_spf.google.com ~all"
```

**DMARC:**
```
"v=DMARC1; p=quarantine; rua=mailto:taylor@mavnox.com; pct=100"
```

**DKIM (already working):**
```
"v=DKIM1; k=rsa; p=..." (long key)
```

## Troubleshooting

### SPF Record Not Showing

**Possible issues:**
1. **Wrong host name**: Try both `@` and `mavnox.com` depending on your provider
2. **Propagation delay**: Wait 5-15 minutes and check again
3. **Multiple TXT records**: Some providers require separate records, others allow multiple values in one record
4. **Syntax error**: Make sure there are no extra spaces or quotes in the value

**Test with:**
```bash
dig TXT mavnox.com +short | grep -i spf
```

### DMARC Record Not Showing

**Possible issues:**
1. **Missing underscore**: Must be `_dmarc`, not `dmarc`
2. **Wrong subdomain**: Should be `_dmarc.mavnox.com`, not `_dmarc@mavnox.com`
3. **Propagation delay**: Wait 5-15 minutes

**Test with:**
```bash
dig TXT _dmarc.mavnox.com +short
```

### Multiple TXT Records

If you see multiple TXT records (like Google site verification + SPF), that's normal and correct. DNS allows multiple TXT records for the same domain.

## Quick Reference

**SPF Record:**
```
Type: TXT
Name: @ (or mavnox.com)
Value: v=spf1 include:_spf.google.com ~all
```

**DMARC Record:**
```
Type: TXT
Name: _dmarc
Value: v=DMARC1; p=quarantine; rua=mailto:taylor@mavnox.com; pct=100
```

**DKIM:**
✅ Already configured by Google (no action needed)

## After Setup

Once both records are added and verified:

1. **Wait 24-48 hours** for full propagation
2. **Test email sending** - Send a test email to yourself
3. **Check Google Postmaster Tools** - Set up monitoring (see DELIVERABILITY-GUIDE.md)
4. **Monitor DMARC reports** - Check the email address you specified in `rua=`
5. **Test with mail-tester.com** - Should get 10/10 score

## Need Help?

If you're not sure where to add DNS records:
1. Check your domain registrar's documentation
2. Look for "DNS Management" or "DNS Settings" in your account
3. Contact your DNS provider's support
4. Use online tools to verify records are correct
