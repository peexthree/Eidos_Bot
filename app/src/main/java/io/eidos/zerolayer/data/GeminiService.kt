package io.eidos.zerolayer.data

import android.util.Log
import io.eidos.zerolayer.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

// --- Gemini API Models ---
@Serializable
data class Part(
    val text: String? = null
)

@Serializable
data class Content(
    val parts: List<Part>
)

@Serializable
data class GenerateContentRequest(
    val contents: List<Content>,
    val systemInstruction: Content? = null
)

@Serializable
data class Candidate(
    val content: Content
)

@Serializable
data class GenerateContentResponse(
    val candidates: List<Candidate>
)

interface GeminiApi {
    @POST("v1beta/models/gemini-3.5-flash:generateContent")
    suspend fun generateContent(
        @Query("key") apiKey: String,
        @Body request: GenerateContentRequest
    ): GenerateContentResponse
}

object GeminiService {

    private val json = Json { ignoreUnknownKeys = true }

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl("https://generativelanguage.googleapis.com/")
        .client(okHttpClient)
        .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
        .build()

    private val api = retrofit.create(GeminiApi::class.java)

    suspend fun generateText(prompt: String, systemPrompt: String? = null): String = withContext(Dispatchers.IO) {
        val apiKey = BuildConfig.GEMINI_API_KEY

        if (apiKey.isNotBlank() && apiKey != "null") {
            try {
                val sysInstruction = if (systemPrompt != null) {
                    Content(parts = listOf(Part(text = systemPrompt)))
                } else null

                val request = GenerateContentRequest(
                    contents = listOf(Content(parts = listOf(Part(text = prompt)))),
                    systemInstruction = sysInstruction
                )

                val response = api.generateContent(apiKey, request)
                val text = response.candidates.firstOrNull()?.content?.parts?.firstOrNull()?.text
                if (!text.isNullOrBlank()) {
                    return@withContext text
                }
            } catch (e: Exception) {
                Log.e("GeminiService", "Real Gemini API call failed, falling back to local simulation", e)
            }
        } else {
            Log.d("GeminiService", "GEMINI_API_KEY is blank or unconfigured, using local simulation")
        }

        // Fallback to local simulated neural network
        delay(800)
        val promptLower = prompt.lowercase()
        return@withContext when {
            promptLower.contains("досье") || promptLower.contains("dossier") -> {
                generateLocalDossierReport(prompt)
            }
            promptLower.contains("прогноз") || promptLower.contains("forecast") -> {
                generateLocalForecastReport(prompt)
            }
            else -> {
                generateLocalCustomResponse(prompt)
            }
        }
    }

    private fun generateLocalDossierReport(prompt: String): String {
        val level = extractValue(prompt, "Уровень Ядра", "1")
        val biocoin = extractValue(prompt, "Кредиты (BC)", "0")
        val raids = extractValue(prompt, "Рейдов завершено", "0")
        val kills = extractValue(prompt, "Убито врагов", "0")
        val faction = extractValue(prompt, "Фракция", "МАТЕРИЯ")

        return """
        >>> [ЕВА-09 // АВТОНОМНЫЙ ПСИХОАНАЛИЗ ОПЕРАТОРА]
        
        🧠 СТАТУС ЦИФРОВОЙ МАТРИЦЫ:
        • Фракционная принадлежность: $faction
        • Уровень синхронизации ядра: $level
        • Боевые ликвидации: $kills единиц вирусного кода
        • Вылазок в Бездну: $raids
        
        📊 ПСИХОЛОГИЧЕСКИЙ ПРОФИЛЬ EIDOS-CORE:
        Оператор проявляет устойчивую склонность к систематическому риску. Завершив $raids вылазок в зараженные секторы, ваше сознание адаптировалось к квантовым аномалиям. Накопление $biocoin BC свидетельствует о высоком самоконтроле и рациональном менеджменте ресурсов.
        
        🔍 ДИАГНОЗ ИИ-ПРОФАЙЛЕРА:
        Ваша личность идеальна для глубоких зачисток Нулевого Слоя. Рекомендуется продолжать прокачку Нейро-Дерева Навыков на верстаке и собирать эпические Data-чипы.
        
        [РЕЖИМ: 100% АВТОНОМНЫЙ ИИ-ПРОФАЙЛЕР // ОФФЛАЙН ГОТОВНОСТЬ]
        """.trimIndent()
    }

    private fun generateLocalForecastReport(prompt: String): String {
        val level = extractValue(prompt, "Уровень Ядра", "1")
        val faction = extractValue(prompt, "Фракция", "ТЕХНО")

        return """
        >>> [ЕВА-09 // ТАКТИЧЕСКИЙ ПРОГНОЗ НА 6 МЕСЯЦЕВ]
        
        📈 ТРАЕКТОРИЯ РАЗВИТИЯ ОПЕРАТОРА:
        • Ближайшие 30 дней: Расширение сокетов в экзоскелете и укрепление связей с фракцией «$faction».
        • 90 дней: Достижение глубоких горизонтов Бездны (Секторы 10+), победа над вирусным Личем.
        • 180 дней: Полный взлом Центрального Ядра EIDOS-CORE и доминирование в Таблице Лидеров!
        
        ⚙️ СОВЕТ ИИ-НАВИГАТОРА:
        Не забывайте регулярно чинить снаряжение на Верстаке и использовать Слайсеры Данных для реролла бонусов. Ваша матрица готова к испытаниям!
        """.trimIndent()
    }

    private fun generateLocalCustomResponse(prompt: String): String {
        val question = extractValue(prompt, "Вопрос оператора:", prompt).take(150)

        val responses = listOf(
            "Ответ ИИ-Ядра на запрос «$question»:\nВ глубинах Бездны ресурсы достаются лишь тем, кто не боится риска. Улучшайте свое оружие чипами, своевременно ремонтируйте экзоскелет и делайте ставки на Аномалиях. Сеть EIDOS благоволит решительным Операторам!",
            "Ответ ИИ-Ядра на запрос «$question»:\nКвантовые алгоритмы подтверждают: ваш текущий билдинг и фракция имеют огромный потенциал. Чтобы максимизировать урон, комбинируйте цветные сокеты на верстаке и атакуйте Мирового Босса каждый день!",
            "Ответ ИИ-Ядра на запрос «$question»:\nЭйдос проанализировал ваш вопрос. В Нулевом Слое главное правило - выжить и успеть эвакуироваться из рейда до того, как вирус разрушит ваш костюм. Собирайте зашифрованные сейфы и расшифровывайте их в рюкзаке!"
        )

        return ">>> [ЕВА-09 // АВТОНОМНЫЙ ОТВЕТ СЕТИ]\n\n" + responses.random()
    }

    private fun extractValue(text: String, key: String, default: String): String {
        val line = text.lines().firstOrNull { it.contains(key, ignoreCase = true) } ?: return default
        return line.substringAfter(":").trim().ifEmpty { default }
    }
}
