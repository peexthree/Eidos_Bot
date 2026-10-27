package io.eidos.zerolayer.ui.components

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.ZzzElectricCyan
import io.eidos.zerolayer.ui.theme.ZzzDarkSurface
import java.util.concurrent.ConcurrentHashMap

private val drawableCache = ConcurrentHashMap<String, Int>()
private val bitmapCache = ConcurrentHashMap<Int, ImageBitmap>()

/**
 * Safely decodes a drawable resource ID into an ImageBitmap using runCatching.
 * Supports raster (PNG/JPG/WEBP) and XML vector drawables without throwing ResourceResolutionException.
 */
fun safeLoadImageBitmap(context: Context, resId: Int): ImageBitmap? {
    if (resId == 0) return null
    bitmapCache[resId]?.let { return it }

    return try {
        // 1. Try decoding as direct Bitmap (PNG / JPG / WEBP)
        val options = BitmapFactory.Options().apply {
            inPreferredConfig = Bitmap.Config.ARGB_8888
        }
        val rawBitmap = try {
            BitmapFactory.decodeResource(context.resources, resId, options)
        } catch (_: Throwable) {
            null
        }
        if (rawBitmap != null && rawBitmap.width > 0 && rawBitmap.height > 0) {
            val imgBitmap = rawBitmap.asImageBitmap()
            bitmapCache[resId] = imgBitmap
            return imgBitmap
        }

        // 2. Fallback to ContextCompat for VectorDrawables / NinePatch / XML layers
        val drawable = try {
            ContextCompat.getDrawable(context, resId)
        } catch (_: Throwable) {
            null
        }
        if (drawable != null) {
            val width = drawable.intrinsicWidth.takeIf { it > 0 } ?: 128
            val height = drawable.intrinsicHeight.takeIf { it > 0 } ?: 128
            val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(bitmap)
            drawable.setBounds(0, 0, canvas.width, canvas.height)
            drawable.draw(canvas)
            val imgBitmap = bitmap.asImageBitmap()
            bitmapCache[resId] = imgBitmap
            return imgBitmap
        }
        null
    } catch (_: Throwable) {
        null
    }
}

/**
 * Resolves a string resource name into a valid Android drawable resource ID.
 */
fun resolveDrawableResourceId(context: Context, resName: String?): Int {
    val safeName = resName?.trim() ?: return 0
    if (safeName.isBlank()) return 0

    return drawableCache.getOrPut(safeName) {
        val nameWithoutExt = safeName.substringBeforeLast(".")
        val cleanName = nameWithoutExt.lowercase()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("а", "a").replace("б", "b").replace("в", "v")
            .replace("г", "g").replace("д", "d").replace("е", "e")
            .replace("ж", "zh").replace("з", "z").replace("и", "i")
            .replace("к", "k").replace("л", "l").replace("м", "m")
            .replace("н", "n").replace("о", "o").replace("п", "p")
            .replace("р", "r").replace("с", "s").replace("т", "t")
            .replace("у", "u").replace("ф", "f").replace("х", "kh")
            .replace("ц", "ts").replace("ч", "ch").replace("ш", "sh")
            .replace("щ", "sch").replace("ы", "y").replace("э", "e")
            .replace("ю", "yu").replace("я", "ya")

        // 1. Direct name query
        var foundId = runCatching {
            context.resources.getIdentifier(cleanName, "drawable", context.packageName)
        }.getOrDefault(0)

        if (foundId == 0) {
            foundId = runCatching {
                context.resources.getIdentifier(safeName, "drawable", context.packageName)
            }.getOrDefault(0)
        }

        // 2. Monster and boss mappings
        if (foundId == 0) {
            val monsterDrawable = when {
                cleanName.contains("паразит") -> "monster_1"
                cleanName.contains("глитч") || cleanName.contains("призрак_глитча") -> "monster_2"
                cleanName.contains("дрон") || cleanName.contains("страж_старого") -> "monster_3"
                cleanName.contains("бомба") -> "monster_4"
                cleanName.contains("майнер") -> "monster_5"
                cleanName.contains("гидра") -> "monster_6"
                cleanName.contains("сбой") || cleanName.contains("фатальный") -> "monster_7"
                cleanName.contains("ассасин") || cleanName.contains("даркнет") -> "monster_8"
                cleanName.contains("доминатор") || cleanName.contains("ии_доминатор") -> "monster_9"
                cleanName.contains("стиратель") -> "monster_10"
                cleanName.contains("нейро_призрак") || cleanName.contains("нейропризрак") -> "monster_11"
                cleanName.contains("лич") || cleanName.contains("кибер_лич") -> "monster_12"
                cleanName.contains("архитектор") -> "monster_13"
                cleanName.contains("пожиратель") -> "monster_14"
                cleanName.contains("страж_ядра") -> "monster_15"
                cleanName.contains("синтез") || cleanName.contains("омни_синтез") -> "monster_16"
                cleanName.contains("бог_машины") || cleanName.contains("машина") -> "monster_17"
                cleanName.contains("странник") || cleanName.contains("пустотный") -> "monster_18"
                cleanName.contains("энтропия") -> "monster_19"
                else -> null
            }
            if (monsterDrawable != null) {
                foundId = runCatching {
                    context.resources.getIdentifier(monsterDrawable, "drawable", context.packageName)
                }.getOrDefault(0)
            }
        }

        // 3. Fallback to standard core drawables
        if (foundId == 0) {
            foundId = when {
                cleanName.contains("chip_red") || cleanName.contains("atk") || cleanName == "ram_chip" || cleanName == "god_mode_chip" || cleanName == "overclocker" -> io.eidos.zerolayer.R.drawable.ic_chip_red
                cleanName.contains("chip_blue") || cleanName.contains("def") || cleanName.contains("energy") || cleanName == "logic_gate" || cleanName == "neural_link" -> io.eidos.zerolayer.R.drawable.ic_chip_blue
                cleanName.contains("chip_green") || cleanName.contains("crit") || cleanName.contains("lck") || cleanName.contains("stealth") || cleanName == "glitch_chip" || cleanName == "ai_core" || cleanName == "oblivion_chip" -> io.eidos.zerolayer.R.drawable.ic_chip_green
                cleanName.contains("chip") || cleanName.contains("module") -> io.eidos.zerolayer.R.drawable.ic_chip_red
                cleanName.contains("avatar") || cleanName.contains("operator") -> io.eidos.zerolayer.R.drawable.avatar_operator_default
                cleanName.contains("lootbox") || cleanName.contains("gacha") || cleanName.contains("cube") -> io.eidos.zerolayer.R.drawable.gacha_cube_lootbox
                cleanName.contains("lock") || cleanName.contains("locked") -> io.eidos.zerolayer.R.drawable.ic_lock_cyber
                cleanName.contains("hazard") || cleanName.contains("warning") || cleanName.contains("alert") -> io.eidos.zerolayer.R.drawable.ic_hazard_warning
                else -> 0
            }
        }
        foundId
    }
}

