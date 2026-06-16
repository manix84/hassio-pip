package com.hatvpip.receiver

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.background
import androidx.compose.foundation.focusable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.relocation.BringIntoViewRequester
import androidx.compose.foundation.relocation.bringIntoViewRequester
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private var compatibility by mutableStateOf<DeviceCompatibility?>(null)
    private var endpointInfo by mutableStateOf(ControlEndpointInfo())
    private var controlSnapshot by mutableStateOf(ControlRuntimeState.snapshot())
    private var discoverySnapshot by mutableStateOf(DiscoveryRuntimeState.snapshot())
    private var pairingSnapshot by mutableStateOf<PairingSnapshot?>(null)
    private var launcherVisible by mutableStateOf(true)
    private var remoteConfig by mutableStateOf(RemoteConnectionConfig("", ""))
    private var remoteSnapshot by mutableStateOf(RemoteConnectionRuntimeState.snapshot())
    private val controlSnapshotHandler = Handler(Looper.getMainLooper())
    private val controlSnapshotUpdater = object : Runnable {
        override fun run() {
            controlSnapshot = ControlRuntimeState.snapshot()
            discoverySnapshot = DiscoveryRuntimeState.snapshot()
            pairingSnapshot = PairingState.snapshot(this@MainActivity)
            launcherVisible = LauncherVisibility.isVisible(this@MainActivity)
            remoteSnapshot = RemoteConnectionRuntimeState.snapshot()
            controlSnapshotHandler.postDelayed(this, CONTROL_STATUS_REFRESH_MS)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        AppLog.activityCreated("MainActivity")
        refreshCompatibility()
        val controlServiceIntent = Intent(this, LocalControlService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(controlServiceIntent)
        } else {
            startService(controlServiceIntent)
        }

        setContent {
            HaTvTheme {
                compatibility?.let { currentCompatibility ->
                    MainScreen(
                        compatibility = currentCompatibility,
                        endpointInfo = endpointInfo,
                        controlSnapshot = controlSnapshot,
                        discoverySnapshot = discoverySnapshot,
                        pairingSnapshot = pairingSnapshot,
                        launcherVisible = launcherVisible,
                        remoteConfig = remoteConfig,
                        remoteSnapshot = remoteSnapshot,
                        onRequestOverlayPermission = ::openOverlayPermissionSettings,
                        onStopOverlay = ::stopOverlayFallback,
                        onResetPairing = ::resetPairing,
                        onSetLauncherVisible = ::updateLauncherVisibility,
                        onSaveRemoteConfig = ::saveRemoteConnectionConfig,
                        onClearRemoteConfig = ::clearRemoteConnectionConfig,
                        onPlayTestVideo = {
                            startActivity(
                                PlayerActivity.createShowIntent(
                                    context = this,
                                    command = ShowCommand.testVideo()
                                )
                            )
                        }
                    )
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        refreshCompatibility()
        controlSnapshotHandler.removeCallbacks(controlSnapshotUpdater)
        controlSnapshotHandler.post(controlSnapshotUpdater)
    }

    override fun onPause() {
        controlSnapshotHandler.removeCallbacks(controlSnapshotUpdater)
        super.onPause()
    }

    private fun refreshCompatibility() {
        compatibility = DeviceCompatibilityEvaluator.from(this)
        endpointInfo = ControlEndpointInfo()
        controlSnapshot = ControlRuntimeState.snapshot()
        discoverySnapshot = DiscoveryRuntimeState.snapshot()
        pairingSnapshot = PairingState.snapshot(this)
        launcherVisible = LauncherVisibility.isVisible(this)
        remoteConfig = RemoteConnectionSettings.load(this)
        remoteSnapshot = RemoteConnectionRuntimeState.snapshot()
    }

    private fun openOverlayPermissionSettings() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return

        val settingsIntent = Intent(
            Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
            Uri.parse("package:$packageName")
        )
        runCatching {
            startActivity(settingsIntent)
        }.onFailure { error ->
            AppLog.error("Unable to open overlay permission settings", error)
            startActivity(Intent(Settings.ACTION_SETTINGS))
        }
    }

    private fun stopOverlayFallback() {
        stopService(
            Intent(this, OverlayPlayerService::class.java)
                .setAction(OverlayPlayerService.ACTION_STOP)
        )
    }

    private fun resetPairing() {
        PairingState.reset(this)
        pairingSnapshot = PairingState.snapshot(this)
        AppLog.pairingEvent("pairing_reset", pairingSnapshot?.state?.wireName ?: "unknown")
        startService(
            Intent(this, LocalControlService::class.java)
                .setAction(LocalControlService.ACTION_PAIRING_CHANGED)
        )
    }

    private fun updateLauncherVisibility(visible: Boolean) {
        LauncherVisibility.setVisible(this, visible)
        launcherVisible = LauncherVisibility.isVisible(this)
        AppLog.lifecycleEvent(
            event = "launcher_visibility_changed",
            reason = if (launcherVisible) "visible" else "hidden"
        )
    }

    private fun saveRemoteConnectionConfig(config: RemoteConnectionConfig) {
        RemoteConnectionSettings.save(this, config)
        remoteConfig = RemoteConnectionSettings.load(this)
        AppLog.remoteConnectionEvent(
            event = "remote_settings_saved",
            state = if (remoteConfig.enabled) "enabled" else "disabled"
        )
        startService(
            Intent(this, LocalControlService::class.java)
                .setAction(LocalControlService.ACTION_REMOTE_SETTINGS_CHANGED)
        )
    }

    private fun clearRemoteConnectionConfig() {
        RemoteConnectionSettings.clear(this)
        remoteConfig = RemoteConnectionSettings.load(this)
        AppLog.remoteConnectionEvent(
            event = "remote_settings_cleared",
            state = RemoteConnectionStatus.Disabled.wireName
        )
        startService(
            Intent(this, LocalControlService::class.java)
                .setAction(LocalControlService.ACTION_REMOTE_SETTINGS_CHANGED)
        )
    }
}

@Composable
@OptIn(ExperimentalFoundationApi::class)
private fun MainScreen(
    compatibility: DeviceCompatibility,
    endpointInfo: ControlEndpointInfo,
    controlSnapshot: ControlServerSnapshot,
    discoverySnapshot: DiscoverySnapshot,
    pairingSnapshot: PairingSnapshot?,
    launcherVisible: Boolean,
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot,
    onRequestOverlayPermission: () -> Unit,
    onStopOverlay: () -> Unit,
    onResetPairing: () -> Unit,
    onSetLauncherVisible: (Boolean) -> Unit,
    onSaveRemoteConfig: (RemoteConnectionConfig) -> Unit,
    onClearRemoteConfig: () -> Unit,
    onPlayTestVideo: () -> Unit
) {
    val playButtonFocusRequester = remember { FocusRequester() }
    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        repeat(INITIAL_FOCUS_ATTEMPTS) {
            delay(INITIAL_FOCUS_RETRY_MS)
            if (playButtonFocusRequester.requestFocus()) return@LaunchedEffect
        }
    }

    val colors = MaterialTheme.colorScheme
    val backgroundGradient = Brush.verticalGradient(
        colors = listOf(
            colors.background,
            colors.primaryContainer.copy(alpha = 0.32f),
            colors.tertiaryContainer.copy(alpha = 0.24f),
            colors.background
        )
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(backgroundGradient)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(horizontal = 48.dp, vertical = 32.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp),
            horizontalAlignment = Alignment.Start
        ) {
            ReceiverHeader(
                pairingSnapshot = pairingSnapshot,
                remoteSnapshot = remoteSnapshot,
                launcherVisible = launcherVisible
            )

            PrimaryActions(
                compatibility = compatibility,
                playButtonFocusRequester = playButtonFocusRequester,
                onPlayTestVideo = onPlayTestVideo,
                onRequestOverlayPermission = onRequestOverlayPermission,
                onStopOverlay = onStopOverlay
            )

            StatusOverview(
                compatibility = compatibility,
                controlSnapshot = controlSnapshot,
                discoverySnapshot = discoverySnapshot,
                pairingSnapshot = pairingSnapshot,
                remoteSnapshot = remoteSnapshot
            )

            PairingStatusPanel(
                pairingSnapshot = pairingSnapshot,
                onResetPairing = onResetPairing
            )

            ReceiverManagementPanel(
                launcherVisible = launcherVisible,
                onSetLauncherVisible = onSetLauncherVisible
            )

            RemoteConnectionPanel(
                remoteConfig = remoteConfig,
                remoteSnapshot = remoteSnapshot,
                onSaveRemoteConfig = onSaveRemoteConfig,
                onClearRemoteConfig = onClearRemoteConfig
            )

            DiagnosticsPanel(
                endpointInfo = endpointInfo,
                controlSnapshot = controlSnapshot,
                discoverySnapshot = discoverySnapshot,
                compatibility = compatibility
            )
        }
    }
}

