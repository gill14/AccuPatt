# macOS code signing & notarization — one-time setup

These steps require your Apple ID login and can't be automated for you. Do them
once per machine you build releases on.

## 1. Get a Developer ID Application certificate

1. Open **Keychain Access** → menu **Keychain Access → Certificate Assistant →
   Request a Certificate From a Certificate Authority**.
   - User Email Address: your Apple ID email
   - Common Name: your name or org name
   - Select **Saved to disk**, leave CA email blank → Continue → save
     `CertificateSigningRequest.certSigningRequest` somewhere.
2. Go to [developer.apple.com/account/resources/certificates/add](https://developer.apple.com/account/resources/certificates/add).
3. Choose **Developer ID Application** (under "Software") → Continue.
4. Upload the `.certSigningRequest` file from step 1 → Continue → **Download**.
5. Double-click the downloaded `.cer` file — it installs into your login
   Keychain and pairs with the private key Keychain Access generated.
6. Verify it's installed and note the exact identity string:
   ```
   security find-identity -v -p codesigning
   ```
   You'll see something like:
   `"Developer ID Application: Matt Gill (ABCDE12345)"`

## 2. Set up notarization credentials

1. Find your Team ID at
   [developer.apple.com/account](https://developer.apple.com/account) (top
   right, under your name/org).
2. Generate an app-specific password at
   [appleid.apple.com](https://appleid.apple.com) → Sign-In and Security →
   App-Specific Passwords. (This is scoped to notarization only — not your
   Apple ID password.)
3. Store it in the keychain so future builds don't need it re-entered:
   ```
   xcrun notarytool store-credentials "accupatt-notary" \
       --apple-id "you@example.com" \
       --team-id "TEAMID"
   ```
   It will prompt for the app-specific password interactively (not as a CLI
   arg, so it won't land in shell history).

## 3. Build, sign, notarize, staple

```bash
poetry install --with dev-osx
export CODESIGN_IDENTITY="Developer ID Application: Matt Gill (TEAMID)"
export NOTARY_PROFILE="accupatt-notary"
poetry run python bundle_mac.py py2app
```

`bundle_mac.py` will: build the `.app` with py2app, codesign every nested
binary + the app bundle with Hardened Runtime (`dist/osx/sign_mac.sh`), build
the `.dmg` (`genAppDmg.sh`), then submit it for notarization and staple the
ticket (`dist/osx/notarize_mac.sh`).

Leave `CODESIGN_IDENTITY`/`NOTARY_PROFILE` unset for a quick unsigned local
dev build — those steps are skipped automatically.

## 4. Sanity check the result

```bash
spctl -a -t open --context context:primary-signature -v dist/osx/AccuPatt.dmg
```
Should print `accepted`. A user downloading the DMG should now be able to
open it with a plain double-click — no "unidentified developer" warning.

## Notes / known gotchas

- `liboceandirect.dylib` (vendored Ocean Optics SDK) and several OpenCV
  `.dylib`s ship only ad-hoc signed. `entitlements.plist` sets
  `com.apple.security.cs.disable-library-validation` so Hardened Runtime
  still loads them once re-signed by `sign_mac.sh`.
- The certificate and app-specific password are tied to your Apple ID/Team —
  if release builds ever move to CI (GitHub Actions), the cert (as a
  base64-encoded `.p12`) and notary credentials need to be added as repo
  secrets rather than reused from this machine's keychain.
- If `codesign --verify --deep --strict` fails after adding new dependencies,
  it's almost always a newly-vendored dylib that `sign_mac.sh`'s `find` isn't
  catching — check the failing path it reports and confirm it matches the
  `.dylib`/`.so`/executable-bit search.
