#!/usr/bin/env python3
import aws_cdk as cdk
from src.AgentCoreStack import AgentCoreStack

app = cdk.App()
agentCoreStack = AgentCoreStack(app, "StockResearchAgent")

app.synth()
