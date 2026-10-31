### 1. Fluid Sub-Pixel Matrix (Хирургические субпиксельные границы)
**Проблема:** Стандартное свойство `border: 1px solid` на флагманских дисплеях (iPhone Pro Max, S25 Ultra с `device-pixel-ratio: 3` и 450+ PPI) рендерится как 3 физических пикселя. Это делает рамки интерфейса толстыми, грубыми и лишает его премиальной "бритвенной" резкости.
**The "Ultra" Solution:** Использование медиазапросов плотности экрана для задания дробных значений бордера (`0.5px` или `0.33px`), либо использование векторного GPU-масштабирования псевдоэлементов, чтобы на холсте всегда отрисовывался ровно 1 физический пиксель матрицы.
**Technical Implementation (Exact CSS/JS):**
```css
/* Нативный подход для современных движков */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .nexus-tile, .modal-content {
    border-width: 0.5px;
  }
}
@media (-webkit-min-device-pixel-ratio: 3), (min-resolution: 288dpi) {
  .nexus-tile, .modal-content {
    border-width: 0.33px;
  }
}

/* Fallback-матрица через GPU для абсолютной стабильности */
.ultra-border {
  position: relative;
  border: none !important;
}
.ultra-border::after {
  content: "";
  position: absolute;
  top: 0; left: 0;
  width: 200%; height: 200%;
  border: 1px solid rgba(102, 252, 241, 0.4);
  transform-origin: 0 0;
  transform: scale(0.5); /* Сжимаем 1px на холсте 200% до 0.5px */
  pointer-events: none;
  border-radius: calc(var(--panel-radius) * 2);
}
```

### 2. Container-Aware Typography (Живая геометрия CQI)
**Проблема:** Использование `vw` (Viewport Width) или жестких `px` для шрифтов ломается, когда элементы (например, карточки предметов) меняют свой размер внутри разных контейнеров (сетка или список). Шрифты не знают о реальных размерах своего родителя.
**The "Ultra" Solution:** Отказ от глобальных Media Queries в пользу Container Queries (`@container`) и математической функции `clamp()`. Текст идеально масштабируется относительно своего непосредственного контейнера, обеспечивая идеальные пропорции и на iPhone Mini, и на S25 Ultra.
**Technical Implementation (Exact CSS/JS):**
```css
.items-list {
  container-type: inline-size;
  container-name: inventory-grid;
}

@container inventory-grid (min-width: 0px) {
  .inv-item-name {
    /* Мин: 12px, Идеал: 4% от ширины контейнера + 0.3rem, Макс: 16px */
    font-size: clamp(0.75rem, 4cqi + 0.3rem, 1rem);
    /* Идеальный технический интерлиньяж на базе высоты строчной буквы */
    line-height: calc(1ex / 0.32);
    letter-spacing: -0.02em;
  }
}
```

### 3. 120Hz GPU Glassmorphism (Аппаратное многопоточное стекло)
**Проблема:** Обилие тяжелых `backdrop-filter: blur(15px)` заставляет CPU перерисовывать размытие каждый кадр при скролле. На сложных панелях инвентаря это вызывает просадки FPS (Scroll Jank) и уничтожает плавность 120Hz экранов.
**The "Ultra" Solution:** Принудительное выделение стеклянных элементов в изолированный композитный слой GPU (`translateZ(0)`) и раннее оповещение браузера о возможных изменениях через `will-change`. Это переносит расчеты размытия на видеоускоритель смартфона.
**Technical Implementation (Exact CSS/JS):**
```css
.stats-header, .nexus-tile, .modal-content {
  background-color: rgba(5, 7, 10, 0.65);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);

  /* Форсируем Hardware Acceleration */
  transform: translateZ(0);
  backface-visibility: hidden;
  will-change: transform, opacity;
}
```

### 4. OLED Anti-Smearing Engine (Подавление черного шлейфа)
**Проблема:** При использовании `#000000` (Pure Black) пиксели OLED-матрицы полностью отключаются. При быстром скролле им требуются микросекунды на включение, что создает эффект тошнотворного фиолетового шлейфа (smearing) за яркими элементами.
**The "Ultra" Solution:** Внедрение "сигнального черного". Замена `#000000` на минимально светящийся оттенок, который держит субпиксели в постоянном напряжении (1-2% свечения), обеспечивая мгновенный отклик матрицы при 120Hz скроллинге без потери восприятия глубокого черного.
**Technical Implementation (Exact CSS/JS):**
```css
:root {
  /* Заменяем Pure Black на цвет, держащий пиксели включенными */
  --oled-deep-black: #020304;
  --eidos-bg: var(--oled-deep-black);
}

body {
  background-color: var(--eidos-bg);
}
```

