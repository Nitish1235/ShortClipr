# How to Set Up YouTube Cookies for ShortClipr Worker

The worker uses a YouTube `cookies.txt` file to authenticate requests from our GCP datacenter IP,
bypassing the "Sign in to confirm you're not a bot" error.

## Why Cookies?

Google detects GCP datacenter IPs as bot-origin traffic. Even with correct PO Tokens, some IP
ranges get `LOGIN_REQUIRED` on all clients (web, mweb, android). Cookies make the request appear
to come from a logged-in human browser session, bypassing this entirely.

---

## Step 1: Export Cookies (Official Method — robots.txt trick)

> **Important**: This method creates a session that YouTube will NOT rotate (unlike a normal tab).

1. Install the **"Get cookies.txt LOCALLY"** Chrome extension:
   - https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - ⚠️ Use "LOCALLY" version only — the non-LOCALLY version is malware

2. Open a **new incognito/private window** in Chrome

3. In that window, **log into YouTube** (use a throwaway Google account, not your main account)

4. In the **same tab**, navigate to: `https://www.youtube.com/robots.txt`
   - This prevents the session from being opened again and rotated

5. Click the "Get cookies.txt LOCALLY" extension icon and export cookies for `youtube.com`

6. **Close the incognito window immediately** — the session is now "frozen"

7. Save the file as `cookies.txt`

---

## Step 2: Add to Cloud Run

### Option A: As an Environment Variable (Recommended)

1. Base64-encode the file:
   ```bash
   # On Linux/Mac:
   base64 cookies.txt | tr -d '\n'

   # On Windows PowerShell:
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("cookies.txt"))
   ```

2. Add to Cloud Run as a secret:
   - Go to **GCP Console → Secret Manager → Create Secret**
   - Name: `youtube-cookies`
   - Value: paste the base64 string
   
3. In Cloud Run service → Edit & Deploy → **Environment Variables**:
   - Add: `YOUTUBE_COOKIES` = (reference the Secret Manager secret)

### Option B: As a Secret Volume Mount

1. Upload `cookies.txt` to Secret Manager as a binary secret
2. Mount it in Cloud Run at `/app/cookies.txt`
3. Set env var: `YOUTUBE_COOKIES_FILE=/app/cookies.txt`

---

## Step 3: Verify

After deploying, check logs for:
```
[cookies] Decoded YOUTUBE_COOKIES env var → /tmp/shortclipr_yt_cookies.txt
[cookies] Attached cookiefile to yt-dlp opts: /tmp/shortclipr_yt_cookies.txt
```

And the download should then show:
```
[youtube] sX6gEwH-SA4: web player response playability status: OK
[youtube] Downloading audio ...
```

---

## Cookie Rotation Warning

YouTube rotates cookies **every ~30 days** if the session is opened in a browser again.
Our robots.txt export method prevents rotation, but you may still need to refresh cookies
every 30-90 days if downloads start failing again with `LOGIN_REQUIRED`.

---

## Security Notes

- Use a **throwaway Google account**, not your personal account
- The cookies contain full authentication tokens — treat them like passwords
- Storing in GCP Secret Manager encrypts them at rest
- Never commit `cookies.txt` to git (it's in `.gitignore`)