@Composable
private fun ReceiverHeader(
    pairingSnapshot: PairingSnapshot?,
    remoteSnapshot: RemoteConnectionSnapshot,
    launcherVisible: Boolean
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Text(
            text = "HA TV PiP Receiver",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 34.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Receiver is ${pairingSnapshot?.state?.wireName ?: "unknown"} | Remote ${remoteSnapshot.status.wireName} | Launcher ${if (launcherVisible) "visible" else "hidden"}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 17.sp
        )
    }
}

@Composable
private fun PrimaryActions(
    compatibility: DeviceCompatibility,
    playButtonFocusRequester: FocusRequester,
    onPlayTestVideo: () -> Unit,
    onRequestOverlayPermission: () -> Unit,
    onStopOverlay: () -> Unit
) {
    SectionCard(title = "PiP controls") {
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            TvActionButton(
                text = "Play Test Video",
                onClick = onPlayTestVideo,
                modifier = Modifier
                    .focusRequester(playButtonFocusRequester),
                minWidth = 220
            )
            if (compatibility.canRequestOverlayPermission) {
                TvActionButton(
                    text = "Overlay Settings",
                    onClick = onRequestOverlayPermission,
                    minWidth = 220
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            if (compatibility.overlayPermission == CompatibilityState.Granted) {
                TvActionButton(
                    text = "Stop Overlay",
                    onClick = onStopOverlay,
                    minWidth = 180
                )
            }
        }
    }
}

@Composable
private fun StatusOverview(
    compatibility: DeviceCompatibility,
    controlSnapshot: ControlServerSnapshot,
    discoverySnapshot: DiscoverySnapshot,
    pairingSnapshot: PairingSnapshot?,
    remoteSnapshot: RemoteConnectionSnapshot
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            SummaryCard(
                title = "Local",
                value = if (controlSnapshot.running) "Running" else "Stopped",
                detail = "Port ${controlSnapshot.port}"
            )
            SummaryCard(
                title = "Discovery",
                value = if (discoverySnapshot.running) "Advertising" else "Stopped",
                detail = discoverySnapshot.serviceType
            )
            SummaryCard(
                title = "Pairing",
                value = pairingSnapshot?.state?.wireName ?: "unknown",
                detail = pairingSnapshot?.pairedClientName ?: "No paired client"
            )
        }
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            SummaryCard(
                title = "Display",
                value = compatibility.recommendedMode.label,
                detail = "Overlay ${compatibility.overlayPermission.label}"
            )
            SummaryCard(
                title = "Remote",
                value = remoteSnapshot.status.wireName,
                detail = remoteSnapshot.lastError ?: "External receiver"
            )
        }
    }
}

