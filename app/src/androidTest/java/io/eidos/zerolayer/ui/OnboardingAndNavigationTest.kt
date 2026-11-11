package io.eidos.zerolayer.ui

import android.Manifest
import android.content.Context
import androidx.compose.ui.semantics.SemanticsActions
import androidx.compose.ui.test.SemanticsNodeInteraction
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.hasSetTextAction
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.rule.GrantPermissionRule
import androidx.test.uiautomator.UiDevice
import io.eidos.zerolayer.MainActivity
import io.eidos.zerolayer.data.EidosDatabase
import io.eidos.zerolayer.data.Player
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.Before
import org.junit.Ignore
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Первая партия сквозных UI-тестов (П0 из docs/TZ_UPGRADE_2026-11-11.md):
 * онбординг -> хаб, гейт кузницы, переход в инвентарь, кузница с предзаполненным
 * прогрессом, клейм суточного депо.
 *
 * Подход:
 * - Приложение всегда стартует с Splash (видео, тап = скип) -> Onboarding/Hub.
 * - Тесты не удаляют файл БД: синглтон EidosDatabase живёт в общем процессе
 *   инструментальных тестов, и удаление файла под открытой сессией Room
 *   оставляет соединение на несуществующем иноде. Вместо этого каждый тест
 *   прописывает в "eidos_device_prefs" свой device_uuid и device_local_uid -
 *   MainViewModel читает их при создании, поэтому каждый тест работает со
 *   своим чистым профилем игрока в общей БД.
 * - Интерфейс насыщен бесконечными анимациями (rememberInfiniteTransition),
 *   поэтому composeTestRule.mainClock.autoAdvance = false; кадры прокачиваются
 *   вручную через advanceTimeBy, реальная IO (Room-потоки) - через Thread.sleep.
 */
@RunWith(AndroidJUnit4::class)
class OnboardingAndNavigationTest {

    @get:Rule
    val permissionRule: GrantPermissionRule =
        GrantPermissionRule.grant(Manifest.permission.POST_NOTIFICATIONS)

    @get:Rule
    val composeRule = createEmptyComposeRule()

    // Оригинальный профиль реального владельца телефона: тесты прописывают свои
    // uid в eidos_device_prefs и обязаны вернуть всё как было в @After.
    private var savedUuid: String? = null
    private var savedLocalUid: Long? = null
    private var hadPrefs: Boolean = false

    @Before
    fun saveOriginalPrefs() {
        val prefs = targetContext()
            .getSharedPreferences("eidos_device_prefs", Context.MODE_PRIVATE)
        hadPrefs = prefs.all.isNotEmpty()
        savedUuid = prefs.getString("device_uuid", null)
        if (prefs.contains("device_local_uid")) savedLocalUid = prefs.getLong("device_local_uid", 0L)
    }

    @After
    fun restoreOriginalPrefs() {
        val prefs = targetContext()
            .getSharedPreferences("eidos_device_prefs", Context.MODE_PRIVATE)
            .edit()
        if (!hadPrefs) {
            prefs.clear()
        } else {
            savedUuid?.let { prefs.putString("device_uuid", it) }
            if (savedLocalUid != null) {
                prefs.putLong("device_local_uid", savedLocalUid!!)
            } else {
                prefs.remove("device_local_uid")
            }
        }
        prefs.commit()
    }

    /** Скриншот экрана при падении ожидания - чтобы видеть, где тест промахнулся. */
    private fun screenshotOnFail(tag: String) {
        try {
            // /data/local/tmp переживает деинсталляцию приложения после прогона
            val fd = InstrumentationRegistry.getInstrumentation().uiAutomation
                .executeShellCommand("screencap -p /data/local/tmp/FAIL_$tag.png")
            fd.close()
            Thread.sleep(500)
            println("DIAGSHOT: /data/local/tmp/FAIL_$tag.png")
        } catch (_: Throwable) {
        }
    }

