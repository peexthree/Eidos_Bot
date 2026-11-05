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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
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
import coil.ImageLoader
import coil.compose.AsyncImage
import coil.decode.SvgDecoder
import coil.request.ImageRequest
import io.eidos.zerolayer.data.AssetIconsMapping
import io.eidos.zerolayer.ui.theme.EidosCyan
import io.eidos.zerolayer.ui.theme.EidosGlass
import io.eidos.zerolayer.ui.theme.ZzzElectricCyan
import io.eidos.zerolayer.ui.theme.ZzzDarkSurface
import java.util.concurrent.ConcurrentHashMap

private val drawableCache = ConcurrentHashMap<String, Int>()
private val bitmapCache = android.util.LruCache<Int, ImageBitmap>(80)

private val ITEM_DRAWABLE_ALIASES: Map<String, String> = mapOf(
    "eidos_shard" to "data_shard",
    "schrodinger_armor" to "schrodingers_armor",
    "neural_link" to "neuro_link",
    "error_404_mirror" to "error_404",
    "martyr_halo" to "martyrs_halo",
    "cyber_halo" to "martyrs_halo",
    "cryo" to "cryo_capsule",
    "fragment" to "data_fragment",
    "memory_wiper" to "cache_wiper",
    "admin_key" to "master_key",
    "neural_stimulator" to "neural_injector",
    "exo_skeleton" to "exoskeleton_frame",
    "crown_paranoia" to "eidos_crown",
    "overclock_crown" to "neuro_crown",
    "architect_mask" to "architect_eye",
    "void_walker_hood" to "holo_hood",
    "nano_suit" to "nano_armor",
    "reality_armor" to "void_armor",
    "quantum_shield" to "aegis",
    "vampire_visor" to "reflex_visor",
    "tac_visor" to "sentinel_visor",
    "tactical_scanner" to "combat_goggles",
    "soft_trojan_v1" to "trojan_bat",
    "soft_ddos_v1" to "ddos_cannon",
    "soft_vpn_v1" to "vpn_ghost",
    "soft_sniffer_v1" to "sniffer",
    "soft_backdoor_v1" to "backdoor_js",
    "soft_brute_v1" to "bruteforce_exe",
    "soft_wall_v1" to "firewall_10",
    "soft_ice_v1" to "ice_wall",
    "soft_proxy_v1" to "vpn_ghost",
    "soft_botnet_v1" to "ddos_cannon",
    "soft_antivirus_v1" to "firewall_10",
    "soft_aegis_v1" to "aegis",
    "hub_lock" to "cipher_lock",
    "decoy_trap" to "ic_event_trap",
    "firewall" to "firewall_10",
    "ice_trap" to "ice_wall",
    "proxy_server" to "vpn_ghost",
    "stealth_spray" to "reality_silencer",
    "chronometer" to "chrono_drive",
    "god_mode_chip" to "kamikaze_protocol",
    "overclocker" to "overclock_module",
    "backup_drive" to "flash_storage",
    "logic_gate" to "quantum_transistor",
    "ai_core" to "tachyon_core",
    "leather_jacket" to "cyber_vest",
    "scavenger_coat" to "hoodie",
    "tactical_suit" to "kevlar_vest",
    "phantom_cloak" to "shadow_cowl",
    "force_field" to "thermonuclear_shroud",
    "relic_vampire" to "eidos_crown",
    "relic_speed" to "tactical_helmet",
    "shadow_reliq_speed" to "tactical_helmet",
    "corrupted_data_cluster" to "anomaly_glitch_3",
    "accel" to "cpu_booster",
    "decoder" to "abyssal_key",
    "encrypted_cache" to "cipher_lock",
    "purification_sync" to "glitch_filter",
    "ram_chip" to "quantum_chip",
    "maxwells_demon" to "imposter_syndrome"
)

/**
 * Singleton Coil ImageLoader configured with SvgDecoder for rendering SVG icons from assets.
 */
object EidosSvgImageLoader {
    @Volatile
    private var loader: ImageLoader? = null

    fun get(context: Context): ImageLoader {
        return loader ?: synchronized(this) {
            loader ?: ImageLoader.Builder(context.applicationContext)
                .components {
                    add(SvgDecoder.Factory())
                }
                .build().also { loader = it }
        }
    }
}

/**
 * Safely decodes a drawable resource ID into an ImageBitmap using runCatching.
 * Supports raster (PNG/JPG/WEBP) and XML vector drawables without throwing ResourceResolutionException.
 */
