package com.example.eidos.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.ui.theme.EidosCyan
import com.example.eidos.ui.theme.EidosGlass
import com.example.eidos.ui.theme.EidosNeon

/**
 * 📱 7. ADAPTIVE & RESPONSIVE MULTI-PANE CYBER LAYOUT
 * Supports Foldables, Tablets, and Chromebooks by detecting screen width (> 600.dp)
 * and dynamically showing a Dual-Column Command Bridge HUD.
 */

@Composable
fun AdaptiveCyberContainer(
    leftPane: @Composable ColumnScope.() -> Unit,
    rightPane: @Composable ColumnScope.() -> Unit,
    modifier: Modifier = Modifier
) {
    BoxWithConstraints(modifier = modifier.fillMaxSize()) {
        val isWideScreen = maxWidth >= 600.dp

        if (isWideScreen) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Left Panel (Command Side Deck)
                Card(
                    modifier = Modifier
                        .weight(0.4f)
                        .fillMaxHeight()
                        .border(1.dp, EidosCyan, CutCornerShape(8.dp)),
                    colors = CardDefaults.cardColors(containerColor = EidosGlass),
                    shape = CutCornerShape(8.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("📡", fontSize = 16.sp)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "КОМАНДНЫЙ МОСТИК // HUD",
                                color = EidosNeon,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                        leftPane()
                    }
                }

                // Right Panel (Main Operations Area)
                Card(
                    modifier = Modifier
                        .weight(0.6f)
                        .fillMaxHeight()
                        .border(1.dp, EidosNeon.copy(alpha = 0.6f), CutCornerShape(8.dp)),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF080C12)),
                    shape = CutCornerShape(8.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(12.dp)
                    ) {
                        rightPane()
                    }
                }
            }
        } else {
            // Standard Single-Pane Layout
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                rightPane()
            }
        }
    }
}
