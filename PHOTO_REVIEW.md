# Student Edition: local ECG photo review pilot

Development branch: student-photo-review. Base: 49f389ff1c48d72f0a092cb8574f0b04397fb9b9.
Live student-edition, main, validation-v03 and research algorithms are unchanged.

## Architecture and privacy
Authenticated student_app.py embeds a self-contained HTML component. The file picker opens JPEG/PNG/WebP locally in the browser, not through st.file_uploader. No image, filename or comment is sent to Python, a server, analytics or an external service. The component has no fetch, storage or parent messaging API; CSP blocks network connections and form submission. No new application dependency.

Before choosing a photo, users must physically cover or crop identifiers and confirm permission for teaching use. A local preview allows opaque rectangular masking, then a second explicit whole-image review is required before notes become available. No OCR or automatic PHI detection. Human confirmation can be mistaken: this does NOT guarantee that an image is anonymous. The local-only architecture prevents accidental submission of identifiable pixels to the app server. Screen capture, device security, browser extensions and a user's own original photo are outside this protection.

The decoded canvas contains only pixels, not EXIF metadata. Blob URLs are revoked after decoding. Masking overwrites canvas pixels without undo; rotate copies only the current masked canvas. Original files on the device are untouched. Clear wipes the canvas, comment and picker. Changing module, reload or logout destroys the iframe. Browser memory reclamation is implementation-dependent, not secure forensic erasure. There is no permanent app storage, cross-device synchronization, download or instructor submission. Comments are max 5000 characters and are not graded.

Limits: one photo, 15 MB, decoded dimensions <=24 MP. HEIC must be exported to JPEG on device. All 12 leads and printed speed/gain must remain visible. Zoom is visual only, not calibrated measurement. No automatic QRS, arrhythmia, QT, digitization or diagnosis.

## Verification
Run from repository root:
`python -m unittest test_photo test_student -v`
`node test_photo_client.cjs`
The Node checks use a mocked DOM/canvas and verify state transitions, not browser rendering, pixel orientation or mobile touch behavior. Real browser engine download failed in the development environment. Actual iPhone/Android test is mandatory before promoting the branch. Existing Streamlit HTML component API works in installed 1.67 but emits a deprecation warning; a future Streamlit upgrade needs a compatibility check.

## Separate phone staging test (do not edit existing deployment)
Create a NEW Streamlit app from CeyhunCeyhan/cardiorhythm-ai-edu, branch student-photo-review, entrypoint student_app.py, Python 3.12. Configure test accounts and approved cases in the new app's Secrets without sharing credentials. Keep current live deployment on student-edition.
1. Sign in as student. Confirm all five existing cases and answer feedback.
2. Select EKG fotoğrafı inceleme. File picker must be disabled until initial confirmation.
3. First use a non-patient test image marked TEST NAME/TEST ID. Select JPEG, PNG, WebP from iPhone/Android gallery; if OS offers camera, test a freshly taken photo too. HEIC should be rejected with guidance.
4. Mask TEST NAME/ID by dragging. Confirm the whole image; open notes. Try fit, 2x/4x, touch scrolling and 90-degree rotations. Verify all 12 leads remain legible and masks rotate with pixels.
5. Type a test interpretation. Clear: image and comment must disappear. Also test module change, reload, logout and a separate browser session.
6. Reject oversized and corrupt files. Desktop network inspector should show no image/comment upload during selection, masking, zoom or typing.
7. Run a short 10–15 phone classroom rehearsal. Local handling reduces server work but concurrency and device behavior have not yet been proven.
Only after successful phone review should promotion to student-edition be considered. No merge/promotion is performed by this change.
