package com.example.citizensurface

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.citizensurface.protocol.CitizenProtocol
import com.example.citizensurface.protocol.MockCitizenProtocol
import com.example.citizensurface.update.UpdateEngine
import com.example.citizensurface.update.UpdateState
import kotlinx.coroutines.launch
import java.io.File

class MainActivity : ComponentActivity() {
    private val protocol: CitizenProtocol = MockCitizenProtocol()
    private val updateEngine = UpdateEngine()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    CitizenApp(protocol, updateEngine, cacheDir)
                }
            }
        }
    }
}

@Composable
fun CitizenApp(protocol: CitizenProtocol, updateEngine: UpdateEngine, cacheDir: File) {
    var selectedTab by remember { mutableIntStateOf(0) }
    
    Column(modifier = Modifier.fillMaxSize()) {
        TabRow(selectedTabIndex = selectedTab) {
            Tab(selected = selectedTab == 0, onClick = { selectedTab = 0 }, text = { Text("Home") })
            Tab(selected = selectedTab == 1, onClick = { selectedTab = 1 }, text = { Text("Chat") })
            Tab(selected = selectedTab == 2, onClick = { selectedTab = 2 }, text = { Text("Update") })
        }
        
        Box(modifier = Modifier.weight(1f).padding(16.dp)) {
            when (selectedTab) {
                0 -> HomeTab(protocol)
                1 -> ChatTab(protocol)
                2 -> UpdateTab(updateEngine, cacheDir)
            }
        }
    }
}

@Composable
fun HomeTab(protocol: CitizenProtocol) {
    val connectionState by protocol.connectionState.collectAsState()
    val status by protocol.status.collectAsState()
    val scope = rememberCoroutineScope()

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Citizen Surface V0", style = MaterialTheme.typography.headlineMedium)
        
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Connection Status: $connectionState", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(8.dp))
                if (status != null) {
                    Text("Citizen Version: ${status!!.citizenVersion}")
                    Text("Surface Version: ${status!!.surfaceVersion}")
                }
            }
        }
        
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = { scope.launch { protocol.connect("android-surface-1") } }) {
                Text("Connect")
            }
            Button(onClick = { scope.launch { protocol.disconnect() } }) {
                Text("Disconnect")
            }
        }
    }
}

@Composable
fun ChatTab(protocol: CitizenProtocol) {
    val messages by protocol.conversationMessages.collectAsState()
    val scope = rememberCoroutineScope()
    var inputText by remember { mutableStateOf("") }

    Column(modifier = Modifier.fillMaxSize()) {
        LazyColumn(modifier = Modifier.weight(1f)) {
            items(messages) { msg ->
                Text(msg, modifier = Modifier.padding(vertical = 4.dp))
            }
        }
        
        Row(modifier = Modifier.fillMaxWidth()) {
            OutlinedTextField(
                value = inputText,
                onValueChange = { inputText = it },
                modifier = Modifier.weight(1f)
            )
            Button(
                onClick = {
                    if (inputText.isNotBlank()) {
                        scope.launch { protocol.sendMessage(inputText) }
                        inputText = ""
                    }
                },
                modifier = Modifier.padding(start = 8.dp)
            ) {
                Text("Send")
            }
        }
    }
}

@Composable
fun UpdateTab(updateEngine: UpdateEngine, cacheDir: File) {
    val updateState by updateEngine.updateState.collectAsState()
    val scope = rememberCoroutineScope()

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Text("Update Engine", style = MaterialTheme.typography.headlineMedium)
        Text("State: $updateState")
        
        Button(onClick = { 
            scope.launch { 
                val manifest = updateEngine.checkForUpdate(mockAvailable = true) 
                if (manifest != null) {
                    // Simulate download and verification (valid)
                    updateEngine.downloadAndVerify(manifest, File(cacheDir, "mock_valid_file"))
                }
            }
        }) {
            Text("Simulate Valid Update")
        }
        
        Button(onClick = { 
            scope.launch { 
                val manifest = updateEngine.checkForUpdate(mockAvailable = true) 
                if (manifest != null) {
                    // Simulate download and verification (invalid hash)
                    updateEngine.downloadAndVerify(manifest, File(cacheDir, "mock_invalid_file"), simulateCorruption = true)
                }
            }
        }) {
            Text("Simulate Corrupt Update")
        }
        
        Button(
            onClick = { updateEngine.install() },
            enabled = updateState == UpdateState.READY_TO_INSTALL
        ) {
            Text("Install")
        }
    }
}
