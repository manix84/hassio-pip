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
import androidx.compose.foundation.Image
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
import androidx.compose.ui.focus.focusProperties
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
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
            remoteConfig = RemoteConnectionSettings.load(this@MainActivity)
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
                                    command = ShowCommand.testVideo(getString(R.string.test_video_title))
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
    val pipSectionFocusRequester = remember { FocusRequester() }
    val playButtonFocusRequester = remember { FocusRequester() }
    val overlaySettingsFocusRequester = remember { FocusRequester() }
    val stopOverlayFocusRequester = remember { FocusRequester() }
    val setupSectionFocusRequester = remember { FocusRequester() }
    val statusSectionFocusRequester = remember { FocusRequester() }
    val pairingSectionFocusRequester = remember { FocusRequester() }
    val resetPairingFocusRequester = remember { FocusRequester() }
    val launcherSectionFocusRequester = remember { FocusRequester() }
    val launcherButtonFocusRequester = remember { FocusRequester() }
    val remoteSectionFocusRequester = remember { FocusRequester() }
    val remoteClearFocusRequester = remember { FocusRequester() }
    val remoteAdvancedFocusRequester = remember { FocusRequester() }
    val remoteSaveFocusRequester = remember { FocusRequester() }
    val troubleshootingSectionFocusRequester = remember { FocusRequester() }
    val diagnosticsSectionFocusRequester = remember { FocusRequester() }
    val scrollState = rememberScrollState()
    val primaryLastButtonFocusRequester = when {
        compatibility.overlayPermission == CompatibilityState.Granted -> stopOverlayFocusRequester
        compatibility.canRequestOverlayPermission -> overlaySettingsFocusRequester
        else -> playButtonFocusRequester
    }
    val statusDownFocusRequester = if (pairingSnapshot != null) {
        pairingSectionFocusRequester
    } else {
        launcherSectionFocusRequester
    }
    val launcherUpFocusRequester = when {
        pairingSnapshot?.state == PairingStatus.Paired -> resetPairingFocusRequester
        pairingSnapshot != null -> pairingSectionFocusRequester
        else -> statusSectionFocusRequester
    }

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
                remoteConfig = remoteConfig,
                remoteSnapshot = remoteSnapshot,
                launcherVisible = launcherVisible
            )

            PrimaryActions(
                compatibility = compatibility,
                sectionFocusRequester = pipSectionFocusRequester,
                playButtonFocusRequester = playButtonFocusRequester,
                overlaySettingsFocusRequester = overlaySettingsFocusRequester,
                stopOverlayFocusRequester = stopOverlayFocusRequester,
                downFromSectionFocusRequester = playButtonFocusRequester,
                upFromPlayFocusRequester = pipSectionFocusRequester,
                downFromPlayFocusRequester = if (compatibility.canRequestOverlayPermission) {
                    overlaySettingsFocusRequester
                } else if (compatibility.overlayPermission == CompatibilityState.Granted) {
                    stopOverlayFocusRequester
                } else {
                    setupSectionFocusRequester
                },
                downFromOverlaySettingsFocusRequester = if (compatibility.overlayPermission == CompatibilityState.Granted) {
                    stopOverlayFocusRequester
                } else {
                    setupSectionFocusRequester
                },
                upFromStopOverlayFocusRequester = if (compatibility.canRequestOverlayPermission) {
                    overlaySettingsFocusRequester
                } else {
                    playButtonFocusRequester
                },
                downFromStopOverlayFocusRequester = setupSectionFocusRequester,
                onPlayTestVideo = onPlayTestVideo,
                onRequestOverlayPermission = onRequestOverlayPermission,
                onStopOverlay = onStopOverlay
            )

            SetupGuidePanel(
                sectionFocusRequester = setupSectionFocusRequester,
                upFocusRequester = primaryLastButtonFocusRequester,
                downFocusRequester = statusSectionFocusRequester
            )

            StatusOverview(
                compatibility = compatibility,
                controlSnapshot = controlSnapshot,
                discoverySnapshot = discoverySnapshot,
                pairingSnapshot = pairingSnapshot,
                remoteConfig = remoteConfig,
                remoteSnapshot = remoteSnapshot,
                sectionFocusRequester = statusSectionFocusRequester,
                upFocusRequester = setupSectionFocusRequester,
                downFocusRequester = statusDownFocusRequester
            )

            PairingStatusPanel(
                pairingSnapshot = pairingSnapshot,
                sectionFocusRequester = pairingSectionFocusRequester,
                resetPairingFocusRequester = resetPairingFocusRequester,
                upFocusRequester = statusSectionFocusRequester,
                downFocusRequester = launcherSectionFocusRequester,
                onResetPairing = onResetPairing
            )

            ReceiverManagementPanel(
                launcherVisible = launcherVisible,
                sectionFocusRequester = launcherSectionFocusRequester,
                launcherButtonFocusRequester = launcherButtonFocusRequester,
                upFocusRequester = launcherUpFocusRequester,
                downFocusRequester = remoteSectionFocusRequester,
                onSetLauncherVisible = onSetLauncherVisible
            )

            RemoteConnectionPanel(
                remoteConfig = remoteConfig,
                remoteSnapshot = remoteSnapshot,
                sectionFocusRequester = remoteSectionFocusRequester,
                clearFocusRequester = remoteClearFocusRequester,
                advancedFocusRequester = remoteAdvancedFocusRequester,
                saveFocusRequester = remoteSaveFocusRequester,
                upFocusRequester = launcherButtonFocusRequester,
                downFocusRequester = troubleshootingSectionFocusRequester,
                onSaveRemoteConfig = onSaveRemoteConfig,
                onClearRemoteConfig = onClearRemoteConfig
            )

            TroubleshootingPanel(
                sectionFocusRequester = troubleshootingSectionFocusRequester,
                upFocusRequester = remoteAdvancedFocusRequester,
                downFocusRequester = diagnosticsSectionFocusRequester
            )

            DiagnosticsPanel(
                endpointInfo = endpointInfo,
                controlSnapshot = controlSnapshot,
                discoverySnapshot = discoverySnapshot,
                compatibility = compatibility,
                sectionFocusRequester = diagnosticsSectionFocusRequester,
                upFocusRequester = troubleshootingSectionFocusRequester
            )
        }
    }
}

