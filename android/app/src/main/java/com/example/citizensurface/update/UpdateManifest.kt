package com.example.citizensurface.update

data class UpdateManifest(
    val manifestVersion: Int,
    val citizenProtocolVersion: String,
    val surfaceVersion: String,
    val releaseVersion: String,
    val artifactUrl: String,
    val artifactHash: String,
    val artifactSize: Long,
    val releaseId: String,
    val minimumSupportedVersion: String,
    val rollbackInformation: String
)
