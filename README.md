# gmail-cleaner

Small Python script to clean up my Gmail inbox automatically using the Gmail API.

## What it does
Connects to Gmail via OAuth, scans your inbox and clears out clutter based on rules I've set (old promo emails, read newsletters etc). Built this because I was sick of manually archiving the same junk every week.

## Setup
1. Create a Google Cloud project and enable the Gmail API
2. Download your OAuth credentials as `credentials.json` and drop it in this folder
3. `pip install -r requirements.txt` (or install google-auth, google-auth-oauthlib, google-api-python-client)
4. Run `python cleaner.py` - first run will open a browser to authenticate, then it'll save a token so you don't have to log in every time

## Notes
credentials.json and token.json are gitignored on purpose since they're personal to your Google account - you'll need to generate your own.