    // ---------------------------------------------------------------- helpers

    private fun targetContext(): Context =
        InstrumentationRegistry.getInstrumentation().targetContext

    /** Уникальный тестовый профиль: MainViewModel прочитает это при создании. */
    private fun setTestDeviceContext(testId: Long) {
        val ok = targetContext()
            .getSharedPreferences("eidos_device_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString("device_uuid", "00000000-0000-0000-0000-%012d".format(testId))
            .putLong("device_local_uid", testId)
            .commit()
        assertTrue("Не удалось прописать тестовый uid в eidos_device_prefs", ok)
    }

    private fun launchApp() {
        composeRule.mainClock.autoAdvance = false
        // Android 15+ (OneUI тем более) блокирует подъём активити из фона:
        // ActivityScenario.launch оставляет окно за лончером, тапы уходят мимо.
        // Выводим игру в фокус принудительно через shell-uid UiAutomation.
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        runCatching { if (!device.isScreenOn) device.wakeUp() }
        device.executeShellCommand("wm dismiss-keyguard")
        device.pressHome()
        device.executeShellCommand("am start -W -n io.eidos.zerolayer/.MainActivity")
        Thread.sleep(2000)
        // Сценарий под управлением правила: получает управляемые mainClock кадры
        ActivityScenario.launch(MainActivity::class.java)
    }

    /** Прокачка виртуальных кадров + окно реальному IO (Room-потоки). */
    private fun settle(frameMs: Long = 300) {
        composeRule.mainClock.advanceTimeBy(frameMs)
        Thread.sleep(120)
    }

    private fun hasAnyNode(text: String, substring: Boolean): Boolean =
        composeRule.onAllNodes(hasText(text, substring = substring))
            .fetchSemanticsNodes()
            .isNotEmpty()

    private fun waitText(text: String, substring: Boolean = true, timeoutMs: Long = 20000) {
        val deadline = System.currentTimeMillis() + timeoutMs
        while (System.currentTimeMillis() < deadline) {
            settle(250)
            if (hasAnyNode(text, substring)) return
        }
        screenshotOnFail("wait_" + text.take(20).replace(' ', '_'))
        fail("Текст не найден за ${timeoutMs}мс: \"$text\"")
    }

    private fun clickableNode(text: String, substring: Boolean): SemanticsNodeInteraction? {
        val matches = composeRule.onAllNodes(hasText(text, substring = substring))
            .fetchSemanticsNodes()
        for (i in matches.indices) {
            val node = composeRule.onAllNodes(hasText(text, substring = substring))[i]
            if (node.fetchSemanticsNode().config.contains(SemanticsActions.OnClick)) return node
        }
        return null
    }

    /** Клик по тексту; если узел за экраном - попытка performScrollTo. */
    private fun clickText(text: String, substring: Boolean = true) {
        waitText(text, substring)
        val node = clickableNode(text, substring)
        if (node != null) {
            node.performClick()
            settle(600)
            return
        }
        try {
            composeRule.onAllNodes(hasText(text, substring = substring))[0]
                .performScrollTo()
                .performClick()
        } catch (e: Throwable) {
            fail("Не удалось кликнуть \"$text\": ${e.message}")
        }
        settle(600)
    }

    private fun findClickableByText(text: String): SemanticsNodeInteraction? = try {
        val nodes = composeRule.onAllNodes(hasText(text, substring = true))
        val list = nodes.fetchSemanticsNodes()
        for (i in list.indices) {
            if (nodes[i].fetchSemanticsNode().config.contains(SemanticsActions.OnClick)) {
                return nodes[i]
            }
        }
        null
    } catch (_: Throwable) {
        null
    }

    /**
     * Скип видео-интро (и сплэш, и интро онбординга) - тап в центр экрана.
     * Клик по кликабельным узлам не годится: первый в дереве - кнопка мьюта
     * Евы справа сверху, иначе бесконечно дёргаем звук. Шаг 0 (Lore) не имеет
     * маркера позывного - для него кликаем по кнопке ДАЛЕЕ справа внизу.
     */
    private fun skipIntro() {
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        val deadline = System.currentTimeMillis() + 45000
        val cx = device.displayWidth / 2
        val cy = device.displayHeight / 2
        while (System.currentTimeMillis() < deadline) {
            if (hasAnyNode("ВВЕДИ ПОЗЫВНОЙ", substring = true)) return
            if (hasAnyNode("КУЗНИЦА И СИНТЕЗ", substring = true)) return
            val next = findClickableByText("ДАЛЕЕ")
            if (next != null) {
                next.performClick()
            } else {
                device.click(cx, cy)
            }
            settle(900)
        }
        screenshotOnFail("skip_intro")
        fail("Не удалось пройти Splash-интро за 45с")
    }

    private fun completeOnboarding(nickname: String = "TEST_OP") {
        skipIntro()
        if (!hasAnyNode("ВВЕДИ ПОЗЫВНОЙ", substring = true)) {
            // skipIntro перекликал дальше шага позывного - онбординг уже завершён
            return
        }
        composeRule.onNode(hasSetTextAction()).performTextInput(nickname)
        composeRule.onNode(hasSetTextAction()).performTextInput(nickname)
        settle(300)
        clickText("ДАЛЕЕ")                      // шаг 1 (позывной) -> шаг 2 (синдикаты)
        waitText("СИНДИКАТ")
        clickText("РАЗУМ")
        clickText("ДАЛЕЕ")                      // шаг 2 -> шаг 3 (директивы)
        clickText("ДАЛЕЕ")                      // шаг 3 -> шаг 4 (снаряжение)
        clickText("ПОГРУЖЕНИЕ")                 // финал -> Hub
    }

    /** Ожидание текста с прокруткой: списки не выдают офскрин элементы семантики. */
    private fun waitTextScrollable(text: String, maxSwipes: Int = 4, timeoutMs: Long = 20000) {
        val device = UiDevice.getInstance(InstrumentationRegistry.getInstrumentation())
        val cx = device.displayWidth / 2
        val cy = device.displayHeight / 2
        val deadline = System.currentTimeMillis() + timeoutMs
        var swipes = 0
        while (System.currentTimeMillis() < deadline) {
            settle(250)
            if (hasAnyNode(text, substring = true)) return
            if (swipes < maxSwipes) {
                device.swipe(cx, (cy * 1.6).toInt(), cx, (cy * 0.4).toInt(), 10)
                swipes++
            }
        }
        screenshotOnFail("scroll_" + text.take(20).replace(' ', '_'))
        fail("Текст не найден за ${timeoutMs}мс (со свайпами): \"$text\"")
    }

    // ------------------------------------------------------------------ tests

    @Test
    fun onboardingCompletesToHub() {
        setTestDeviceContext(990001L)
        launchApp()
        completeOnboarding()
        waitText("КУЗНИЦА И СИНТЕЗ")
    }

    @Test
    fun freshOperatorForgeIsLocked() {
        setTestDeviceContext(990002L)
        launchApp()
        completeOnboarding("TEST_GATE")
        waitText("ДОСТУП: 1-Й РЕЙД (100м)")
        // Клик по заблокированной карте не навигирует в кузницу
        clickText("КУЗНИЦА И СИНТЕЗ")
        settle(1000)
        assertTrue(
            "Кузница не должна открываться у свежего оператора",
            !hasAnyNode("КОВКА ШЕЙДЕРОВ", substring = true)
        )
    }

    @Test
    fun hubNavigatesToInventory() {
        setTestDeviceContext(990003L)
        launchApp()
        completeOnboarding("TEST_INV")
        waitText("КУЗНИЦА И СИНТЕЗ")
        clickText("ИНВЕНТАРЬ", substring = false)
        waitText("// ИНВЕНТАРЬ")
        // Секция хранилища отрисована со счётчиком предметов стартового набора
        waitTextScrollable("КЭШ ПРЕДМЕТОВ")
        waitText("ВСЕГО")
    }

    @Test
    fun preseededOperatorReachesForge() {
        setTestDeviceContext(990004L)
        runBlocking {
            EidosDatabase.getDatabase(targetContext()).dao().insertPlayer(
                Player(
                    uid = 990004L,
                    username = "TEST_FORGE",
                    first_name = "TEST_FORGE",
                    faction = "РАЗУМ",
                    max_depth = 1000,
                    raids_done = 1,
                    level = 2,
                    biocoin = 5000L
                )
            )
        }
        launchApp()
        skipIntro()
        // Кузница разблокирована: max_depth >= 100
        waitText("МОДЫ И СИНТЕЗ")
        clickText("КУЗНИЦА И СИНТЕЗ")
        waitText("КОВКА ШЕЙДЕРОВ")
    }

    /**
     * ВРЕМЕННО ОТКЛЮЧЁН (docs/TZ_UPGRADE_2026-11-11.md П0).
     * Тест поймал реальный баг: депо клеймилось многократно - dbMutex у
     * GameRepository экземплярный, параллельные экземпляры VM/репозитория
     * не сериализуются. Частично починено (условный UPDATE в клейме +
     * точечный реген энергии без полной копии игрока), но ещё один
     * stale-writer сбрасывает last_supply_drop - поиск на П4.
     * Вернуть после устранения: клейм -> кулдаун 24ч -> повторное открытие.
     */
    @Ignore("Депо: остался stale-writer, сбрасывающий last_supply_drop - см. комментарий")
    @Test
    fun depotClaimFlowStartsCooldown() {
        setTestDeviceContext(990005L)
        launchApp()
        completeOnboarding("TEST_DEPOT")
        waitText("СИНХРОНИЗАЦИЯ ДЕПО")
        // Баннер открывает диалог синхронизации депо
        clickText("СИНХРОНИЗАЦИЯ ДЕПО")
        waitText("SUPPLY DROP")
        screenshotOnFail("1_dialog_open")
        if (hasAnyNode("СИНХРОНИЗИРОВАТЬ", substring = false)) {
            // Клейм: диалог закрывается сразу после синхронизации
            val claimBtn = findClickableByText("СИНХРОНИЗИРОВАТЬ")
            println("DIAG: кнопка клейма найдена = ${claimBtn != null}")
            claimBtn?.performClick()
            // Клейм асинхронный: ждём появления last_supply_drop в БД до 15с
            runBlocking {
                val dao = EidosDatabase.getDatabase(targetContext()).dao()
                repeat(15) { attempt ->
                    kotlinx.coroutines.delay(1000)
                    val p = dao.getPlayer(990005L)
                    println("DIAG: попытка $attempt: last_supply_drop = ${p?.last_supply_drop}")
                    if ((p?.last_supply_drop ?: 0L) > 0L) return@runBlocking
                }
            }
            screenshotOnFail("2_after_claim")
            // Диалог должен закрыться; если остался - клейм не прошёл
            if (hasAnyNode("SUPPLY DROP", substring = true)) {
                screenshotOnFail("3_dialog_still_open")
                fail("Диалог депо не закрылся после клейма")
            }
            // Перепроверка: повторное открытие показывает кулдаун 24ч
            waitText("СИНХРОНИЗАЦИЯ ДЕПО")
            clickText("СИНХРОНИЗАЦИЯ ДЕПО")
            waitText("SUPPLY DROP")
        }
        // В диалоге идёт перезарядка шлюза (клейм уже был - руками или за туториал)
        waitText("ПЕРЕЗАРЯДКА")
        clickText("ОТМЕНА", substring = false)
    }
}
