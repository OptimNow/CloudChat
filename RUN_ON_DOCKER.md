## How to run the project

First, build the image:

```bash
docker build -t cloudchat:latest .
```

Then, run it with Docker by choosing one of the 3 authentication strategies:

### Using the IAM role strategy (when running on AWS)

First, set your AWS credentials as environment variables:
```bash
export AWS_REGION=your_region
```

Then run it with Docker passing the correct environment variables:
```bash
docker run -it \
  --network=bridge \
  -p 8000:8000 \
  --env AWS_REGION=$AWS_REGION \
  --env AWS_LOGIN_STRATEGY=aws_iam_role \
  cloudchat:latest
```

### Using the AWS SSO login strategy

First, set your AWS credentials as environment variables:
```bash
export AWS_REGION=your_region
export AWS_CONFIG_DIR=~/.aws
export AWS_PROFILE=your_aws_profile
```

Then run it with Docker passing the correct environment variables:
```bash
docker run -it \
  --network=bridge \
  -p 8000:8000 \
  --env AWS_REGION=$AWS_REGION \
  --env AWS_LOGIN_STRATEGY=aws_sso \
  --env AWS_PROFILE=$AWS_PROFILE \
  --volume $AWS_CONFIG_DIR:/aws \
  cloudchat:latest
```

### Using the AWS Keys login strategy

First, set your AWS credentials as environment variables:
```bash
export AWS_REGION=your_region
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_SESSION_TOKEN=your_session_token
```

Then run it with Docker passing the correct environment variables:
```bash
docker run -it \
  --network=bridge \
  -p 8000:8000 \
  --env AWS_REGION=$AWS_REGION \
  --env AWS_LOGIN_STRATEGY=aws_keys \
  --env AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  --env AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  --env AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN \
  cloudchat:latest
```