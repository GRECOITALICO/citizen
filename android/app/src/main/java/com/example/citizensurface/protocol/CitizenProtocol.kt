package com.example.citizensurface.protocol

import kotlinx.coroutines.flow.StateFlow

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    RECONNECTING,
    ERROR
}

data class CitizenStatus(
    val citizenVersion: String,
    val surfaceVersion: String,
    val lastSynchronization: Long,
    val updateAvailable: Boolean
)

interface CitizenProtocol {
    val connectionState: StateFlow<ConnectionState>
    val status: StateFlow<CitizenStatus?>
    val conversationMessages: StateFlow<List<String>>

    suspend fun connect(surfaceId: String)
    suspend fun disconnect()
    suspend fun reconnect()
    
    suspend fun sendMessage(message: String)
}
