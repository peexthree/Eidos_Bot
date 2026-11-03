package io.eidos.zerolayer.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

@Composable
fun ZzzIcon(
    @DrawableRes iconRes: Int,
    contentDescription: String? = null,
    modifier: Modifier = Modifier,
    size: Dp = 20.dp,
    tint: Color = Color.Unspecified
) {
    if (tint == Color.Unspecified) {
        Image(
            painter = painterResource(id = iconRes),
            contentDescription = contentDescription,
            modifier = modifier.size(size)
        )
    } else {
        Icon(
            painter = painterResource(id = iconRes),
            contentDescription = contentDescription,
            tint = tint,
            modifier = modifier.size(size)
        )
    }
}
