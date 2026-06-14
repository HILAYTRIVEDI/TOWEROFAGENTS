# Band Integration

Band is the visible collaboration and audit layer. Each workflow creates or reuses a room, posts the workflow goal and assignments, receives agent status/finding messages, and publishes the final summary. Message metadata is mirrored into `band_messages`.

`BandClient` is the adapter contract:

- `MockBandClient` creates local IDs and logs clearly labeled mock messages.
- `BandSDKClient` will wrap the real SDK and must fail as unconfigured until implemented.

The backend chooses a client from `BAND_MODE`. No caller should branch on SDK details.

