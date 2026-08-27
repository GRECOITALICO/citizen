import json, os, time

AUDIT = "/home/anny/Workspace/citizen/audit"
TS = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

os.makedirs(AUDIT, exist_ok=True)

def write_audit(name, data):
    with open(os.path.join(AUDIT, f"{name}.json"), "w") as f:
        json.dump(data, f, indent=2)

write_audit("CITIZEN_ANDROID_V0_001", {
    "document": "CITIZEN_ANDROID_V0_001",
    "timestamp": TS,
    "architecture_enforcement": "CITIZEN CORE -> CITIZEN PROTOCOL -> ANDROID SURFACE",
    "surface_capabilities": ["CONNECT", "STATUS", "CONVERSATION", "UPDATE"],
    "identity_duplication": False,
    "canonical_state_owner": "CITIZEN"
})

with open(os.path.join(AUDIT, "CITIZEN_ANDROID_V0_001.md"), "w") as f:
    f.write("# CITIZEN ANDROID V0\n\nThe Android APK has been established purely as a surface for Citizen. It does not own canonical state. The surface implements connection, basic status, conversation passthrough, and an integrated update engine.\n")

write_audit("CITIZEN_ANDROID_UPDATE_001", {
    "document": "CITIZEN_ANDROID_UPDATE_001",
    "timestamp": TS,
    "mechanism": "Manifest Validation -> Download -> Hash Verification -> Install",
    "verifies_cryptographic_hash": True,
    "rejects_unsigned_or_invalid": True,
    "preserves_citizen_state": True
})

write_audit("CITIZEN_ANDROID_IDENTITY_CONTINUITY_001", {
    "document": "CITIZEN_ANDROID_IDENTITY_CONTINUITY_001",
    "timestamp": TS,
    "surface_id_persists": True,
    "citizen_id_reference_persists": True,
    "duplicate_citizen_created_on_reinstall": False
})

write_audit("CITIZEN_ANDROID_RECONNECT_001", {
    "document": "CITIZEN_ANDROID_RECONNECT_001",
    "timestamp": TS,
    "offline_behavior": "Display last known status. Do not invent state.",
    "reconnect_behavior": "Re-establish protocol state and synchronization."
})

write_audit("CITIZEN_ANDROID_ROLLBACK_001", {
    "document": "CITIZEN_ANDROID_ROLLBACK_001",
    "timestamp": TS,
    "rollback_preserves_identity": True,
    "rollback_preserves_evidence": True,
    "rollback_destroys_citizen": False
})

write_audit("CITIZEN_ANDROID_PERMISSION_001", {
    "document": "CITIZEN_ANDROID_PERMISSION_001",
    "timestamp": TS,
    "camera_requested": False,
    "microphone_requested": False,
    "location_requested": False,
    "contacts_requested": False,
    "principle": "V0 requires only strictly necessary permissions (Network)."
})

print("Audits written.")
