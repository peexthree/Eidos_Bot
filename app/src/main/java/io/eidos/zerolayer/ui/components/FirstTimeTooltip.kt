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
        val tooltipShape = CutCornerShape(topStart = 10.dp, bottomEnd = 10.dp, topEnd = 2.dp, bottomStart = 2.dp)
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(tooltipShape)
                .background(
                    androidx.compose.ui.graphics.Brush.verticalGradient(
                        listOf(
                            Color(0xF2142033),
                            Color(0xF50B1320),
                            Color(0xFA05080E)
                        )
                    )
                )
                .border(1.5.dp, Color(0xFFFFD700).copy(alpha = 0.85f), tooltipShape)
        ) {
            // Studio Glass Top Reflection Sheen
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(1.5.dp)
                    .background(
                        androidx.compose.ui.graphics.Brush.horizontalGradient(
                            listOf(
                                Color.Transparent,
                                Color.White.copy(alpha = 0.4f),
                                Color(0xFFFFD700),
                                Color.Transparent
                            )
                        )
                    )
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalAlignment = Alignment.Top,
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(28.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0x33FFD700))
                        .border(1.dp, Color(0xFFFFD700), CutCornerShape(4.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "💡",
                        fontSize = 14.sp
                    )
                }
                Column(modifier = Modifier.weight(1f)) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(5.dp)
                                .clip(androidx.compose.foundation.shape.CircleShape)
                                .background(Color(0xFFFFD700))
                        )
                        Text(
                            text = "// СОВЕТ ЕВЫ-09  [AI_NAV]",
                            color = Color(0xFFFFD700),
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp
                        )
                    }
                    Spacer(modifier = Modifier.height(3.dp))
                    Text(
                        text = text,
                        color = Color(0xFFF1F5F9),
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
                    modifier = Modifier
                        .size(26.dp)
                        .clip(CutCornerShape(4.dp))
                        .background(Color(0x22FFFFFF))
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Dismiss",
                        tint = Color.White,
                        modifier = Modifier.size(15.dp)
                    )
                }
            }
        }
    }
}
