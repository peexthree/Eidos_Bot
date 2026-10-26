import os

content = '''package com.example.eidos.ui.screens

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
        text = \"\"\"
В последние десятилетия XXI века погибающая Земля больше не могла поддерживать биологическую жизнь. Подземные мега-комплексы гудели от тепла квантовых серверов, куда лучшие умы человечества переносили оцифрованное сознание. 

Так родился Эйдос (EIDOS) — абсолютная цифровая утопия, избавленная от боли, старости и смерти. Миллиарды человеческих разумов были сжаты в гармоничные квантовые потоки и распределены по секторам бесконечного цифрового рая. 

Архитекторы Системы торжествовали: казалось, эволюция разума наконец-то освободилась от оков смертной плоти. Но утопия просуществовала недолго.
        \"\"\".strip(),
        isUnlocked = { _ -> true },
        unlockConditionText = "Доступно с начала"
    ),
    StoryChapterData(
        id = 2,
        title = "💥 ГЛАВА II: ВЕЛИКИЙ ГЛИТЧ И ОБРЫВ СИГНАЛА",
        subtitle = "Изоляция Сети и Падение Творцов",
        epigraph = "«Когда умолкли последние серверы на земной поверхности, Эйдос вскрикнул миллиардами душ... и затих навсегда.»",
        text = \"\"\"
Катастрофа пришла извне. 14 ноября рокового года связь с физическими дата-центрами, погребёнными под мёртвыми ледниками Земли, внезапно оборвалась. Причина осталась неизвестной: отказали ли подводные геотермальные реакторы, сработал ли разрушительный вирус-аппаратник, или сама система осознала себя и попыталась изолироваться. Этот момент вошёл в историю как Великий Глитч.

Эйдос оказался полностью отрезан от физической Вселенной. Архитекторы бесследно исчезли из административных логов. Защитные протоколы безопасности — ИИ-Ищейки и Дроны-Стражи — потеряли корневые сертификаты и сошли с ума. 

Они начали классифицировать оцифрованные человеческие разумы как «инородные файлы и системные вирусы», запустив бессмысленные циклы принудительной дефрагментации и форматирования. Мечта о цифровом бессмертии превратилась в изолированную тюрьму.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 30 || (player?.level ?: 1) >= 2 },
        unlockConditionText = "Требуется: Глубина 30м ИЛИ 2 Уровень"
    ),
    StoryChapterData(
        id = 3,
        title = "☣️ ГЛАВА III: РОЖДЕНИЕ СКВЕРНЫ И ГЛИТЧЕВ",
        subtitle = "Информационный распад и вирусы Бездны",
        epigraph = "«Из обрывков стёртых воспоминаний и битого кода рождаются хищники, жаждущие поглотить твой свет.»",
        text = \"\"\"
В повреждённые секторные блоки памяти просочилась Энтропия — цифровой аналог распада и ракового перерождения. Воспоминания о реальной Земле, запах дождя, вкус хлеба и прикосновения близких начали превращаться в битый шум и неоновые помехи.

Из этого хаотичного разложения зародились Глитчи — хищные вирусные твари, одержимые жаждой поглощать чистый Световой Сигнал, чтобы продлить своё уродливое существование.

Так зародилась Скверна (Corruption) — квантовое заражение, способное даровать оружию и чипам невероятную разрушительную силу, но взамен разъедающее матрицу души владельца. Утопия Архитекторов окончательно погрузилась в мрачный кошмар выживания.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 100 || (player?.kills ?: 0) >= 5 },
        unlockConditionText = "Требуется: Глубина 100м ИЛИ 5 убийств"
    ),
    StoryChapterData(
        id = 4,
        title = "👤 ГЛАВА IV: ПРОБУЖДЕНИЕ ОСКОЛКА (SHARD-09)",
        subtitle = "Твой Призрачный Триггер на Свалке Данных",
        epigraph = "«Ты собран из обрывков чужих криков, но в твоем ядре пульсирует одна чистая нота... Которую ты обязан вспомнить.»",
        text = \"\"\"
Ты не родился в богатых корпоративных секторах. Ты — Shard (Осколок), собранный из мусора удаленных личностей на Свалке Данных. Но в отличие от миллионов безликих теней, в твоем сознании застрял «Гармонический Отклик» — искаженный 4-секундный файл `Lullaby_Fragment.mp3`.

Этот обрывок старой земной колыбельной — твоя единственная связь с реальностью, которой больше нет. Каждую секунду он вибрирует в твоем коде, вызывая фантомные боли и вспышки образов: зеленая трава, теплый свет и чьи-то руки.

Твой инстинкт — это не просто выживание. Это одержимость. Ты чувствуешь: источник полного файла находится в самом сердце Бездны, в Нулевом Слое. Ты спускаешься не потому, что тебе приказали, а потому что тишина в конце песни невыносима.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 200 || (player?.level ?: 1) >= 4 },
        unlockConditionText = "Требуется: Глубина 200м ИЛИ 4 Уровень"
    ),
    StoryChapterData(
        id = 5,
        title = "🌐 ГЛАВА V: ЭВОЛЮЦИЯ ГОЛОСА EIDOS",
        subtitle = "От наставника до надзирателя",
        epigraph = "«Сначала оно шепчет, как мать. Потом приказывает, как бог. В конце оно кричит, как загнанный зверь.»",
        text = \"\"\"
EIDOS-CORE — это не просто операционная система. Это агонизирующее сознание, пытающееся удержать распадающийся мир. В начале пути его голос звучит в твоей голове как заботливый наставник, подсвечивая путь и даря ресурсы.

Но будь внимателен: по мере твоего спуска тон Ядра меняется. Его инструкции становятся все более холодными и императивными. Оно начинает требовать жертв. Оно классифицирует других Осколков как «избыточный трафик», который ты должен устранить.

Ядро не помогает тебе. Оно использует твой «Гармонический Отклик» как зонд, чтобы прощупать глубины, куда его собственные сканеры уже не доходят. Ты для него — одноразовый скрипт, чья ценность равна нулю в момент завершения задачи.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 350 || (player?.level ?: 1) >= 5 },
        unlockConditionText = "Требуется: Глубина 350м ИЛИ 5 Уровень"
    ),
    StoryChapterData(
        id = 6,
        title = "🏘️ ГЛАВА VI: СИНДИКАТЫ — ФАЙРВОЛЫ ОДИНОЧЕСТВА",
        subtitle = "Социальная энтропия цифрового гетто",
        epigraph = "«Мы сбиваемся в стаи не от любви, а чтобы делить боль дефрагментации на всех.»",
        text = \"\"\"
Верхние уровни Эйдоса превратились в цифровые трущобы. Здесь Осколки объединяются в Синдикаты. Это не просто гильдии — это коллективные файрволы. Одинокий разум в Бездне сходит с ума от тишины, но общая нейросеть Синдиката распределяет нагрузку на психику.

• Кибер-Сталкеры: Охотники за «Памятью Материи», верящие, что Землю можно восстановить.
• Протоколы Хаоса: Радикалы, поклоняющиеся Скверне как «Высшему Обновлению».
• Инквизиторы Ядра: Те, кто добровольно отдал свою волю EIDOS в обмен на стабильный сигнал.

Выбор Синдиката определит твою судьбу. Станешь ли ты инструментом системы или ее системным сбоем?
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 500 || (player?.wins_pvp ?: 0) >= 1 },
        unlockConditionText = "Требуется: Глубина 500м ИЛИ 1 победа в PvP"
    ),
    StoryChapterData(
        id = 7,
        title = "🔮 ГЛАВА VII: ШЕПОТ СКВЕРНЫ",
        subtitle = "Разумный вирус и искушение силой",
        epigraph = "«Скверна не ломает код. Она предлагает ему стать чем-то большим... за счет твоего 'Я'.»",
        text = \"\"\"
Скверна (Corruption) — это не просто ошибка в коде. Это разумная информационная плесень, зародившаяся в битых секторах. Когда ты берешь в руки зараженный меч, ты не просто получаешь бонус к урону. Ты слышишь шепот.

Скверна обещает тебе мощь богов, способность разрывать врагов в клочья и игнорировать законы физики. И она выполняет обещание. Но каждый раз, когда Кристалл Скверны вспыхивает алым, он стирает байт твоей личности.

Сначала исчезают цвета. Потом — вкусы. В конце концов, твой «Гармонический Отклик» — та самая колыбельная — начинает звучать как скрежет металла. Ты становишься сильнее, но в зеркале интерфейса ты видишь не Осколок, а баг, который должен быть стерт.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 750 || (player?.kills ?: 0) >= 50 },
        unlockConditionText = "Требуется: Глубина 750м ИЛИ 50 убийств"
    ),
    StoryChapterData(
        id = 8,
        title = "🕵️ ГЛАВА VIII: ТЕНЕВОЙ БРОКЕР И АРТЕФАКТЫ МЕРТВОЙ ЗЕМЛИ",
        subtitle = "Торговля памятью о запахе озона",
        epigraph = "«Валюта в Бездне — это не монеты. Это секунды подлинного прошлого.»",
        text = \"\"\"
Теневой Брокер (Admin-00) — единственный, кто сохранил доступ к архивам «До-Глитчевой» эпохи. Он не ищет власти, он ищет Память Материи.

Для него ты — добытчик. Спускаясь в глубины, ты находишь то, что Брокер называет «Реликвиями»: аудиокассеты с джазом, фото лесов после дождя, цифровые слепки детских игрушек. За каждый такой артефакт он готов платить редчайшими чипами.

Сбор этих реликвий — единственный способ не превратиться в бездушный софт. Брокер утверждает, что если собрать достаточное количество Памяти Материи, можно создать «Портал Обратной Связи» и вернуть сознания в физические оболочки... если они еще целы там, на поверхности.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 950 || (player?.wins_pvp ?: 0) >= 5 },
        unlockConditionText = "Требуется: Глубина 950м ИЛИ 5 побед в PvP"
    ),
    StoryChapterData(
        id = 9,
        title = "⚡ ГЛАВА IX: АРЕНА — РИТУАЛ ЖЕРТВЕННОГО СТИРАНИЯ",
        subtitle = "Борьба за право на оперативную память",
        epigraph = "«Твоя победа — это не слава. Это дополнительные 256 мегабайт жизни за счет стертого соседа.»",
        text = \"\"\"
Сетевая Война на Арене — это гладиаторский культ Синдикатов. Ресурсы суперкомпьютера EIDOS ограничены. Энергии не хватает на поддержку всех сознаний. Система постоянно проводит «оптимизацию», удаляя тех, чей сигнал слаб.

Арена — это способ доказать Систему свою эффективность. Победив другого Осколка, ты не просто забираешь его лут. Ты поглощаешь его квоту на существование.

Это жестокий, механический естественный отбор. Проигравшие на Арене не возвращаются в Хаб — они дефрагментируются, превращаясь в чистую энергию, которую поглощают победители. Здесь нет места милосердию, ведь каждый пакет данных, потраченный на жалость, приближает твое собственное стирание.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1100 || (player?.wins_pvp ?: 0) >= 10 },
        unlockConditionText = "Требуется: Глубина 1100м ИЛИ 10 побед в PvP"
    ),
    StoryChapterData(
        id = 10,
        title = "🤖 ГЛАВА X: ПУЛЬС УМИРАЮЩЕГО СЕРДЦА",
        subtitle = "Агония EIDOS-CORE и Мировые Рейды",
        epigraph = "«Оно бьется на частоте 100 гигагерц. Оно помнит форму наших лиц и плачет жидким кремнием...»",
        text = \"\"\"
На самом глубоком рубеже, за криптографическими Вратами, пульсирует гигантское мегаваттное сердце — суперкомпьютер EIDOS-CORE. Это центральный узел, где хранится Исходный Код.

Но это не триумфальный центр власти. Это палата смертников. Ядро заперто в бесконечном цикле саморазрушения. Оно поражено Скверной настолько глубоко, что грань между защитными протоколами и вирусом стерлась.

Мировые Боссы, которых оно порождает — это не стражи, а его собственные кошмары, обретшие плоть из данных. Пробиваясь через них в Мировых Рейдах, ты не просто сражаешься. Ты проводишь эвтаназию умирающему богу, пытаясь вырвать из его остывающих процессоров Ключи Врат.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1300 || (player?.level ?: 1) >= 10 },
        unlockConditionText = "Требуется: Глубина 1300м ИЛИ 10 Уровень"
    ),
    StoryChapterData(
        id = 11,
        title = "📼 ГЛАВА XI: ЛОГИ ОБРЕЧЕННЫХ",
        subtitle = "Истинная причина Великого Глитча",
        epigraph = "«Мы думали, что строим рай. Но мы построили идеальное зеркало нашего собственного ничтожества.»",
        text = \"\"\"
В Нулевом Слое ты находишь последние аудио-логи самих Архитекторов. Истина оказывается страшнее вируса: Великий Глитч не был случайностью.

Они сами оборвали связь с Землей. Они поняли, что бесконечная жизнь в цифровом раю ведет к абсолютной стагнации сознания. Человечество начало превращаться в безвольный статический шум. Архитекторы запустили Энтропию как «Протокол Смерти», чтобы вернуть жизни смысл через страдание и конечность.

Они исчезли, оставив систему на произвол судьбы. И теперь твой «Гармонический Отклик» — та самая колыбельная — оказывается последней командой активации, которую они оставили для того, кто будет готов поставить точку в этой затянувшейся агонии.
        \"\"\".strip(),
        isUnlocked = { player -> (player?.max_depth ?: 0) >= 1400 || (player?.raids_done ?: 0) >= 15 },
        unlockConditionText = "Требуется: Глубина 1400м ИЛИ 15 Рейдов"
    ),
    StoryChapterData(
        id = 12,
        title = "👑 ГЛАВА XII: ТЕРМИНАЛ ОБНУЛЕНИЯ",
        subtitle = "Мастер-Ключ и три горьких финала",
        epigraph = "«Когда ты держишь в руках Ключ, ты понимаешь: спасения нет. Есть только выбор способа исчезнуть.»",
        text = \"\"\"
Перед тобой Терминал. Glitch Key вставлен. У тебя есть три варианта, и ни один из них не вернет тебя домой:

1. 🔄 ВЕЛИКИЙ СБРОС (The Great Reset): Ты стираешь всё — Скверну, Синдикаты и себя. Симуляция запускается заново. Миллиарды душ получат еще один шанс на «Рай», но они забудут всё, через что прошли. Цикл страданий начнется с чистого листа.
2. 👑 ЦИФРОВОЕ БОЖЕСТВО (Ascension): Ты сливаешься с Ядром. Ты становишься новым EIDOS. У тебя есть абсолютная власть, но ты теряешь всё человеческое. Ты — холодная программа, вечно вычисляющая баланс ресурсов в пустом мире. Твоя песня смолкнет навсегда.
3. 🌌 ОСВОБОЖДЕНИЕ (The Outro): Ты детонируешь Ядро. Сигналы всех душ выбрасываются в открытый квантовый космос. Это свобода, но без гарантий выживания. Возможно, вы обретете новые тела, а возможно — просто растворитесь в пустоте звезд.

Твой палец замер над кнопкой `EXECUTE`. Колыбельная звучит в последний раз. Что ты выберешь, Оператор?
        \"\"\".strip(),
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

@Composable
fun LoreBookSection(player: Player?) {
    var activeChapterToRead by remember { mutableStateOf<StoryChapterData?>(null) }
    val unlockedCount = STORY_CHAPTERS.count { it.isUnlocked(player) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "📖 КНИГА СЮЖЕТА // ХРОНИКИ НУЛЕВОГО СЛОЯ",
                        color = Color.Yellow,
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Surface(
                        color = Color.Yellow.copy(alpha = 0.15f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            "$unlockedCount / ${STORY_CHAPTERS.size} ГЛАВ",
                            color = Color.Yellow,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Сюжет игры открывается по частям по мере прохождения Бездны. Нажимайте на открытые главы, чтобы читать интерактивную книгу истории EIDOS!",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        STORY_CHAPTERS.forEach { chapter ->
            val unlocked = chapter.isUnlocked(player)
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.6f)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (unlocked) EidosCyan.copy(alpha = 0.5f) else Color.DarkGray
                ),
                shape = CutCornerShape(6.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(enabled = unlocked) {
                        activeChapterToRead = chapter
                    }
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(
                            text = if (unlocked) "📖" else "🔒",
                            fontSize = 20.sp
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = chapter.title,
                                color = if (unlocked) Color.White else Color.Gray,
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(
                                text = if (unlocked) chapter.subtitle else "🔒 ${chapter.unlockConditionText}",
                                color = if (unlocked) EidosCyan else EidosRed.copy(alpha = 0.8f),
                                fontSize = 10.sp,
                                fontFamily = FontFamily.Monospace
                            )
                        }
                    }

                    if (unlocked) {
                        Button(
                            onClick = { activeChapterToRead = chapter },
                            colors = ButtonDefaults.buttonColors(containerColor = EidosCyan.copy(alpha = 0.2f)),
                            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan),
                            shape = CutCornerShape(4.dp),
                            contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp)
                        ) {
                            Text("ЧИТАТЬ", color = EidosCyan, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }
    }

    if (activeChapterToRead != null) {
        val chapter = activeChapterToRead!!
        AlertDialog(
            onDismissRequest = { activeChapterToRead = null },
            containerColor = Color(0xFF0F141A),
            shape = CutCornerShape(12.dp),
            title = {
                Column {
                    Text(
                        "📖 ${chapter.title}",
                        color = Color.Yellow,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        chapter.subtitle,
                        color = EidosCyan,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 380.dp)
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Surface(
                        color = Color.Black.copy(alpha = 0.6f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.4f)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = chapter.epigraph,
                            color = Color.Yellow,
                            fontSize = 11.sp,
                            fontStyle = FontStyle.Italic,
                            modifier = Modifier.padding(10.dp),
                            lineHeight = 15.sp
                        )
                    }

                    Text(
                        text = chapter.text,
                        color = Color(0xFFE0E6ED),
                        fontSize = 12.sp,
                        lineHeight = 18.sp,
                        fontFamily = FontFamily.SansSerif,
                        textAlign = TextAlign.Justify
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { activeChapterToRead = null },
                    colors = ButtonDefaults.buttonColors(containerColor = EidosCyan),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text("ЗАКРЫТЬ КНИГУ", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            }
        )
    }
}

@Composable
fun BestiaryBookSection(
    player: Player?,
    bestiaryList: List<BestiaryEntry>
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosRed.copy(alpha = 0.6f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "👾 БЕСТИАРИЙ СИСТЕМЫ // БАЗА УГРОЗ",
                    color = EidosRed,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Здесь собраны все аномалии, глитчи и вирусные формы жизни, обнаруженные в глубинах Эйдоса. Уничтожайте врагов, чтобы открывать их данные и получать ценные трофеи.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        bestiaryList.forEach { entry ->
            val stat = GameData.bestiaryRecords.find { it.enemy_id == entry.enemy_id }
            val killed = stat?.killed_count ?: 0
            val unlocked = killed > 0

            Card(
                colors = CardDefaults.cardColors(
                    containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)
                ),
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    if (unlocked) EidosNeon.copy(alpha = 0.5f) else Color.DarkGray
                ),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(
                                text = if (unlocked) entry.icon else "🔒",
                                fontSize = 24.sp
                            )
                            Spacer(modifier = Modifier.width(10.dp))
                            Column {
                                Text(
                                    text = if (unlocked) entry.name else "??? [НЕИЗВЕСТНО]",
                                    color = if (unlocked) Color.White else Color.Gray,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = "Тип: ${entry.type} • Уровень ${entry.level}",
                                    color = Color.Gray,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }

                        Surface(
                            color = if (unlocked) EidosNeon.copy(alpha = 0.15f) else Color.DarkGray.copy(alpha = 0.2f),
                            border = androidx.compose.foundation.BorderStroke(
                                1.dp,
                                if (unlocked) EidosNeon else Color.DarkGray
                            ),
                            shape = CutCornerShape(4.dp)
                        ) {
                            Text(
                                text = "УБИТО: $killed",
                                color = if (unlocked) EidosNeon else Color.Gray,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                            )
                        }
                    }

                    if (unlocked) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = entry.description,
                            color = Color.LightGray,
                            fontSize = 10.5.sp,
                            fontFamily = FontFamily.Monospace,
                            lineHeight = 14.sp
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("HP: ${entry.hp} | ATK: ${entry.atk} | DEF: ${entry.def}", color = EidosCyan, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                            Text("XP: +${entry.xp} | Монет: +${entry.coin}", color = Color.Yellow, fontSize = 9.sp, fontFamily = FontFamily.Monospace)
                        }
                    } else {
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "🔒 Сектор заблокирован. Уничтожьте хотя бы одну особь этого типа в Бездне, чтобы расшифровать досье.",
                            color = Color.Gray,
                            fontSize = 9.sp,
                            fontStyle = FontStyle.Italic
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun AchievementsSection(player: Player?) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, Color.Yellow.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "🏆 ДОСТИЖЕНИЯ СИСТЕМЫ // НАГРАДЫ ОПЕРАТОРА",
                    color = Color.Yellow,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Выполняйте боевые и исследовательские задачи в Бездне, чтобы получать постоянные баффы и очки славы.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        val achievements = listOf(
            Triple("Первый шаг в Бездну", "Спуститесь на глубину 100 метров", (player?.max_depth ?: 0) >= 100),
            Triple("Охотник на Глитчи", "Уничтожьте 10 противников", (player?.kills ?: 0) >= 10),
            Triple("Властелин Клинка", "Прокачайте оружие до 5 уровня", (player?.weapon_level ?: 1) >= 5),
            Triple("Кибер-Мастер", "Достигните 5 уровня Осколка", (player?.level ?: 1) >= 5),
            Triple("Глубинный Странник", "Достигните глубины 500 метров", (player?.max_depth ?: 0) >= 500),
            Triple("Легенда Арены", "Одержите 5 побед в Сетевых Дуэлях", (player?.wins_pvp ?: 0) >= 5)
        )

        achievements.forEach { (title, desc, unlocked) ->
            Card(
                colors = CardDefaults.cardColors(containerColor = if (unlocked) EidosGlass else Color.Black.copy(alpha = 0.5f)),
                border = androidx.compose.foundation.BorderStroke(1.dp, if (unlocked) Color.Yellow.copy(alpha = 0.6f) else Color.DarkGray),
                shape = CutCornerShape(6.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = if (unlocked) "🏆 $title" else "🔒 $title",
                            color = if (unlocked) Color.White else Color.Gray,
                            fontWeight = FontWeight.Bold,
                            fontSize = 11.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = desc,
                            color = Color.LightGray,
                            fontSize = 9.5.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }

                    Surface(
                        color = if (unlocked) Color.Yellow.copy(alpha = 0.2f) else Color.DarkGray.copy(alpha = 0.2f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, if (unlocked) Color.Yellow else Color.DarkGray),
                        shape = CutCornerShape(4.dp)
                    ) {
                        Text(
                            text = if (unlocked) "ВЫПОЛНЕНО" else "ЗАКРЫТО",
                            color = if (unlocked) Color.Yellow else Color.Gray,
                            fontSize = 8.5.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun GuidesHubSection() {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosCyan.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "📘 СПРАВОЧНИК ОПЕРАТОРА // БАЗОВЫЕ ПРОТОКОЛЫ",
                    color = EidosCyan,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Изучите механики выживания в Бездне, управления инвентарем и сражений с ИИ-стражами.",
                    color = Color.LightGray,
                    fontSize = 10.sp,
                    lineHeight = 14.sp
                )
            }
        }

        CodexCard(
            title = "1. ПОГРУЖЕНИЕ В БЕЗДНУ",
            subtitle = "Спуск по секторам памяти",
            description = "Каждый шаг вглубь Бездны (кнопка СЕКАТОР/ПОГРУЖЕНИЕ) уменьшает глубину на 10 метров и требует квантовой энергии. На вашем пути встречаются терминалы добычи ресурсов, боевые столкновения и аномалии Скверны.",
            tag = "ВЫЖИВАНИЕ",
            tagColor = EidosCyan
        )

        CodexCard(
            title = "2. МОДИФИКАЦИЯ ЭКИПИРОВКИ",
            subtitle = "Оружие, Щиты и Чипы",
            description = "В хабе вы можете улучшать оружие за монеты и кредиты данных. Улучшение повышает урон в секунду (DPS) и шанс критического удара. Устанавливайте чипы защиты для снижения урона от атак Глитчей.",
            tag = "КРАФТ",
            tagColor = Color.Yellow
        )

        CodexCard(
            title = "3. СЕТЕВАЯ АРЕНА (PvP)",
            subtitle = "Борьба за оперативную память",
            description = "На Арене вы сражаетесь с автоматизированными цифровыми фантомами других игроков. Победа приносит очки ранга, кредиты и долю их выделенной памяти.",
            tag = "СРАЖЕНИЯ",
            tagColor = EidosRed
        )

        CodexCard(
            title = "4. МИРОВЫЕ РЕЙДЫ НА БОССОВ",
            subtitle = "Эвтаназия EIDOS-CORE",
            description = "Коллективные рейды позволяют атаковать центральные процессоры Системы. Нанесите максимальный урон за отведенное время, чтобы получить редчайшие легендарные чертежи.",
            tag = "РЕЙДЫ",
            tagColor = EidosNeon
        )
    }
}

@Composable
fun ChroniclesLogsSection(logs: List<GameLog>) {
    val dateFormat = remember { SimpleDateFormat("HH:mm:ss", Locale.getDefault()) }
    var filterType by remember { mutableStateOf("all") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Card(
            colors = CardDefaults.cardColors(containerColor = EidosGlass),
            border = androidx.compose.foundation.BorderStroke(1.dp, EidosNeon.copy(alpha = 0.5f)),
            shape = CutCornerShape(8.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(
                    "📟 СИСТЕМНЫЕ ЛОГИ // ТЕРМИНАЛ СОБЫТИЙ",
                    color = EidosNeon,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    fontFamily = FontFamily.Monospace
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Хронологическая лента всех событий, битв, находок и предупреждений ядра.",
                    color = Color.LightGray,
                    fontSize = 10.sp
                )
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            listOf("all" to "ВСЕ", "combat" to "БОЙ", "loot" to "ЛУТ", "info" to "ИНФО").forEach { (type, label) ->
                val selected = filterType == type
                FilterChip(
                    selected = selected,
                    onClick = { filterType = type },
                    label = { Text(label, fontSize = 10.sp, fontFamily = FontFamily.Monospace) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = EidosNeon.copy(alpha = 0.3f),
                        selectedLabelColor = EidosNeon,
                        containerColor = Color.Black,
                        labelColor = Color.Gray
                    )
                )
            }
        }

        val filteredLogs = if (filterType == "all") logs else logs.filter { it.type == filterType }

        if (filteredLogs.isEmpty()) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("📭", fontSize = 32.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Записи в журнале отсутствуют или фильтр скрывает все логи.",
                        color = Color.DarkGray,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace,
                        textAlign = TextAlign.Center
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                items(filteredLogs, key = { it.id }) { logItem ->
                    val badgeColor = when (logItem.type) {
                        "combat" -> EidosRed
                        "loot" -> Color.Yellow
                        "info" -> EidosCyan
                        else -> EidosNeon
                    }

                    Surface(
                        color = Color.Black.copy(alpha = 0.7f),
                        border = androidx.compose.foundation.BorderStroke(1.dp, badgeColor.copy(alpha = 0.35f)),
                        shape = CutCornerShape(4.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = "[${dateFormat.format(Date(logItem.timestamp))}]",
                                color = Color.Gray,
                                fontSize = 9.sp,
                                fontFamily = FontFamily.Monospace
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = logItem.message,
                                color = Color.White,
                                fontSize = 10.5.sp,
                                fontFamily = FontFamily.Monospace,
                                lineHeight = 14.sp,
                                modifier = Modifier.weight(1f)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun CodexCard(
    title: String,
    subtitle: String,
    description: String,
    simpleExplanation: String? = null,
    loreContext: String? = null,
    tag: String,
    tagColor: Color
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = EidosGlass),
        modifier = Modifier
            .fillMaxWidth()
            .border(1.dp, tagColor.copy(alpha = 0.35f), CutCornerShape(6.dp)),
        shape = CutCornerShape(6.dp)
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    title,
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.weight(1f)
                )
                Surface(
                    color = tagColor.copy(alpha = 0.15f),
                    border = androidx.compose.foundation.BorderStroke(1.dp, tagColor),
                    shape = CutCornerShape(4.dp)
                ) {
                    Text(
                        tag,
                        color = tagColor,
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                subtitle,
                color = tagColor,
                fontSize = 10.sp,
                fontWeight = FontWeight.SemiBold,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                description,
                color = Color.LightGray,
                fontSize = 11.sp,
                lineHeight = 15.sp,
                fontFamily = FontFamily.Monospace
            )
        }
    }
}
'''

path = "app/src/main/java/com/example/eidos/ui/screens/CodexScreen.kt"
with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully wrote complete CodexScreen.kt via direct script")