@Composable
private fun SetupGuidePanel(
    sectionFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester
) {
    SectionCard(
        title = stringResource(R.string.section_setup_guide),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = downFocusRequester
    ) {
        GuidanceText(text = stringResource(R.string.setup_step_pair))
        GuidanceText(text = stringResource(R.string.setup_step_overlay))
        GuidanceText(text = stringResource(R.string.setup_step_remote))
    }
}

@Composable
private fun TroubleshootingPanel(
    sectionFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester
) {
    SectionCard(
        title = stringResource(R.string.section_troubleshooting),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = downFocusRequester
    ) {
        GuidanceText(text = stringResource(R.string.troubleshooting_discovery))
        GuidanceText(text = stringResource(R.string.troubleshooting_remote))
        GuidanceText(text = stringResource(R.string.troubleshooting_launcher))
    }
}

@Composable
private fun GuidanceText(text: String) {
    Text(
        text = text,
        color = MaterialTheme.colorScheme.onSurface,
        fontSize = 15.sp
    )
}

@Composable
private fun ReceiverHeader(
    pairingSnapshot: PairingSnapshot?,
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot,
    launcherVisible: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = stringResource(R.string.main_title),
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 34.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = stringResource(
                    R.string.main_status_summary,
                    pairingSnapshot?.state?.wireName ?: stringResource(R.string.status_unknown),
                    remoteHeaderStatus(remoteConfig, remoteSnapshot),
                    if (launcherVisible) {
                        stringResource(R.string.status_visible)
                    } else {
                        stringResource(R.string.status_hidden)
                    }
                ),
                color = MaterialTheme.colorScheme.onBackground,
                fontSize = 17.sp
            )
        }
        Image(
            painter = painterResource(R.mipmap.ic_launcher_foreground),
            contentDescription = stringResource(R.string.app_name),
            modifier = Modifier
                .width(92.dp)
                .height(92.dp)
        )
    }
}

