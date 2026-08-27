package com.example.citizensurface.protocol

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

class MockCitizenProtocol : CitizenProtocol {
    private val _connectionState = MutableStateFlow(ConnectionState.DISCONNECTED)
    override val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()

    private val _status = MutableStateFlow<CitizenStatus?>(null)
    override val status: StateFlow<CitizenStatus?> = _status.asStateFlow()

    private val _conversationMessages = MutableStateFlow<List<String>>(emptyList())
    override val conversationMessages: StateFlow<List<String>> = _conversationMessages.asStateFlow()

    override suspend fun connect(surfaceId: String) {
        _connectionState.value = ConnectionState.CONNECTING
        delay(1000)
        _connectionState.value = ConnectionState.CONNECTED
        _status.value = CitizenStatus(
            citizenVersion = "1.0.0-mock",
            surfaceVersion = "0.1.0-alpha",
            lastSynchronization = System.currentTimeMillis(),
            updateAvailable = false
        )
    }

    override suspend fun disconnect() {
        _connectionState.value = ConnectionState.DISCONNECTED
        _status.value = null
    }

    override suspend fun reconnect() {
        _connectionState.value = ConnectionState.RECONNECTING
        delay(1000)
        _connectionState.value = ConnectionState.CONNECTED
        _status.value = _status.value?.copy(lastSynchronization = System.currentTimeMillis())
    }

    override suspend fun sendMessage(message: String) {
        val current = _conversationMessages.value.toMutableList()
        current.add("Surface: $message")
        _conversationMessages.value = current
        
        delay(500)
        
        val reply = current.toMutableList()
        reply.add("Citizen: Acknowledged message '$message'")
        _conversationMessages.value = reply
    }
}
