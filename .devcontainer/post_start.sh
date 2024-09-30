#!/usr/bin/env bash

pre-commit install

# Install CDK requirements
(
    cd cdk
    pip install -r <(pipenv requirements --dev)
)

# Install lambda requirements
(
    cd src
    pip install -r <(pipenv requirements --dev)
)
