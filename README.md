# ARIS

ARIS (A-R-I-S) is a Windows desktop assistant project. The first release is a local-first MVP: a lightweight status overlay, voice interaction, a small allowlisted set of computer actions, and user-controlled preferences.

The MVP does not attempt unrestricted computer control or self-modifying behavior. Actions are added through reviewed tools with narrow permissions. User rules and preferences remain editable by the owner.

## Project status

See [the project plan](docs/PROJECT_PLAN.md), [architecture](docs/ARCHITECTURE.md), [security model](docs/SECURITY.md), and [developer guide](docs/DEVELOPMENT.md). The first implementation section is the Windows shell and status overlay. Voice and task tools will be added in later sections.

## User rules

`USER_RULES.md` is intentionally blank so the owner can define ARIS's behavior. Until rules are added, the application follows the fixed safety controls in the code and [security model](docs/SECURITY.md).

## License

No license has been selected yet. Do not redistribute this project until its owner chooses one.