@Composable
@OptIn(ExperimentalFoundationApi::class)
private fun RowScope.SummaryCard(
    title: String,
    value: String,
    detail: String
) {
    Card(
        modifier = Modifier
            .weight(1f)
            .height(112.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.72f)
        ),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.55f))
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text = title,
                color = MaterialTheme.colorScheme.primary,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = value,
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = detail,
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 13.sp
            )
        }
    }
}

@Composable
@OptIn(ExperimentalFoundationApi::class)
private fun SectionCard(
    title: String,
    focusableSection: Boolean = false,
    modifier: Modifier = Modifier.fillMaxWidth(),
    contentPadding: Int = 18,
    content: @Composable ColumnScope.() -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme
    val focusModifier = if (focusableSection) {
        Modifier
            .bringIntoViewOnFocus()
            .focusable(interactionSource = interactionSource)
    } else {
        Modifier
    }

    Card(
        modifier = modifier
            .then(focusModifier),
        colors = CardDefaults.cardColors(
            containerColor = colors.surface.copy(alpha = if (isFocused) 0.88f else 0.72f)
        ),
        border = BorderStroke(
            width = if (isFocused) 3.dp else 1.dp,
            color = if (isFocused) colors.tertiary else colors.outline.copy(alpha = 0.55f)
        )
    ) {
        Column(
            modifier = Modifier.padding(contentPadding.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = title,
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
            content()
        }
    }
}

@Composable
private fun RemoteConnectionPanel(
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot,
    onSaveRemoteConfig: (RemoteConnectionConfig) -> Unit,
    onClearRemoteConfig: () -> Unit
) {
    var homeAssistantUrl by remember(remoteConfig.homeAssistantUrl) {
        mutableStateOf(remoteConfig.homeAssistantUrl)
    }
    var accessToken by remember(remoteConfig.accessToken) {
        mutableStateOf(remoteConfig.accessToken)
    }

    SectionCard(title = "Remote receiver") {
        Text(
            text = "State: ${remoteSnapshot.status.wireName}",
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        remoteSnapshot.lastError?.let { error ->
            Text(
                text = "Last error: $error",
                color = MaterialTheme.colorScheme.error,
                fontSize = 15.sp
            )
        }
        Text(
            text = "Home Assistant can provision this for you. Manual setup remains available here for advanced troubleshooting. Remote mode connects outbound to your own Home Assistant instance; it is not a HA TV PiP cloud service.",
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 15.sp
        )
        OutlinedTextField(
            value = homeAssistantUrl,
            onValueChange = { homeAssistantUrl = it },
            modifier = Modifier
                .fillMaxWidth()
                .bringIntoViewOnFocus(),
            label = { Text("Home Assistant URL") },
            singleLine = true
        )
        OutlinedTextField(
            value = accessToken,
            onValueChange = { accessToken = it },
            modifier = Modifier
                .fillMaxWidth()
                .bringIntoViewOnFocus(),
            label = { Text("Long-lived access token") },
            visualTransformation = PasswordVisualTransformation(),
            singleLine = true
        )
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            TvActionButton(
                text = "Save Remote",
                onClick = {
                    onSaveRemoteConfig(
                        RemoteConnectionConfig(
                            homeAssistantUrl = homeAssistantUrl,
                            accessToken = accessToken
                        )
                    )
                },
                minWidth = 190
            )
            TvActionButton(
                text = "Clear Remote",
                onClick = onClearRemoteConfig,
                minWidth = 190
            )
        }
    }
}

@Composable
private fun ReceiverManagementPanel(
    launcherVisible: Boolean,
    onSetLauncherVisible: (Boolean) -> Unit
) {
    SectionCard(title = "Launcher controls") {
        Text(
            text = "Launcher icon: ${if (launcherVisible) "visible" else "hidden"}",
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        Text(
            text = "If hidden, Home Assistant can reopen this screen with the Open Launcher button. You can also recover from Android Settings > Apps > HA TV PiP.",
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 15.sp
        )
        TvActionButton(
            text = if (launcherVisible) "Hide Launcher Icon" else "Show Launcher Icon",
            onClick = { onSetLauncherVisible(!launcherVisible) },
            minWidth = 260
        )
    }
}

@Composable
@OptIn(ExperimentalFoundationApi::class)
private fun Modifier.bringIntoViewOnFocus(): Modifier {
    val bringIntoViewRequester = remember { BringIntoViewRequester() }
    val coroutineScope = rememberCoroutineScope()

    return bringIntoViewRequester(bringIntoViewRequester)
        .onFocusChanged { focusState ->
            if (focusState.isFocused) {
                coroutineScope.launch {
                    delay(80)
                    bringIntoViewRequester.bringIntoView()
                }
            }
        }
}

private const val CONTROL_STATUS_REFRESH_MS = 1_000L
private const val INITIAL_FOCUS_ATTEMPTS = 8
private const val INITIAL_FOCUS_RETRY_MS = 120L

@Composable
private fun PairingStatusPanel(
    pairingSnapshot: PairingSnapshot?,
    onResetPairing: () -> Unit
) {
    val snapshot = pairingSnapshot ?: return
    SectionCard(title = "Pairing") {
        Text(
            text = "State: ${snapshot.state.wireName}",
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        snapshot.pendingCode?.let { code ->
            Text(
                text = "Pairing code: $code",
                color = MaterialTheme.colorScheme.tertiary,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
        }
        snapshot.pendingClientName?.let { clientName ->
            Text(
                text = "Waiting for: $clientName",
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 15.sp
            )
        }
        snapshot.pairedClientName?.let { clientName ->
            Text(
                text = "Paired with: $clientName",
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 15.sp
            )
        }
        if (snapshot.state == PairingStatus.Paired) {
            TvActionButton(
                text = "Reset Pairing",
                onClick = onResetPairing,
                minWidth = 190
            )
        }
    }
}

@Composable
private fun TvActionButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    minWidth: Int
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme

    Button(
        onClick = onClick,
        modifier = modifier
            .bringIntoViewOnFocus()
            .widthIn(min = minWidth.dp),
        interactionSource = interactionSource,
        border = BorderStroke(
            width = if (isFocused) 4.dp else 1.dp,
            color = if (isFocused) colors.tertiary else colors.outline
        ),
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isFocused) colors.tertiary else colors.primary,
            contentColor = if (isFocused) colors.onTertiary else colors.onPrimary
        )
    ) {
        Text(
            text = text,
            fontSize = 18.sp,
            fontWeight = if (isFocused) FontWeight.Bold else FontWeight.Medium
        )
    }
}

@Composable
private fun DiagnosticsPanel(
    endpointInfo: ControlEndpointInfo,
    controlSnapshot: ControlServerSnapshot,
    discoverySnapshot: DiscoverySnapshot,
    compatibility: DeviceCompatibility
) {
    SectionCard(
        title = "Diagnostics",
        focusableSection = true
    ) {
        val lastRequest = controlSnapshot.lastRequest
        val runningLabel = if (controlSnapshot.running) "running" else "stopped"

        DiagnosticRow(label = "Endpoint", value = endpointInfo.displayAddress)
        DiagnosticRow(
            label = "Local control",
            value = "State: $runningLabel | Uptime: ${
                controlSnapshot.uptimeSeconds(System.currentTimeMillis())
            }s | Requests: ${controlSnapshot.requestCount}"
        )
        if (lastRequest != null) {
            DiagnosticRow(
                label = "Last request",
                value = "${lastRequest.method} ${lastRequest.path} -> ${lastRequest.status}"
            )
        }
        DiagnosticRow(
            label = "Discovery",
            value = "${if (discoverySnapshot.running) "advertising" else "stopped"} | ${discoverySnapshot.serviceType}"
        )
        discoverySnapshot.serviceName?.let { serviceName ->
            DiagnosticRow(label = "Service", value = serviceName)
        }
        discoverySnapshot.errorMessage?.let { error ->
            Text(
                text = "Discovery error: $error",
                color = MaterialTheme.colorScheme.error,
                fontSize = 15.sp
            )
        }
        DiagnosticRow(label = "Android", value = compatibility.androidVersionLabel)
        DiagnosticRow(label = "Native PiP", value = compatibility.nativePictureInPicture.label)
        DiagnosticRow(label = "Compatibility", value = compatibility.statusText)
    }
}

@Composable
private fun DiagnosticRow(label: String, value: String) {
    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
        Text(
            modifier = Modifier.width(130.dp),
            text = label,
            color = MaterialTheme.colorScheme.primary,
            fontSize = 15.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = value,
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 15.sp
        )
    }
}
