# Reusable Workflows
**THIS REPOSITORY MUST BE FORKED INTO YOUR CONTEXT IN ORDER TO PASS SECRETS!**
## Action Prefixes:
- `alert-`: Offers an API through which to send a notification.
- `build-`: Offers an action to build/compile an application.
- `gh-`: Offers meta github functionality.
- `meta-`: Meta functionality to be used by other workflows (not called from other repos).
- `publish-`: Offers an action to publish a build application to a registry.
- `test-`: Offers an action to run a test suite.
*If an action is language/framework specific, a `lang-` section follows the above prefix before the descriptor.
## Triggers:
The `triggers` folder contains trigger actions that go into repositories to trigger the core actions.
- `on-pr-`: Triggers on PR made to specified branches.
- `on-push-`: Triggers on push made to specified branches.
