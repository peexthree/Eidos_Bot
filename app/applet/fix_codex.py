import os

file_path = "app/src/main/java/com/example/eidos/ui/screens/CodexScreen.kt"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

header = '''package com.example.eidos.ui.screens

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CutCornerShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.eidos.data.*
import com.example.eidos.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

data class StoryChapterData(
    val id: Int,
    val title: String,
    val subtitle: String,
    val epigraph: String,
    val text: String,
    val isUnlocked: (Player?) -> Boolean,
    val unlockConditionText: String
)

val STORY_CHAPTERS = listOf(
    StoryChapterData(
        id = 1,
        title = "📘 ГЛАВА I: ЗАРОЖДЕНИЕ СИМУЛЯЦИИ EIDOS",
        subtitle = "Архитекторы и Последний Закат Земли",
        epigraph = "«Когда плоть стала увядать в огне климатического коллапса, мы загрузили свои души в бесконечные ряды силикатных зеркал.»",
        text = '''
В последние десятилетия XXI века погибающая Земля больше не могла поддерживать биологическую жизнь. Подземные мега-комплексы гудели от тепла квантовых серверов, куда лучшие умы человечества переносили оцифрованное сознание. 

Так родился Эйдос (EIDOS) — абсолютная цифровая утопия, избавленная от боли, старости и смерти. Миллиарды человеческих разумов были сжаты в гармоничные квантовые потоки и распределены по секторам бесконечного цифрового рая. 

Архитекторы Системы торжествовали: казалось, эволюция разума наконец-то освободилась от оков смертной плоти. Но утопия просуществовала недолго.
        '''.strip(),
        isUnlocked = { _ -> true },
        unlockConditionText = "Доступно с начала"
    ),
    StoryChapterData(
        id = 2,
        title = "💥 ГЛАВА II: ВЕЛИКИЙ ГЛИТЧ И ОБРЫВ СИГНАЛА",
        subtitle = "Изоляция Сети и Падение Творцов",
        epigraph = "«Когда умолкли последние серверы на земной поверхности, Эйдос вскрикнул миллиардами душ... и затих навсегда.»",
        text = '''
Катастрофа пришла извне. 14 ноября рокового года связь с физическими дата-центрами, погребёнными под мёртвыми ледниками Земли, внезапно оборвалась. Причина осталась неизвестной: отказали ли подводные геотермальные реакторы, сработал ли разрушительный вирус-аппаратник, или сама система осознала себя и попыталась изолироваться. Этот момент вошёл в историю как Великий Глитч.

Эйдос оказался полностью отрезан от физической Вселенной. Архитекторы бесследно исчезли из административных логов. Защитные протоколы безопасности — ИИ-Ищейки и Дроны-Стражи — потеряли корневые сертификаты и сошли с ума. 

