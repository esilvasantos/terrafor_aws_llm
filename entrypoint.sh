#!/bin/sh

# Export environment variables from the .env file
set -a
. /root/.env
set +a

# Configure AWS credentials
aws configure set aws_access_key_id "$AWSACCESSKEYID"
aws configure set aws_secret_access_key "$AWSSECRETKEY"
aws configure set region "$AWS_REGION"

# Pass control to the command defined by the user (bash by default)
exec "$@"