### 5. Bezel Bleed Integration (Бесшовная интеграция вырезов)
**Проблема:** Контент либо обрезается Dynamic Island / челкой, либо для их обхода добавляются грубые черные `padding`, что убивает эффект безрамочности флагманов.
**The "Ultra" Solution:** Использование переменных среды `env(safe-area-inset-*)` для создания градиентных неоновых свечений, которые визуально "вытекают" из аппаратных вырезов, превращая мертвую зону экрана в элемент футуристичного дизайна.
**Technical Implementation (Exact CSS/JS):**
```css
.stats-header {
  /* Безопасный отступ */
  padding-top: max(env(safe-area-inset-top), 24px);

  /* Кибер-свечение, исходящее из-под Dynamic Island */
  background: radial-gradient(
    ellipse 150% 50% at 50% calc(env(safe-area-inset-top) * -0.5),
    rgba(102, 252, 241, 0.15) 0%,
    var(--eidos-glass) 100%
  );
}
```

### 6. Raster Asset Masking (Оптическая очистка растра)
**Проблема:** Загружаемые аватары Telegram часто имеют сильное сжатие. Рядом с кристально чистым векторным интерфейсом EIDOS они выглядят размытыми и чужеродными.
**The "Ultra" Solution:** Пропуск растра через пайплайн CSS-фильтров: обесцвечивание, жесткое повышение контраста, тонирование в системные цвета и обрезка строгим геометрическим `clip-path` с наложением внутренней тени для сокрытия лесенок.
**Technical Implementation (Exact CSS/JS):**
```css
.avatar {
  /* Оптимизация контраста браузером при скейлинге */
  image-rendering: -webkit-optimize-contrast;

  /* Цветовая нормализация: ЧБ -> Контраст -> Тонирование в циан */
  filter: grayscale(100%) contrast(1.3) sepia(100%) hue-rotate(135deg) brightness(0.8);

  /* Строгая геометрия вместо мыльного border-radius */
  clip-path: polygon(15% 0, 100% 0, 100% 85%, 85% 100%, 0 100%, 0 15%);
}

.avatar-wrapper::after {
  content: "";
  position: absolute; inset: 0;
  box-shadow: inset 0 0 15px rgba(0,0,0,0.9);
  pointer-events: none;
}
```

### 7. DVH Absolute Lock (Стабилизация Viewport'а)
**Проблема:** Использование `100vh` в Telegram WebApp приводит к тому, что при системных свайпах или появлении клавиатуры интерфейс дергается, так как реальная высота видимой области меняется.
**The "Ultra" Solution:** Использование `100dvh` (Dynamic Viewport Height) в связке с блокировкой нативного скролла `overscroll-behavior: none`. Это фиксирует внешний каркас приложения, делая его монолитным.
**Technical Implementation (Exact CSS/JS):**
```css
body, html {
  /* Жесткий лок с учетом динамических панелей ОС */
  height: 100dvh;
  min-height: -webkit-fill-available;

  overflow: hidden;
  /* Убийство резинового "баунса" iOS/Telegram */
  overscroll-behavior-y: none;
}

#views-container {
  height: 100dvh;
  padding-bottom: env(safe-area-inset-bottom, 20px);
}
```

### 8. PenTile Subpixel Smoothing (Антиалиасинг кибер-шрифтов)
**Проблема:** Технические шрифты (Rajdhani) на OLED-экранах с раскладкой PenTile выглядят зубчатыми или пересвеченными из-за субпиксельного гало.
**The "Ultra" Solution:** Переопределение алгоритмов сглаживания текста на уровне движка рендеринга macOS/iOS. Отключение субпиксельного сглаживания делает светлый текст на темном фоне идеально тонким и резким.
**Technical Implementation (Exact CSS/JS):**
```css
* {
  /* Переход на grayscale-сглаживание (убирает цветные ореолы вокруг букв) */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;

  /* Включение микро-кернинга для плотных технических логов */
  text-rendering: optimizeLegibility;
}
```

### 9. DOM CSS Containment (Блокировка каскадных фризов)
**Проблема:** Когда JS обновляет статы (добавляет класс `.stat-up`) или перестраивает инвентарь, браузер пересчитывает Layout всего дерева страницы, что вызывает дропы кадров.
**The "Ultra" Solution:** Использование свойства `contain`, которое изолирует поддеревья. Изменения внутри одной ячейки сетки не заставят браузер проверять, не съехали ли соседние элементы.
**Technical Implementation (Exact CSS/JS):**
```css
.nexus-tile, .items-list {
  /* Строгая изоляция от родительского DOM */
  contain: strict;
}

.inv-item {
  /* Виртуализация невидимых элементов */
  content-visibility: auto;
  contain-intrinsic-size: 80px;
}
```

### 10. Hardware Momentum Snap (Физический магнетизм списков)
**Проблема:** Длинные списки логов или инвентаря скроллятся вязко и останавливаются хаотично, между элементами. Это разрушает тактильное ощущение дорогого приложения.
**The "Ultra" Solution:** Внедрение аппаратного магнетизма (`scroll-snap`) с привязкой к физическим пикселям и инерционным замедлением (`Momentum Scrolling`).
**Technical Implementation (Exact CSS/JS):**
```css
.scroll-area {
  overflow-y: scroll;
  /* Аппаратная инерция iOS */
  -webkit-overflow-scrolling: touch;

  /* Настройка магнитного прилипания */
  scroll-snap-type: y mandatory;
  scroll-padding-top: max(env(safe-area-inset-top), 20px);
}

.nexus-tile {
  scroll-snap-align: start;
  scroll-snap-stop: always;
}
```