@Composable
private fun PrimaryActions(
    compatibility: DeviceCompatibility,
    sectionFocusRequester: FocusRequester,
    playButtonFocusRequester: FocusRequester,
    overlaySettingsFocusRequester: FocusRequester,
    stopOverlayFocusRequester: FocusRequester,
    downFromSectionFocusRequester: FocusRequester,
    upFromPlayFocusRequester: FocusRequester,
    downFromPlayFocusRequester: FocusRequester,
    downFromOverlaySettingsFocusRequester: FocusRequester,
    upFromStopOverlayFocusRequester: FocusRequester,
    downFromStopOverlayFocusRequester: FocusRequester,
    onPlayTestVideo: () -> Unit,
    onRequestOverlayPermission: () -> Unit,
    onStopOverlay: () -> Unit
) {
    SectionCard(
        title = stringResource(R.string.section_pip_controls),
        focusRequester = sectionFocusRequester,
        downFocusRequester = downFromSectionFocusRequester
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            TvActionButton(
                text = stringResource(R.string.action_play_test_video),
                onClick = onPlayTestVideo,
                focusRequester = playButtonFocusRequester,
                upFocusRequester = upFromPlayFocusRequester,
                downFocusRequester = downFromPlayFocusRequester,
                minWidth = 220
            )
            if (compatibility.canRequestOverlayPermission) {
                TvActionButton(
                    text = stringResource(R.string.action_overlay_settings),
                    onClick = onRequestOverlayPermission,
                    focusRequester = overlaySettingsFocusRequester,
                    upFocusRequester = playButtonFocusRequester,
                    downFocusRequester = downFromOverlaySettingsFocusRequester,
                    minWidth = 220
                )
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            if (compatibility.overlayPermission == CompatibilityState.Granted) {
                TvActionButton(
                    text = stringResource(R.string.action_stop_overlay),
                    onClick = onStopOverlay,
                    focusRequester = stopOverlayFocusRequester,
                    upFocusRequester = upFromStopOverlayFocusRequester,
                    downFocusRequester = downFromStopOverlayFocusRequester,
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
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot,
    sectionFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester
) {
    SectionCard(
        title = stringResource(R.string.section_status_overview),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = downFocusRequester
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                SummaryCard(
                    title = stringResource(R.string.summary_local_title),
                    value = if (controlSnapshot.running) {
                        stringResource(R.string.status_running)
                    } else {
                        stringResource(R.string.status_stopped)
                    },
                    detail = stringResource(R.string.summary_port, controlSnapshot.port)
                )
                SummaryCard(
                    title = stringResource(R.string.summary_discovery_title),
                    value = if (discoverySnapshot.running) {
                        stringResource(R.string.status_advertising)
                    } else {
                        stringResource(R.string.status_stopped)
                    },
                    detail = discoverySnapshot.serviceType
                )
                SummaryCard(
                    title = stringResource(R.string.summary_pairing_title),
                    value = pairingSnapshot?.state?.wireName ?: stringResource(R.string.status_unknown),
                    detail = pairingSnapshot?.pairedClientName ?: stringResource(R.string.summary_no_paired_client)
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                SummaryCard(
                    title = stringResource(R.string.summary_display_title),
                    value = compatibility.recommendedMode.localizedLabel(),
                    detail = stringResource(R.string.summary_overlay_state, compatibility.overlayPermission.localizedLabel())
                )
                SummaryCard(
                    title = stringResource(R.string.summary_remote_title),
                    value = remoteSummaryValue(remoteConfig, remoteSnapshot),
                    detail = remoteSummaryDetail(remoteConfig, remoteSnapshot)
                )
            }
        }
    }
}

@Composable
private fun remoteHeaderStatus(
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot
): String = when {
    remoteSnapshot.status == RemoteConnectionStatus.Connected -> stringResource(R.string.status_connected_lower)
    remoteConfig.enabled -> stringResource(R.string.status_configured_with_state, remoteSnapshot.status.wireName)
    else -> stringResource(R.string.status_not_configured_lower)
}

@Composable
private fun remoteSummaryValue(
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot
): String = when {
    remoteSnapshot.status == RemoteConnectionStatus.Connected -> stringResource(R.string.status_connected)
    remoteConfig.enabled -> stringResource(R.string.status_configured)
    else -> stringResource(R.string.status_not_configured)
}

@Composable
private fun remoteSummaryDetail(
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot
): String = when {
    remoteSnapshot.lastError != null -> remoteSnapshot.lastError
    remoteConfig.enabled -> stringResource(R.string.remote_setup_saved)
    else -> stringResource(R.string.remote_use_ha_to_sync)
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
    modifier: Modifier = Modifier.fillMaxWidth(),
    focusRequester: FocusRequester? = null,
    upFocusRequester: FocusRequester? = null,
    downFocusRequester: FocusRequester? = null,
    contentPadding: Int = 18,
    content: @Composable ColumnScope.() -> Unit
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme

    Card(
        modifier = modifier
            .then(focusRequester?.let { Modifier.focusRequester(it) } ?: Modifier)
            .focusProperties {
                upFocusRequester?.let { up = it }
                downFocusRequester?.let { down = it }
            }
            .bringIntoViewOnFocus()
            .focusable(interactionSource = interactionSource),
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
    sectionFocusRequester: FocusRequester,
    clearFocusRequester: FocusRequester,
    advancedFocusRequester: FocusRequester,
    saveFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester,
    onSaveRemoteConfig: (RemoteConnectionConfig) -> Unit,
    onClearRemoteConfig: () -> Unit
) {
    var homeAssistantUrl by remember(remoteConfig.homeAssistantUrl) {
        mutableStateOf(remoteConfig.homeAssistantUrl)
    }
    var accessToken by remember(remoteConfig.accessToken) {
        mutableStateOf(remoteConfig.accessToken)
    }
    var showManualSetup by remember { mutableStateOf(false) }

    SectionCard(
        title = stringResource(R.string.section_remote_receiver),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = if (remoteConfig.enabled) {
            clearFocusRequester
        } else {
            advancedFocusRequester
        }
    ) {
        RemoteReceiverStatusBanner(
            remoteConfig = remoteConfig,
            remoteSnapshot = remoteSnapshot
        )
        Text(
            text = stringResource(R.string.state_value, remoteSnapshot.status.wireName),
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        remoteSnapshot.lastError?.let { error ->
            Text(
                text = stringResource(R.string.last_error_value, error),
                color = MaterialTheme.colorScheme.error,
                fontSize = 15.sp
            )
        }
        Text(
            text = stringResource(R.string.remote_receiver_help),
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 15.sp
        )
        if (remoteConfig.enabled) {
            RemoteConfigDetailRow(
                label = stringResource(R.string.label_home_assistant_url),
                value = remoteConfig.homeAssistantUrl
            )
            RemoteConfigDetailRow(
                label = stringResource(R.string.label_access_token),
                value = stringResource(R.string.status_saved)
            )
            TvActionButton(
                text = stringResource(R.string.action_clear_remote),
                onClick = onClearRemoteConfig,
                focusRequester = clearFocusRequester,
                upFocusRequester = sectionFocusRequester,
                downFocusRequester = advancedFocusRequester,
                minWidth = 190
            )
        }
        TvActionButton(
            text = if (showManualSetup) {
                stringResource(R.string.action_hide_manual_remote_setup)
            } else {
                stringResource(R.string.action_show_manual_remote_setup)
            },
            onClick = { showManualSetup = !showManualSetup },
            focusRequester = advancedFocusRequester,
            upFocusRequester = if (remoteConfig.enabled) {
                clearFocusRequester
            } else {
                sectionFocusRequester
            },
            downFocusRequester = if (showManualSetup) {
                null
            } else {
                downFocusRequester
            },
            minWidth = 290
        )
        if (showManualSetup) {
            OutlinedTextField(
                value = homeAssistantUrl,
                onValueChange = { homeAssistantUrl = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .bringIntoViewOnFocus(),
                label = { Text(stringResource(R.string.label_home_assistant_url)) },
                singleLine = true
            )
            OutlinedTextField(
                value = accessToken,
                onValueChange = { accessToken = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .bringIntoViewOnFocus(),
                label = { Text(stringResource(R.string.label_long_lived_access_token)) },
                visualTransformation = PasswordVisualTransformation(),
                singleLine = true
            )
            TvActionButton(
                text = stringResource(R.string.action_save_remote),
                onClick = {
                    onSaveRemoteConfig(
                        RemoteConnectionConfig(
                            homeAssistantUrl = homeAssistantUrl,
                            accessToken = accessToken
                        )
                    )
                },
                focusRequester = saveFocusRequester,
                downFocusRequester = downFocusRequester,
                minWidth = 190
            )
        }
    }
}

@Composable
private fun RemoteReceiverStatusBanner(
    remoteConfig: RemoteConnectionConfig,
    remoteSnapshot: RemoteConnectionSnapshot
) {
    val colors = MaterialTheme.colorScheme
    val provisioned = remoteConfig.enabled
    val connected = remoteSnapshot.status == RemoteConnectionStatus.Connected
    val containerColor = when {
        connected -> colors.primaryContainer
        provisioned -> colors.secondaryContainer
        else -> colors.surfaceVariant
    }
    val contentColor = when {
        connected -> colors.onPrimaryContainer
        provisioned -> colors.onSecondaryContainer
        else -> colors.onSurfaceVariant
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = containerColor.copy(alpha = 0.92f)),
        border = BorderStroke(1.dp, contentColor.copy(alpha = 0.28f))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text = if (provisioned) {
                        stringResource(R.string.remote_details_saved)
                    } else {
                        stringResource(R.string.remote_details_not_configured)
                    },
                    color = contentColor,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = if (provisioned) {
                        stringResource(R.string.remote_details_saved_description)
                    } else {
                        stringResource(R.string.remote_details_not_configured_description)
                    },
                    color = contentColor,
                    fontSize = 14.sp
                )
            }
            StatusPill(
                text = remoteSummaryValue(remoteConfig, remoteSnapshot),
                containerColor = contentColor.copy(alpha = 0.16f),
                contentColor = contentColor
            )
        }
    }
}

@Composable
private fun RemoteConfigDetailRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            modifier = Modifier.width(190.dp),
            color = MaterialTheme.colorScheme.primary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = value,
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 14.sp
        )
    }
}

