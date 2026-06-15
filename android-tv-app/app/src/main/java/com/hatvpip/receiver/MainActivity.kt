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
import androidx.compose.foundation.background
import androidx.compose.foundation.focusable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class MainActivity : ComponentActivity() {
    private var compatibility by mutableStateOf<DeviceCompatibility?>(null)
    private var endpointInfo by mutableStateOf(ControlEndpointInfo())
    private var controlSnapshot by mutableStateOf(ControlRuntimeState.snapshot())
    private var discoverySnapshot by mutableStateOf(DiscoveryRuntimeState.snapshot())
    private val controlSnapshotHandler = Handler(Looper.getMainLooper())
    private val controlSnapshotUpdater = object : Runnable {
        override fun run() {
            controlSnapshot = ControlRuntimeState.snapshot()
            discoverySnapshot = DiscoveryRuntimeState.snapshot()
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
                        onRequestOverlayPermission = ::openOverlayPermissionSettings,
                        onStopOverlay = ::stopOverlayFallback,
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
}

@Composable
private fun MainScreen(
    compatibility: DeviceCompatibility,
    endpointInfo: ControlEndpointInfo,
    controlSnapshot: ControlServerSnapshot,
    discoverySnapshot: DiscoverySnapshot,
    onRequestOverlayPermission: () -> Unit,
    onStopOverlay: () -> Unit,
    onPlayTestVideo: () -> Unit
) {
    val playButtonFocusRequester = remember { FocusRequester() }
    val scrollState = rememberScrollState()

    LaunchedEffect(Unit) {
        playButtonFocusRequester.requestFocus()
    }

    Surface(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(horizontal = 56.dp, vertical = 36.dp),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = "HA TV PiP Receiver",
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 34.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = "Stage 2 MVP: local HTTP control on port ${LocalControlServer.DEFAULT_PORT}, test HLS playback, and TV-safe display modes.",
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 18.sp
            )
            Spacer(modifier = Modifier.height(20.dp))
            CompatibilityStatus(compatibility = compatibility)
            Spacer(modifier = Modifier.height(18.dp))
            ControlEndpointStatus(
                endpointInfo = endpointInfo,
                controlSnapshot = controlSnapshot,
                discoverySnapshot = discoverySnapshot
            )
            Spacer(modifier = Modifier.height(24.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                TvActionButton(
                    text = "Play Test Video",
                    onClick = onPlayTestVideo,
                    modifier = Modifier
                        .focusRequester(playButtonFocusRequester)
                        // Explicit focusability makes D-pad startup focus predictable on TV launchers.
                        .focusable(),
                    minWidth = 220
                )
                if (compatibility.canRequestOverlayPermission) {
                    TvActionButton(
                        text = "Open Overlay Settings",
                        onClick = onRequestOverlayPermission,
                        minWidth = 260
                    )
                }
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
}

private const val CONTROL_STATUS_REFRESH_MS = 1_000L

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
        modifier = modifier.widthIn(min = minWidth.dp),
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
private fun ControlEndpointStatus(
    endpointInfo: ControlEndpointInfo,
    controlSnapshot: ControlServerSnapshot,
    discoverySnapshot: DiscoverySnapshot
) {
    Column(
        modifier = Modifier.widthIn(max = 760.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        val lastRequest = controlSnapshot.lastRequest
        val runningLabel = if (controlSnapshot.running) "running" else "stopped"

        Text(
            text = "Local control endpoint",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = endpointInfo.displayAddress,
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp
        )
        Text(
            text = "State: $runningLabel | Uptime: ${
                controlSnapshot.uptimeSeconds(System.currentTimeMillis())
            }s | Requests: ${controlSnapshot.requestCount}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 15.sp
        )
        if (lastRequest != null) {
            Text(
                text = "Last: ${lastRequest.method} ${lastRequest.path} -> ${lastRequest.status}",
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 15.sp
            )
        }
        Text(
            text = "Discovery: ${if (discoverySnapshot.running) "advertising" else "stopped"} | ${discoverySnapshot.serviceType}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 15.sp
        )
        discoverySnapshot.serviceName?.let { serviceName ->
            Text(
                text = "Service: $serviceName",
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 15.sp
            )
        }
        discoverySnapshot.errorMessage?.let { error ->
            Text(
                text = "Discovery error: $error",
                color = MaterialTheme.colorScheme.error,
                fontSize = 15.sp
            )
        }
    }
}

@Composable
private fun CompatibilityStatus(compatibility: DeviceCompatibility) {
    Column(
        modifier = Modifier.widthIn(max = 760.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "Device compatibility",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = compatibility.androidVersionLabel,
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp
        )
        Text(
            text = "Native PiP: ${compatibility.nativePictureInPicture.label}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp
        )
        Text(
            text = "Overlay permission: ${compatibility.overlayPermission.label}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp
        )
        Text(
            text = "Recommended mode: ${compatibility.recommendedMode.label}",
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = compatibility.statusText,
            color = MaterialTheme.colorScheme.onBackground,
            fontSize = 16.sp
        )
    }
}
