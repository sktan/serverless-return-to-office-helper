# Return to Office Helper

The Return to Office helper is a simple web application that allows users to track their office attendance throughout the month.

Deployed resources are as follows:

- CloudFront Distribution
- 2x S3 Buckets to store the assets + assets bundle
- 2x DynamoDB
- API Gateway
- 1x Lambda Function (to handle HTTP requests to API Gateway)
- KMS (we will be using the dynamodb default kms key)

## Usage

You will need to create a dashboard by going to the homepage and pressing the "Create one now". Once a dashboard has been created, a unique URL will be generated for you to access it.

By keeping the tab open and disabling tab sleep for this tab or by using the cronhelper apps, you will be able to automatically detect your office attendance.

## Deployment

Deploying this is really easy, due to AWS CDK being used for building and deploying the entire website and backend services.

To deploy the website, you will need the following requirements (already bundled within the Visual Studio Code Devcontainer)

- An AWS account
- AWS CDK v2
- Python 3.9
- Pipenv
- Nodejs
- Docker (to build the website)

``` shell
sktan ➜ ~/repos/sktan/serverless-return-to-office-helper (master ✗) $ cd cdk
sktan ➜ ~/repos/sktan/serverless-return-to-office-helper/cdk (master ✗) $ pipenv run cdk bootstrap # only need to run this once
sktan ➜ ~/repos/sktan/serverless-return-to-office-helper/cdk (master ✗) $ pipenv run cdk deploy rtoapp-database
sktan ➜ ~/repos/sktan/serverless-return-to-office-helper/cdk (master ✗) $ pipenv run cdk deploy rtoapp-backend
sktan ➜ ~/repos/sktan/serverless-return-to-office-helper/cdk (master ✗) $ pipenv run cdk deploy rtoapp-backend
```

This will deloy the entire service to AWS automatically without any configuration or building of the frontend on your part.

You are also able to configure your deployment to use a custom domains and certificate for both CloudFront and API Gateway.

This is done via the `cdk/cdk.json` file under the `context` keys:

| Context Key           | Description             |
| --------------------- | ----------------------- |
| office_ips            | The known IP addresses of your office so that you can track where a request is coming from |
| frontend_domain       | The domain that will point to CloudFront for the WebUI  |
| frontend_acm          | The ACM certificate to be used for CloudFront (should be in us-east-1)           |
| backend_domain        | The domain that will point to the API Gateway  |
| backend_acm           | The ACM certificate to be used for API Gateway (can be in your deployment region)          |

``` json
{
  "context": {
    "app_config": {
      "office_ips": [
        "8.8.8.8",
        "1.1.1.1"
      ],
      "backend_domain": "rto.api.example.com",
      "backend_acm": "arn:aws:acm:ap-southeast-2:123456789012:certificate/62f3dd58-5113-4914-bb0e-702a93af2f7c",
      "frontend_domain": "rto.example.com",
      "frontend_acm": "arn:aws:acm:us-east-1:123456789012:certificate/62f3dd58-5113-4914-bb0e-702a93af2f7c"
    }
  }
}
```

In the frontend directory, create a new `.env` file and replace `VITE_WEBAPI_ENDPOINT` with your Backend API Domain.

## Development

Requirements:

- Black (for Python formatting)
- Eslint (for Nodejs formatting)
- boto3 (for testing the lambda function)
- boto3-stubs (optional, but for boto3 type hinting)

You are able to run a local development environment by deploying the backend services to AWS, and adding the API gateway the `frontend/.env` file (copy the contents from `frontend/.env.example`).

Once you have deployed the backend, you can run the `npm run dev` command to start the frontend development server.

You will be able to find the backend lambda function source in the `src` directory.

Both the CDK infrastructure as code and lambda sourcecode have unit-tests included, so you will be able to test any changes before deployment by running `pipenv run pytest --cov --cov-report term-missing -v`
