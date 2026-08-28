#!/usr/bin/env bash
#
# Deploy the InstructorDash build to the live site (S3 + CloudFront).
# The "live site" is NOT a git push — it's a static build uploaded to S3 and
# served via CloudFront. See DEPLOY.md for how to get AWS access.
#
# Usage: AWS_PROFILE=<your-sso-profile> npm run deploy
#    or: ./deploy.sh <your-sso-profile>
#
set -euo pipefail

PROFILE="${AWS_PROFILE:-${1:-}}"
REGION="ap-southeast-2"
BUCKET="test-18-may-instructordash"
DIST_ID="ESSBPX2SEQR6S"

if [ -n "$PROFILE" ]; then
  PROFILE_ARG="--profile $PROFILE"
else
  PROFILE_ARG=""
fi

cd "$(dirname "$0")"

npm run build
aws s3 sync ./build "s3://$BUCKET/" --delete --region "$REGION" $PROFILE_ARG
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" $PROFILE_ARG

echo "Deployed → https://d7o47tp7r931l.cloudfront.net"
