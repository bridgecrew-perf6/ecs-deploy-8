#!/usr/bin/env python3

from aws_cdk import core

from infra.infra_stack import InfraStack


app = core.App()
InfraStack(app, "infra")

app.synth()