fun safeLoadImageBitmap(context: Context, resId: Int): ImageBitmap? {
    if (resId == 0) return null
    bitmapCache.get(resId)?.let { return it }

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
            bitmapCache.put(resId, imgBitmap)
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
            bitmapCache.put(resId, imgBitmap)
            return imgBitmap
        }
        null
    } catch (t: Throwable) {
        android.util.Log.w("EidosImage", "safeLoadImageBitmap failed for resId=$resId: ${t.message}")
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

        // 0. Explicit Item Aliases Map query
        val aliasTarget = ITEM_DRAWABLE_ALIASES[cleanName] ?: ITEM_DRAWABLE_ALIASES[safeName.lowercase()]
        var foundId = if (aliasTarget != null) {
            runCatching {
                context.resources.getIdentifier(aliasTarget, "drawable", context.packageName)
            }.getOrDefault(0)
        } else 0

        // 1. Direct name query
        if (foundId == 0) {
            foundId = runCatching {
                context.resources.getIdentifier(cleanName, "drawable", context.packageName)
            }.getOrDefault(0)
        }

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
                cleanName.contains("дрон") -> "monster_3"
                cleanName.contains("бомба") -> "monster_4"
                cleanName.contains("майнер") -> "monster_5"
                cleanName.contains("гидра") -> "monster_6"
                cleanName.contains("доминатор") || cleanName.contains("ии_доминатор") -> "monster_7"
                cleanName.contains("стиратель") -> "monster_8"
                cleanName.contains("нейро_призрак") || cleanName.contains("нейропризрак") -> "monster_9"
                cleanName.contains("кибер_лич") || cleanName.contains("лич") -> "monster_10"
                cleanName.contains("архитектор") -> "monster_11"
                cleanName.contains("пожиратель") -> "monster_12"
                cleanName.contains("страж_ядра") || cleanName.contains("страж") -> "monster_13"
                cleanName.contains("синтез") || cleanName.contains("омни_синтез") -> "monster_14"
                cleanName.contains("бог_машины") || cleanName.contains("бог") || cleanName.contains("машина") -> "monster_15"
                cleanName.contains("странник") || cleanName.contains("пустотный") -> "monster_16"
                cleanName.contains("энтропия") -> "monster_17"
                cleanName.contains("сбой") || cleanName.contains("фатальный") -> "monster_18"
                cleanName.contains("ассасин") || cleanName.contains("даркнет") -> "monster_19"
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
                cleanName.contains("avatar") || cleanName.contains("operator") -> io.eidos.zerolayer.R.drawable.doll_operator_rig
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
    borderColor: Color = Color.Transparent,
    borderWidth: Dp = 0.dp,
    contentScale: ContentScale = ContentScale.Crop
) {
    val context = LocalContext.current

    val safeName = remember(resName) { resName?.trim() ?: "" }
    val resId = remember(safeName) { resolveDrawableResourceId(context, safeName) }
    val loadedBitmap = remember(resId, context) { safeLoadImageBitmap(context, resId) }

    val cleanName = remember(safeName) {
        safeName.lowercase()
            .removeSuffix(".jpeg")
            .removeSuffix(".jpg")
            .removeSuffix(".png")
            .removeSuffix(".webp")
            .replace(" ", "_")
    }

    val boxModifier = modifier
        .background(if (borderWidth > 0.dp && borderColor != Color.Transparent) EidosGlass else Color.Transparent)
        .then(
            if (borderWidth > 0.dp && borderColor != Color.Transparent) {
                Modifier.border(borderWidth, borderColor, CutCornerShape(4.dp))
            } else Modifier
        )

    if (loadedBitmap != null) {
        // Direct Bitmap or VectorDrawable from res/drawable
        Box(
            modifier = boxModifier,
            contentAlignment = Alignment.Center
        ) {
            Image(
                bitmap = loadedBitmap,
                contentDescription = contentDescription ?: safeName,
                modifier = Modifier
                    .fillMaxSize()
                    .padding(if (contentScale == ContentScale.Crop || borderWidth == 0.dp || borderColor == Color.Transparent) 0.dp else 2.dp),
                contentScale = contentScale
            )
        }
    } else {
        // Variant A: Load SVG from assets icons via Coil
        val assetSvgUrl = remember(safeName) { AssetIconsMapping.getAssetIconUrl(safeName) }
        val imageLoader = remember(context) { EidosSvgImageLoader.get(context) }
        var isSvgError by remember(safeName) { mutableStateOf(false) }

        if (!isSvgError && assetSvgUrl.isNotBlank()) {
            Box(
                modifier = boxModifier,
                contentAlignment = Alignment.Center
            ) {
                AsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(assetSvgUrl)
                        .crossfade(true)
                        .build(),
                    imageLoader = imageLoader,
                    contentDescription = contentDescription ?: safeName,
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(if (contentScale == ContentScale.Crop || borderWidth == 0.dp || borderColor == Color.Transparent) 0.dp else 2.dp),
                    contentScale = contentScale,
                    onError = {
                        isSvgError = true
                    }
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
}