/**
 * Returns a stylized category glyph or abbreviation for fallback display.
 */
private fun getFallbackGlyph(cleanName: String, fallbackText: String?): String {
    return when {
        cleanName.contains("sword") || cleanName.contains("blade") || cleanName.contains("baton") ||
                cleanName.contains("pistol") || cleanName.contains("rifle") || cleanName.contains("knife") ||
                cleanName.contains("cannon") || cleanName.contains("weapon") || cleanName.contains("spike") ||
                cleanName.contains("клинок") || cleanName.contains("меч") || cleanName.contains("оружие") -> "⚔️"

        cleanName.contains("armor") || cleanName.contains("vest") || cleanName.contains("suit") ||
                cleanName.contains("jacket") || cleanName.contains("hoodie") || cleanName.contains("cloak") ||
                cleanName.contains("shield") || cleanName.contains("aegis") || cleanName.contains("броня") ||
                cleanName.contains("щит") -> "🛡️"

        cleanName.contains("head") || cleanName.contains("helmet") || cleanName.contains("goggles") ||
                cleanName.contains("mask") || cleanName.contains("шлем") || cleanName.contains("маска") -> "🪖"

        cleanName.contains("chip") || cleanName.contains("core") || cleanName.contains("link") ||
                cleanName.contains("ram") || cleanName.contains("gate") || cleanName.contains("booster") ||
                cleanName.contains("чип") -> "💾"

        cleanName.contains("medkit") || cleanName.contains("cell") || cleanName.contains("capsule") ||
                cleanName.contains("battery") || cleanName.contains("stim") || cleanName.contains("spray") ||
                cleanName.contains("cleanse") || cleanName.contains("purge") || cleanName.contains("аптечка") ||
                cleanName.contains("стимулятор") || cleanName.contains("припас") -> "🧪"

        cleanName.contains("compass") || cleanName.contains("key") || cleanName.contains("drive") ||
                cleanName.contains("scanner") || cleanName.contains("eraser") || cleanName.contains("wiper") ||
                cleanName.contains("crowbar") || cleanName.contains("ключ") -> "📦"

        !fallbackText.isNullOrBlank() -> fallbackText.trim().take(1).uppercase()
        cleanName.isNotBlank() -> cleanName.take(1).uppercase()
        else -> "◈"
    }
}

@Composable
fun EidosImage(
    resName: String?,
    fallbackIcon: ImageVector = Icons.Default.Info,
    contentDescription: String? = null,
    modifier: Modifier = Modifier,
    borderColor: Color = EidosCyan,
    borderWidth: Dp = 1.dp,
    contentScale: ContentScale = ContentScale.Fit
) {
    val context = LocalContext.current

    val safeName = remember(resName) { resName?.trim() ?: "" }
    val resId = remember(safeName) { resolveDrawableResourceId(context, safeName) }
    val loadedBitmap = remember(resId, context) { safeLoadImageBitmap(context, resId) }

    val cleanName = remember(safeName) {
        safeName.lowercase().removeSuffix(".jpg").removeSuffix(".png").replace(" ", "_")
    }

    if (loadedBitmap != null) {
        Box(
            modifier = modifier
                .background(EidosGlass)
                .then(
                    if (borderWidth > 0.dp && borderColor != Color.Transparent) {
                        Modifier.border(borderWidth, borderColor, CutCornerShape(4.dp))
                    } else Modifier
                ),
            contentAlignment = Alignment.Center
        ) {
            Image(
                bitmap = loadedBitmap,
                contentDescription = contentDescription ?: safeName,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(if (contentScale == ContentScale.Crop || borderWidth == 0.dp) 0.dp else 2.dp),
                contentScale = contentScale
            )
        }
    } else {
        ProceduralCyberpunkArtwork(
            imageName = cleanName,
            modifier = modifier,
            borderColor = borderColor
        )
    }
}
