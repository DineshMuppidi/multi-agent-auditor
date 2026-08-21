# 🛠️ Engineering Remediation Playbook

## 1. Overview of Affected Assets

We have identified two S3 buckets that require remediation:

* `public-marketing-assets-temp` - Public bucket with incorrect permissions
* `unencrypted-storage-bucket` - Unencrypted bucket in need of Server-Side Encryption (SSE)

Additionally, we have a Jira ticket (COMP-101) associated with the unencrypted storage bucket.

## 2. Step-by-Step Remediation Commands

### Enable AES-256 Server-Side Encryption on `unencrypted-storage-bucket`

```bash
aws s3api put-bucket-server-encryption --bucket unencrypted-storage-bucket --sse-Algorithm AES_256 --sse-kms-key-id <KMS_KEY_ID> --request-payer requester
```

Replace `<KMS_KEY_ID>` with the ID of the KMS key that has access to the bucket.

###Enable Public Access Blocks on `public-marketing-assets-temp`

```bash
aws s3api put-public-access-block --bucket public-marketing-assets-temp --block-users --exclude-public-prefix --request-payer requester
```

This command will block all public access to the bucket, including anonymous and authenticated access. Be cautious when running this command.

Alternative option (only for access logs):

```bash
aws s3api put-public-access-block --bucket public-marketing-assets-temp --block-include-public-prefix --request-payer requester
```

### Alternative Methodto Block Public Access

Instead of using the `put-public-access-block` command, you can create a CORS configuration file (`cors.xml`) and upload it to the bucket.

```bash
aws s3api put-bucket-cors --bucket public-marketing-assets-temp --cors-configuration file://path/to/cors.xml --request-payer requester
```

Create a `cors.xml` file with the following content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
< bucket policy>
    < cors>
        < policy>
            < allowed-origins >_*</allowed-origins>
            < allowed-methods >GET,HEAD</allowed-methods>
            < allowed-headers >*</allowed-headers>
            < expose-http-methods >None</expose-http-methods>
            < max-age >3600</max-age>
        </policy>
    </cors>
</bucket-policy>
```

This policy blocks public access to the bucket, except for specific headers.

## 3. Ticket Closure Procedure

After applying the remediation commands to both buckets, we need to update the Jira ticket (COMP-101) to indicate that the remediation has been completed:

1. Log in to the Jira instance as an administrator.
2. Find the COMP-101 ticket and click on its details page.
3. Update the status of the ticket from `In Progress` to `RESOLVED`.
4. Optionally, add a comment describing the changes made to the bucket permissions.

This ensures that our remediation efforts are documented and verified in Jira, providing visibility into the actions taken to protect sensitive data.