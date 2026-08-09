"""
Cloudflare R2 storage backend for media files (e.g. menu images).

R2 is S3-compatible, so we subclass ``S3Boto3Storage``.  Credentials,
bucket name and endpoint are picked up from the ``AWS_*`` settings that
``settings.py`` configures when ``R2_BUCKET_NAME`` is set, so nothing
sensitive is hard-coded here.

To enable R2, make sure these environment variables are set in ``.env``::

    R2_ACCOUNT_ID          - your Cloudflare account id
    R2_BUCKET_NAME         - the bucket you created
    R2_ACCESS_KEY_ID       - R2 Access Key ID
    R2_SECRET_ACCESS_KEY   - R2 Secret Access Key
    R2_PUBLIC_URL          - (optional) public URL used by ``url()``

Leave ``R2_BUCKET_NAME`` empty and the project falls back to local
filesystem storage, so it keeps working out of the box in a normal dev
environment.
"""
from storages.backends.s3boto3 import S3Boto3Storage


class R2MediaStorage(S3Boto3Storage):
    """S3-compatible storage targeting a Cloudflare R2 bucket.

    ``DEFAULT_FILE_STORAGE`` in ``settings.py`` points here, so every
    ``ImageField``/``FileField`` (including ``Menu.images``) automatically
    uploads to R2 and the database only ever stores the object's URL/path.
    """

    # Keep uploaded objects under "media/" to match MEDIA_ROOT semantics.
    location = "media"

    # Don't overwrite if a file with the same name already exists.
    file_overwrite = False
    # R2 does not use legacy ACL headers the way S3 does.
    default_acl = None
    bucket_acl = None
    # R2 is S3-compatible and accepts the s3v4 signature.
    signature_version = "s3v4"
    # We serve files over a public URL, so don't sign every request.
    querystring_auth = False
    # Always use https for the served URLs.
    url_protocol = "https:"
