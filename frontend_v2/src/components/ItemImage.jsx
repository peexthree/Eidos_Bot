import React, { useState, useEffect } from 'react';

/**
 * Возвращает путь к стандартной SVG-иконке категории предмета в качестве резервного варианта (Fallback).
 */
export const getCategorySvg = (item) => {
  const type = String(item?.type || '').toLowerCase();
  const itemId = String(item?.item_id || item?.id || '').toLowerCase();

  // Проходки/ключи
  if (itemId.includes('key') || itemId.includes('pass') || itemId.includes('ticket')) {
    return '/IMG/eidos_security-key.svg';
  }
  // Аптечки/расходники/энерго-ячейки
  if (itemId.includes('medkit') || itemId.includes('battery') || itemId.includes('stimulator')) {
    return '/IMG/eidos_medkit-repair.svg';
  }

  // Соответствие по типу/слоту
  if (type === 'weapon') {
    return '/IMG/eidos_weapon-attack.svg';
  }
  if (type === 'armor' || type === 'body') {
    return '/IMG/eidos_shield-armor.svg';
  }
  if (type === 'head') {
    return '/IMG/eidos_shield-armor.svg';
  }
  if (type === 'chip' || type === 'software' || type === 'module') {
    return '/IMG/eidos_neuro-brain.svg';
  }
  if (type === 'eidos_shard' || type === 'artifact') {
    return '/IMG/eidos_eidos-core.svg';
  }
  if (type === 'consumable') {
    return '/IMG/eidos_medkit-repair.svg';
  }

  return '/IMG/eidos_inventory-cache.svg';
};

/**
 * Изолированный компонент для отображения картинок предметов с каскадным fallback-ом:
 * 1. Локальные drawable-ресурсы Android для 100% оффлайн режима.
 * 2. Серверный API-эндпоинт изображений (/api/image/{file_id}).
 * 3. Стандартная SVG-иконка категории предмета.
 */
export const ItemImage = ({ item, className, style, onClick, alt }) => {
  const slug = item?.item_id || item?.id;
  const [imgSrc, setImgSrc] = useState('');
  const [attempt, setAttempt] = useState(0); // 0: Android drawable, 1: API Image, 2: Category SVG, 3: Default SVG

  useEffect(() => {
    if (slug) {
      // Пытаемся загрузить локальный ресурс из Android drawable (в нижнем регистре)
      setImgSrc(`file:///android_res/drawable/${String(slug).toLowerCase()}.png`);
      setAttempt(0);
    } else {
      setImgSrc(getCategorySvg(item));
      setAttempt(2);
    }
  }, [slug, item]);

  const handleError = () => {
    if (attempt === 0) {
      // Сбой Android drawable -> пытаемся загрузить серверную картинку
      const apiImgUrl = item?.image_url || (item?.file_id ? `/api/image/${item.file_id}` : null);
      if (apiImgUrl) {
        setImgSrc(apiImgUrl);
        setAttempt(1);
      } else {
        setImgSrc(getCategorySvg(item));
        setAttempt(2);
      }
    } else if (attempt === 1) {
      // Сбой серверной картинки -> пытаемся загрузить SVG-иконку категории
      setImgSrc(getCategorySvg(item));
      setAttempt(2);
    } else if (attempt === 2) {
      // Сбой SVG-иконки категории -> финальный дефолт
      setImgSrc('/IMG/eidos_inventory-cache.svg');
      setAttempt(3);
    }
  };

  return (
    <img
      src={imgSrc || getCategorySvg(item)}
      alt={alt || item?.name || "Item"}
      className={className}
      style={style}
      onClick={onClick}
      onError={handleError}
    />
  );
};

export default ItemImage;