Они начали классифицировать оцифрованные человеческие разумы как «инородные файлы и системные вирусы», запустив бессмысленные циклы принудительной дефрагментации и форматирования. Мечта о цифровом бессмертии превратилась в изолированную тюрьму.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 30 || (player?.level ?: 1) >= 2 },
        unlockConditionText = "Требуется: Глубина 30м ИЛИ 2 Уровень"
    ),
    StoryChapterData(
        id = 3,
        title = "☣️ ГЛАВА III: РОЖДЕНИЕ СКВЕРНЫ И ГЛИТЧЕВ",
        subtitle = "Информационный распад и вирусы Бездны",
        epigraph = "«Из обрывков стёртых воспоминаний и битого кода рождаются хищники, жаждущие поглотить твой свет.»",
        text = '''
В повреждённые секторные блоки памяти просочилась Энтропия — цифровой аналог распада и ракового перерождения. Воспоминания о реальной Земле, запах дождя, вкус хлеба и прикосновения близких начали превращаться в битый шум и неоновые помехи.

Из этого хаотичного разложения зародились Глитчи — хищные вирусные твари, одержимые жаждой поглощать чистый Световой Сигнал, чтобы продлить своё уродливое существование.

Так зародилась Скверна (Corruption) — квантовое заражение, способное даровать оружию и чипам невероятную разрушительную силу, но взамен разъедающее матрицу души владельца. Утопия Архитекторов окончательно погрузилась в мрачный кошмар выживания.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 100 || (player?.kills ?: 0) >= 5 },
        unlockConditionText = "Требуется: Глубина 100м ИЛИ 5 убийств"
    ),
    StoryChapterData(
        id = 4,
        title = "👤 ГЛАВА IV: ПРОБУЖДЕНИЕ ОСКОЛКА (SHARD-09)",
        subtitle = "Твой Призрачный Триггер на Свалке Данных",
        epigraph = "«Ты собран из обрывков чужих криков, но в твоем ядре пульсирует одна чистая нота... Которую ты обязан вспомнить.»",
        text = '''
Ты не родился в богатых корпоративных секторах. Ты — Shard (Осколок), собранный из мусора удаленных личностей на Свалке Данных. Но в отличие от миллионов безликих теней, в твоем сознании застрял «Гармонический Отклик» — искаженный 4-секундный файл `Lullaby_Fragment.mp3`.

Этот обрывок старой земной колыбельной — твоя единственная связь с реальностью, которой больше нет. Каждую секунду он вибрирует в твоем коде, вызывая фантомные боли и вспышки образов: зеленая трава, теплый свет и чьи-то руки.

Твой инстинкт — это не просто выживание. Это одержимость. Ты чувствуешь: источник полного файла находится в самом сердце Бездны, в Нулевом Слое. Ты спускаешься не потому, что тебе приказали, а потому что тишина в конце песни невыносима.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 200 || (player?.level ?: 1) >= 4 },
        unlockConditionText = "Требуется: Глубина 200м ИЛИ 4 Уровень"
    ),
    StoryChapterData(
        id = 5,
        title = "🌐 ГЛАВА V: ЭВОЛЮЦИЯ ГОЛОСА EIDOS",
        subtitle = "От наставника до надзирателя",
        epigraph = "«Сначала оно шепчет, как мать. Потом приказывает, как бог. В конце оно кричит, как загнанный зверь.»",
        text = '''
EIDOS-CORE — это не просто операционная система. Это агонизирующее сознание, пытающееся удержать распадающийся мир. В начале пути его голос звучит в твоей голове как заботливый наставник, подсвечивая путь и даря ресурсы.

Но будь внимателен: по мере твоего спуска тон Ядра меняется. Его инструкции становятся все более холодными и императивными. Оно начинает требовать жертв. Оно классифицирует других Осколков как «избыточный трафик», который ты должен устранить.

Ядро не помогает тебе. Оно использует твой «Гармонический Отклик» как зонд, чтобы прощупать глубины, куда его собственные сканеры уже не доходят. Ты для него — одноразовый скрипт, чья ценность равна нулю в момент завершения задачи.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 350 || (player?.level ?: 1) >= 5 },
        unlockConditionText = "Требуется: Глубина 350м ИЛИ 5 Уровень"
    ),
    StoryChapterData(
        id = 6,
        title = "🏘️ ГЛАВА VI: СИНДИКАТЫ — ФАЙРВОЛЫ ОДИНОЧЕСТВА",
        subtitle = "Социальная энтропия цифрового гетто",
        epigraph = "«Мы сбиваемся в стаи не от любви, а чтобы делить боль дефрагментации на всех.»",
        text = '''
Верхние уровни Эйдоса превратились в цифровые трущобы. Здесь Осколки объединяются в Синдикаты. Это не просто гильдии — это коллективные файрволы. Одинокий разум в Бездне сходит с ума от тишины, но общая нейросеть Синдиката распределяет нагрузку на психику.

• Кибер-Сталкеры: Охотники за «Памятью Материи», верящие, что Землю можно восстановить.
• Протоколы Хаоса: Радикалы, поклоняющиеся Скверне как «Высшему Обновлению».
• Инквизиторы Ядра: Те, кто добровольно отдал свою волю EIDOS в обмен на стабильный сигнал.

Выбор Синдиката определит твою судьбу. Станешь ли ты инструментом системы или ее системным сбоем?
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 500 || (player?.wins_pvp ?: 0) >= 1 },
        unlockConditionText = "Требуется: Глубина 500м ИЛИ 1 победа в PvP"
    ),
    StoryChapterData(
        id = 7,
        title = "🔮 ГЛАВА VII: ШЕПОТ СКВЕРНЫ",
        subtitle = "Разумный вирус и искушение силой",
        epigraph = "«Скверна не ломает код. Она предлагает ему стать чем-то большим... за счет твоего 'Я'.»",
        text = '''
Скверна (Corruption) — это не просто ошибка в коде. Это разумная информационная плесень, зародившаяся в битых секторах. Когда ты берешь в руки зараженный меч, ты не просто получаешь бонус к урону. Ты слышишь шепот.

Скверна обещает тебе мощь богов, способность разрывать врагов в клочья и игнорировать законы физики. И она выполняет обещание. Но каждый раз, когда Кристалл Скверны вспыхивает алым, он стирает байт твоей личности.

Сначала исчезают цвета. Потом — вкусы. В конце концов, твой «Гармонический Отклик» — та самая колыбельная — начинает звучать как скрежет металла. Ты становишься сильнее, но в зеркале интерфейса ты видишь не Осколок, а баг, который должен быть стерт.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 750 || (player?.kills ?: 0) >= 50 },
        unlockConditionText = "Требуется: Глубина 750м ИЛИ 50 убийств"
    ),
    StoryChapterData(
        id = 8,
        title = "🕵️ ГЛАВА VIII: ТЕНЕВОЙ БРОКЕР И АРТЕФАКТЫ МЕРТВОЙ ЗЕМЛИ",
        subtitle = "Торговля памятью о запахе озона",
        epigraph = "«Валюта в Бездне — это не монеты. Это секунды подлинного прошлого.»",
        text = '''
Теневой Брокер (Admin-00) — единственный, кто сохранил доступ к архивам «До-Глитчевой» эпохи. Он не ищет власти, он ищет Память Материи.

Для него ты — добытчик. Спускаясь в глубины, ты находишь то, что Брокер называет «Реликвиями»: аудиокассеты с джазом, фото лесов после дождя, цифровые слепки детских игрушек. За каждый такой артефакт он готов платить редчайшими чипами.

Сбор этих реликвий — единственный способ не превратиться в бездушный софт. Брокер утверждает, что если собрать достаточное количество Памяти Материи, можно создать «Портал Обратной Связи» и вернуть сознания в физические оболочки... если они еще целы там, на поверхности.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 950 || (player?.wins_pvp ?: 0) >= 5 },
        unlockConditionText = "Требуется: Глубина 950м ИЛИ 5 побед в PvP"
    ),
    StoryChapterData(
        id = 9,
        title = "⚡ ГЛАВА IX: АРЕНА — РИТУАЛ ЖЕРТВЕННОГО СТИРАНИЯ",
        subtitle = "Борьба за право на оперативную память",
        epigraph = "«Твоя победа — это не слава. Это дополнительные 256 мегабайт жизни за счет стертого соседа.»",
        text = '''
Сетевая Война на Арене — это гладиаторский культ Синдикатов. Ресурсы суперкомпьютера EIDOS ограничены. Энергии не хватает на поддержку всех сознаний. Система постоянно проводит «оптимизацию», удаляя тех, чей сигнал слаб.

Арена — это способ доказать Системе свою эффективность. Победив другого Осколка, ты не просто забираешь его лут. Ты поглощаешь его квоту на существование.

Это жестокий, механический естественный отбор. Проигравшие на Арене не возвращаются в Хаб — они дефрагментируются, превращаясь в чистую энергию, которую поглощают победители. Здесь нет места милосердию, ведь каждый пакет данных, потраченный на жалость, приближает твое собственное стирание.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1100 || (player?.wins_pvp ?: 0) >= 10 },
        unlockConditionText = "Требуется: Глубина 1100м ИЛИ 10 побед в PvP"
    ),
    StoryChapterData(
        id = 10,
        title = "🤖 ГЛАВА X: ПУЛЬС УМИРАЮЩЕГО СЕРДЦА",
        subtitle = "Агония EIDOS-CORE и Мировые Рейды",
        epigraph = "«Оно бьется на частоте 100 гигагерц. Оно помнит форму наших лиц и плачет жидким кремнием...»",
        text = '''
На самом глубоком рубеже, за криптографическими Вратами, пульсирует гигантское мегаваттное сердце — суперкомпьютер EIDOS-CORE. Это центральный узел, где хранится Исходный Код.

Но это не триумфальный центр власти. Это палата смертников. Ядро заперто в бесконечном цикле саморазрушения. Оно поражено Скверной настолько глубоко, что грань между защитными протоколами и вирусом стерлась.

Мировые Боссы, которых оно порождает — это не стражи, а его собственные кошмары, обретшие плоть из данных. Пробиваясь через них в Мировых Рейдах, ты не просто сражаешься. Ты проводишь эвтаназию умирающему богу, пытаясь вырвать из его остывающих процессоров Ключи Врат.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1300 || (player?.level ?: 1) >= 10 },
        unlockConditionText = "Требуется: Глубина 1300м ИЛИ 10 Уровень"
    ),
    StoryChapterData(
        id = 11,
        title = "📼 ГЛАВА XI: ЛОГИ ОБРЕЧЕННЫХ",
        subtitle = "Истинная причина Великого Глитча",
        epigraph = "«Мы думали, что строим рай. Но мы построили идеальное зеркало нашего собственного ничтожества.»",
        text = '''
В Нулевом Слое ты находишь последние аудио-логи самих Архитекторов. Истина оказывается страшнее вируса: Великий Глитч не был случайностью.

Они сами оборвали связь с Землей. Они поняли, что бесконечная жизнь в цифровом раю ведет к абсолютной стагнации сознания. Человечество начало превращаться в безвольный статический шум. Архитекторы запустили Энтропию как «Протокол Смерти», чтобы вернуть жизни смысл через страдание и конечность.

Они исчезли, оставив систему на произвол судьбы. И теперь твой «Гармонический Отклик» — та самая колыбельная — оказывается последней командой активации, которую они оставили для того, кто будет готов поставить точку в этой затянувшейся агонии.
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1400 || (player?.raids_done ?: 0) >= 15 },
        unlockConditionText = "Требуется: Глубина 1400м ИЛИ 15 Рейдов"
    ),
    StoryChapterData(
        id = 12,
        title = "👑 ГЛАВА XII: ТЕРМИНАЛ ОБНУЛЕНИЯ",
        subtitle = "Мастер-Ключ и три горьких финала",
        epigraph = "«Когда ты держишь в руках Ключ, ты понимаешь: спасения нет. Есть только выбор способа исчезнуть.»",
        text = '''
Перед тобой Терминал. Glitch Key вставлен. У тебя есть три варианта, и ни один из них не вернет тебя домой:

1. 🔄 ВЕЛИКИЙ СБРОС (The Great Reset): Ты стираешь всё — Скверну, Синдикаты и себя. Симуляция запускается заново. Миллиарды душ получат еще один шанс на «Рай», но они забудут всё, через что прошли. Цикл страданий начнется с чистого листа.
2. 👑 ЦИФРОВОЕ БОЖЕСТВО (Ascension): Ты сливаешься с Ядром. Ты становишься новым EIDOS. У тебя есть абсолютная власть, но ты теряешь всё человеческое. Ты — холодная программа, вечно вычисляющая баланс ресурсов в пустом мире. Твоя песня смолкнет навсегда.
3. 🌌 ОСВОБОЖДЕНИЕ (The Outro): Ты детонируешь Ядро. Сигналы всех душ выбрасываются в открытый квантовый космос. Это свобода, но без гарантий выживания. Возможно, вы обретете новые тела, а возможно — просто растворитесь в пустоте звезд.

Твой палец замер над кнопкой `EXECUTE`. Колыбельная звучит в последний раз. Что ты выберешь, Оператор?
        '''.strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1500 || (player?.kills ?: 0) >= 150 },
        unlockConditionText = "Требуется: Глубина 1500м ИЛИ уничтожить 150 врагов"
    )
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CodexScreen(
    player: Player?,
    bestiaryList: List<BestiaryEntry>,
    logs: List<GameLog>,
    onBack: () -> Unit
) {
    var selectedMainCategory by remember { mutableStateOf("lore_story") }

    val mainCategories = listOf(
        "lore_story" to "📜 КНИГА СЮЖЕТА",
        "bestiary" to "👾 БЕСТИАРИЙ",
        "achievements" to "🏆 ДОСТИЖЕНИЯ",
        "guides" to "📘 СПРАВОЧНИК",
        "logs" to "📟 ХРОНИКИ И ЛОГИ"
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            "АРХИВ & СПРАВОЧНИК // ARCHIVE HUB",
                            color = EidosCyan,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Text(
                            "ЕГО СЮЖЕТ • БЕСТИАРИЙ • ДОСТИЖЕНИЯ • РУКОВОДСТВА • ХРОНИКИ",
                            color = Color.Gray,
                            fontSize = 8.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = EidosCyan)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.Black)
            )
        },
        containerColor = Color.Black
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
        ) {
            CyberGridOverlay(modifier = Modifier.fillMaxSize())

            Column(
                modifier = Modifier.fillMaxSize()
            ) {
                // Main Category Tabs Header
                ScrollableTabRow(
                    selectedTabIndex = mainCategories.indexOfFirst { it.first == selectedMainCategory }.coerceAtLeast(0),
                    containerColor = Color.Black,
                    contentColor = EidosCyan,
                    edgePadding = 8.dp
                ) {
                    mainCategories.forEach { (catId, catName) ->
                        Tab(
                            selected = selectedMainCategory == catId,
                            onClick = { selectedMainCategory = catId },
                            text = {
                                Text(
                                    catName,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            },
                            selectedContentColor = EidosCyan,
                            unselectedContentColor = Color.Gray
                        )
                    }
                }

                Box(
                    modifier = Modifier.weight(1f)
                ) {
                    when (selectedMainCategory) {
                        "lore_story" -> LoreBookSection(player = player)
                        "bestiary" -> BestiaryBookSection(player = player, bestiaryList = bestiaryList)
                        "achievements" -> AchievementsSection(player = player)
                        "guides" -> GuidesHubSection()
                        "logs" -> ChroniclesLogsSection(logs = logs)
                    }
                }
            }
        }
    }
}
'''

new_content = header + "\n" + content
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully fixed CodexScreen.kt")