@Composable
private fun StatusPill(
    text: String,
    containerColor: Color,
    contentColor: Color
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = containerColor),
        border = BorderStroke(1.dp, contentColor.copy(alpha = 0.32f))
    ) {
        Text(
            text = text,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
            color = contentColor,
            fontSize = 13.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
private fun ReceiverManagementPanel(
    launcherVisible: Boolean,
    sectionFocusRequester: FocusRequester,
    launcherButtonFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester,
    onSetLauncherVisible: (Boolean) -> Unit
) {
    SectionCard(
        title = stringResource(R.string.section_launcher_controls),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = launcherButtonFocusRequester
    ) {
        Text(
            text = stringResource(
                R.string.launcher_icon_value,
                if (launcherVisible) stringResource(R.string.status_visible) else stringResource(R.string.status_hidden)
            ),
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        Text(
            text = stringResource(R.string.launcher_help),
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 15.sp
        )
        TvActionButton(
            text = if (launcherVisible) {
                stringResource(R.string.action_hide_launcher_icon)
            } else {
                stringResource(R.string.action_show_launcher_icon)
            },
            onClick = { onSetLauncherVisible(!launcherVisible) },
            focusRequester = launcherButtonFocusRequester,
            upFocusRequester = sectionFocusRequester,
            downFocusRequester = downFocusRequester,
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
    sectionFocusRequester: FocusRequester,
    resetPairingFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester,
    downFocusRequester: FocusRequester,
    onResetPairing: () -> Unit
) {
    val snapshot = pairingSnapshot ?: return
    SectionCard(
        title = stringResource(R.string.section_pairing),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester,
        downFocusRequester = if (snapshot.state == PairingStatus.Paired) {
            resetPairingFocusRequester
        } else {
            downFocusRequester
        }
    ) {
        Text(
            text = stringResource(R.string.state_value, snapshot.state.wireName),
            color = MaterialTheme.colorScheme.onSurface,
            fontSize = 16.sp
        )
        snapshot.pendingCode?.let { code ->
            Text(
                text = stringResource(R.string.pairing_code_value, code),
                color = MaterialTheme.colorScheme.tertiary,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold
            )
        }
        snapshot.pendingClientName?.let { clientName ->
            Text(
                text = stringResource(R.string.waiting_for_value, clientName),
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 15.sp
            )
        }
        snapshot.pairedClientName?.let { clientName ->
            Text(
                text = stringResource(R.string.paired_with_value, clientName),
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 15.sp
            )
        }
        if (snapshot.state == PairingStatus.Paired) {
            TvActionButton(
                text = stringResource(R.string.action_reset_pairing),
                onClick = onResetPairing,
                focusRequester = resetPairingFocusRequester,
                upFocusRequester = sectionFocusRequester,
                downFocusRequester = downFocusRequester,
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
    focusRequester: FocusRequester? = null,
    upFocusRequester: FocusRequester? = null,
    downFocusRequester: FocusRequester? = null,
    minWidth: Int
) {
    val interactionSource = remember { MutableInteractionSource() }
    val isFocused by interactionSource.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme

    Button(
        onClick = onClick,
        modifier = modifier
            .then(focusRequester?.let { Modifier.focusRequester(it) } ?: Modifier)
            .focusProperties {
                upFocusRequester?.let { up = it }
                downFocusRequester?.let { down = it }
            }
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
    compatibility: DeviceCompatibility,
    sectionFocusRequester: FocusRequester,
    upFocusRequester: FocusRequester
) {
    SectionCard(
        title = stringResource(R.string.section_diagnostics),
        focusRequester = sectionFocusRequester,
        upFocusRequester = upFocusRequester
    ) {
        val lastRequest = controlSnapshot.lastRequest
        val runningLabel = if (controlSnapshot.running) {
            stringResource(R.string.status_running_lower)
        } else {
            stringResource(R.string.status_stopped_lower)
        }

        DiagnosticRow(label = stringResource(R.string.diagnostics_endpoint), value = endpointInfo.displayAddress)
        DiagnosticRow(
            label = stringResource(R.string.diagnostics_local_control),
            value = stringResource(
                R.string.diagnostics_local_control_value,
                runningLabel,
                controlSnapshot.uptimeSeconds(System.currentTimeMillis()),
                controlSnapshot.requestCount
            )
        )
        if (lastRequest != null) {
            DiagnosticRow(
                label = stringResource(R.string.diagnostics_last_request),
                value = stringResource(
                    R.string.diagnostics_last_request_value,
                    lastRequest.method,
                    lastRequest.path,
                    lastRequest.status
                )
            )
        }
        DiagnosticRow(
            label = stringResource(R.string.diagnostics_discovery),
            value = stringResource(
                R.string.diagnostics_discovery_value,
                if (discoverySnapshot.running) {
                    stringResource(R.string.status_advertising_lower)
                } else {
                    stringResource(R.string.status_stopped_lower)
                },
                discoverySnapshot.serviceType
            )
        )
        discoverySnapshot.serviceName?.let { serviceName ->
            DiagnosticRow(label = stringResource(R.string.diagnostics_service), value = serviceName)
        }
        discoverySnapshot.errorMessage?.let { error ->
            Text(
                text = stringResource(R.string.discovery_error_value, error),
                color = MaterialTheme.colorScheme.error,
                fontSize = 15.sp
            )
        }
        DiagnosticRow(label = stringResource(R.string.diagnostics_android), value = compatibility.androidVersionLabel)
        DiagnosticRow(label = stringResource(R.string.diagnostics_native_pip), value = compatibility.nativePictureInPicture.localizedLabel())
        DiagnosticRow(label = stringResource(R.string.diagnostics_compatibility), value = compatibility.localizedStatusText())
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
