# TODO: Fix images not showing in pages

- [x] Step 1: Update Croestore/Corestore/settings.py - Add STATIC_ROOT and STATICFILES_DIRS
- [x] Step 2: Update Croestore/Corestore/urls.py - Add MEDIA_URL static serving
- [x] Step 3: Restart development server
- [x] Step 4: Run python manage.py collectstatic --noinput (if static files broken)
- [ ] Step 5: Test by uploading an image via admin/seller and viewing product pages
- [ ] Step 6: Verify images load from /media/ paths
