# Deploying the frontend (the "live site")

**The live site is not a git push.** The InstructorDash React app is built into static
files and hosted on **AWS S3 + CloudFront**. "Pushing to the live site" means uploading
the build to an S3 bucket and invalidating the CloudFront cache.

| | |
|---|---|
| Live URL | https://d7o47tp7r931l.cloudfront.net |
| S3 bucket | `test-18-may-instructordash` |
| CloudFront distribution | `ESSBPX2SEQR6S` |
| AWS account | `859108043010` |
| Region | `ap-southeast-2` (Sydney) |

## Getting access (the "key")

There is **no static key file to copy** — access is an **AWS IAM Identity Center (SSO)
grant**. That's why someone already deploying "doesn't remember getting a key": they were
added as a user, not handed a secret.

Ask the AWS account owner (account `859108043010`) to add you as a user in **IAM Identity
Center** with a permission set that allows:

- S3 write to `test-18-may-instructordash`, and
- CloudFront `CreateInvalidation` on distribution `ESSBPX2SEQR6S`.

> Fallback if SSO onboarding isn't available: an IAM access-key pair (Access Key ID +
> Secret) with the same permissions, configured via `aws configure`.

## Configure the AWS CLI

```bash
aws configure sso
#   SSO start URL: https://identitycenter.amazonaws.com/ssoins-82596a7dc8914808
#   SSO region:    ap-southeast-2
#   choose any local profile name (use your own, not someone else's)
aws sso login --profile <your-profile>
```

Sanity check — this must report account `859108043010`:

```bash
aws sts get-caller-identity --profile <your-profile>
```

## Deploy

```bash
AWS_PROFILE=<your-profile> npm run deploy
```

This builds the app, syncs `build/` to S3, and invalidates the CloudFront cache. Changes
go live as soon as the invalidation completes (usually under a minute).
