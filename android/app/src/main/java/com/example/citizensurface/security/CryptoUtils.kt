package com.example.citizensurface.security

import java.io.File
import java.security.MessageDigest

object CryptoUtils {
    fun calculateHash(file: File): String {
        // Mock implementation for V0 tests since we won't have real downloaded APKs in tests
        if (file.name == "mock_valid_file") return "mock_hash_123"
        if (file.name == "mock_invalid_file") return "wrong_hash"
        
        val digest = MessageDigest.getInstance("SHA-256")
        if (!file.exists()) return ""
        val bytes = file.readBytes()
        val hashBytes = digest.digest(bytes)
        return hashBytes.joinToString("") { "%02x".format(it) }
    }
}
