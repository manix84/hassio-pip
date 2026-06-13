package com.hatvpip.receiver

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val DarkColors: ColorScheme = darkColorScheme(
    primary = Color(0xFF4FB7FF),
    onPrimary = Color(0xFF001E2F),
    background = Color(0xFF101820),
    onBackground = Color(0xFFF4F7FA),
    surface = Color(0xFF17232D),
    onSurface = Color(0xFFF4F7FA)
)

private val LightColors: ColorScheme = lightColorScheme(
    primary = Color(0xFF006A9E),
    onPrimary = Color.White,
    background = Color(0xFFF4F7FA),
    onBackground = Color(0xFF101820),
    surface = Color.White,
    onSurface = Color(0xFF101820)
)

@Composable
fun HaTvTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        content = content
    )
}
