package io.eidos.zerolayer.ui.components

import android.content.Context
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import io.eidos.zerolayer.ui.theme.EidosCyan
import kotlinx.coroutines.delay

@Composable
fun FirstTimeTooltip(
    prefKey: String,
    text: String,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val prefs = remember { context.getSharedPreferences("eidos_tutorial_prefs", Context.MODE_PRIVATE) }
    var alreadyShown by remember { mutableStateOf(prefs.getBoolean(prefKey, false)) }
    var visible by remember { mutableStateOf(false) }

    LaunchedEffect(alreadyShown) {
        if (!alreadyShown) {
            delay(500L)
            visible = true
        }
    }

    AnimatedVisibility(
        visible = visible && !alreadyShown,
        enter = fadeIn() + expandVertically(),
        exit = fadeOut() + shrinkVertically(),
        modifier = modifier
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(CutCornerShape(8.dp))
                .background(Color(0xFF0F1420))
                .border(1.5.dp, Color(0xFFFFD700), CutCornerShape(8.dp))
                .padding(12.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Top,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = "💡",
                    fontSize = 16.sp
                )
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "// СОВЕТ ЕВЫ-09",
                        color = Color(0xFFFFD700),
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = text,
                        color = Color.White,
                        fontSize = 11.5.sp,
                        lineHeight = 16.sp,
                        fontFamily = FontFamily.SansSerif
                    )
                }
                IconButton(
                    onClick = {
                        prefs.edit().putBoolean(prefKey, true).apply()
                        alreadyShown = true
                        visible = false
                    },
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Dismiss",
                        tint = Color.LightGray,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }
    }
}
