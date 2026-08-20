# Requesting a New Cloud Environment

**Department:** Cloud

## Issue
A team needs a new cloud environment/account/project provisioned (e.g., for
a new application or a dev/test environment).

## Resolution
1. Gather required details: environment purpose, expected owner/team,
   estimated resource needs, and environment type (dev/test/staging/prod).
2. New environments are provisioned from the standard landing-zone template,
   which includes baseline security guardrails, logging, and cost tagging —
   do not create ad hoc accounts/projects outside this process.
3. Confirm required tags (cost center, owner, environment) are applied at
   creation time — retrofitting tags later is a recurring source of
   untraceable spend.
4. Provide the requesting team with access following least-privilege
   defaults; broader access can be requested separately once genuinely
   needed.

## Notes
"Just clone an existing environment" requests should still go through
proper provisioning — cloned environments tend to carry over
overly-broad permissions from the source.
