# Update Protocol

Android = Citizen Surface. Citizen Core remains the owner of canonical state.

The Update Engine fetches a manifest, verifies cryptographic hashes, rejects invalid/unsigned artifacts, and delegates the install to the Android package manager. If an update fails, rollback preserves all Citizen identity and state.
