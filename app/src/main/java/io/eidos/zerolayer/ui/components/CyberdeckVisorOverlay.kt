package io.eidos.zerolayer.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import io.eidos.zerolayer.R

/**
 * Cyberdeck Visor tactical HUD overlay.
 * Renders optional background hex grid, CRT scanlines, and 4 corner holographic brackets.
 * All decorative layers are strictly non-interactive and do not intercept touches.
 */
@Composable
fun CyberdeckVisorOverlay(
    modifier: Modifier = Modifier,
    showGrid: Boolean = true,
    showScanlines: Boolean = true,
    cornerPadding: Dp = 8.dp,
    content: @Composable BoxScope.() -> Unit
) {
    Box(modifier = modifier.fillMaxSize()) {
        // 1. Фоновая гексагональная нано-сетка
        if (showGrid) {
            Image(
                painter = painterResource(id = R.drawable.ic_hud_grid_hex),
                contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier
                    .fillMaxSize()
                    .alpha(0.08f)
            )
        }

        // 2. Основной контент экрана (интерактивные кнопки, карточки, арена)
        content()

        // 3. CRT-сканлинии поверх контента (декоративный слой, не перехватывает клики)
        if (showScanlines) {
            Image(
                painter = painterResource(id = R.drawable.ic_hud_scanlines),
                contentDescription = null,
                contentScale = ContentScale.FillBounds,
                modifier = Modifier
                    .fillMaxSize()
                    .alpha(0.06f)
            )
        }

        // 4. Угловые технологические скобы визора
        Image(
            painter = painterResource(id = R.drawable.ic_hud_corner_tl),
            contentDescription = null,
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(start = cornerPadding, top = cornerPadding)
                .size(44.dp)
                .alpha(0.85f)
        )
        Image(
            painter = painterResource(id = R.drawable.ic_hud_corner_tr),
            contentDescription = null,
            modifier = Modifier
                .align(Alignment.TopEnd)
                .padding(end = cornerPadding, top = cornerPadding)
                .size(44.dp)
                .alpha(0.85f)
        )
        Image(
            painter = painterResource(id = R.drawable.ic_hud_corner_bl),
            contentDescription = null,
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(start = cornerPadding, bottom = cornerPadding)
                .size(44.dp)
                .alpha(0.85f)
        )
        Image(
            painter = painterResource(id = R.drawable.ic_hud_corner_br),
            contentDescription = null,
            modifier = Modifier
                .align(Alignment.BottomEnd)
                .padding(end = cornerPadding, bottom = cornerPadding)
                .size(44.dp)
                .alpha(0.85f)
        )
    }
}
