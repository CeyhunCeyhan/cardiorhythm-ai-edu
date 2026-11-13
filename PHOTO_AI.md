# Experimental educational ECG commentary

Separate development branch; existing photo viewer remains default. No new service
besides opt-in OpenAI Responses API; no new pip dependencies. Pillow is already a
Streamlit dependency. This is not clinically validated ECG interpretation.

## Test deployment
Use this branch only in a separate test Streamlit app, student_app.py, Python 3.12.
Keep the existing users/student_edition Secrets unchanged. Add:

```toml
[photo_ai]
enabled = true
model = "gpt-4.1"
api_key = "REPLACE_PRIVATELY_IN_STREAMLIT_SECRETS"
```
Never commit the actual key or send it in chat. Use a project-scoped key with
Responses permission. Set provider usage limits and billing alerts. Local rate
limits (5/account/hour and 30/process/hour) reset on server restart and are not a
hard monetary budget. A shared student account shares the limit.
Set enabled=false to restore the exact local-only viewer.

## Data flow and limitations
Only after manual de-identification, visual confirmation and separate transmission
consent does the component send flattened PNG canvas pixels to the authenticated
server, which re-encodes to discard metadata and calls OpenAI. Original filename,
EXIF and the student's free-text comment are not sent. No automated identity
recognition guarantee. If identifiers remain visible they can leave the device;
manual review is essential. No application disk writes or image caching. The
Streamlit component value temporarily holds the image until reply acknowledgement;
clear/logout/reload removes client state. RAM is not cryptographically erased.

Responses store=false disables stored response state, not all provider retention.
Default abuse-monitoring retention can be up to 30 days, with policy exceptions;
zero data retention is not promised. Refer to current provider data controls.
Output is untrusted plain text, explicitly experimental and requires instructor
review. No automated measurements, clinical clearance or treatment recommendation.
The model can miss findings or hallucinate. Image quality/resizing affect details.

## Focused verification
19 Python tests passed (existing 14 plus five API/validation/limiter tests), without
real patient data or a real API request. Existing JS pan/mask regression test passed.
Additional JS mocked component test passed: no image before consent, single send
on double click, reply request matching, text-only output, ACK and clear.
Real Streamlit component transport and iPhone/Android rendering remain unverified.
No clinical accuracy evaluation was performed. No paid API call performed.

## Phone acceptance before use
1. Open test app, sign in; confirm five synthetic modules remain available.
2. Use a synthetic or fully de-identified teaching photo; mask and rotate; confirm.
3. Before transmission consent, AI button must remain disabled.
4. Consent, send once, wait for educational draft; compare manually with instructor.
5. Clear: photo, comment and AI draft should disappear. Switch modules and log out.
6. Repeat on iPhone and Android; verify zoom/pan does not draw black marks.
7. Check provider usage dashboard; investigate errors without logging image bodies.

Docs: https://developers.openai.com/api/docs/guides/images-vision
https://developers.openai.com/api/docs/guides/your-data


## Clinical pilot hold — 2026-11-13
The first real API response arrived on iPhone. The instructor identified major
errors: inferior ST-elevation MI with anterior reciprocal changes was described
as anterior ST elevation and wide-complex tachycardia. This instructor reference
is not an independently adjudicated study label. No patient image is committed.
The second conversational interpretation also missed the inferior STEMI pattern;
another LLM answer must not serve as the reference standard.

AI now requires authenticated role=admin on the widget AND server request path.
Student/resident accounts retain local photo review and their own notes. This is
the existing app users Secrets role, not GitHub/OpenAI Owner. No Secrets changed.

Revised instructions request visible calibration only, QRS/ST-T separation,
lead-by-lead ST observations, regional/reciprocal consistency and uncertainty.
This prompt revision is NOT a demonstrated accuracy improvement. No model switch,
extra calls or second-pass model verifier was added.

Before student release, compare against instructor-labelled independent examples:
inferior/anterior STEMI, reciprocal changes, narrow/wide complexes, normal ECGs,
and poor photos. Keep this failed case for regression and reserve unseen cases.
Record missed findings, false positives, localization errors, invented calibration
and abstentions; repeat selected examples to assess variability. Any missed acute
ischemic pattern or false wide-QRS interpretation blocks release. A small passing
set is not clinical validation. Each pilot output needs clinician review.
This clinical evaluation has NOT been run; the API key stays in Streamlit Secrets.
