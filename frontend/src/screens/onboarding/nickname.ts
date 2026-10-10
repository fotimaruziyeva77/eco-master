import type { Language } from "../../i18n/languages";

// Mirrors backend/app/nickname.py so most mistakes are caught before a request.
const LATIN = /^[A-Za-z0-9_]+$/;
const CYRILLIC = /^[А-Яа-яЁёЎўҚқҒғҲҳ0-9_]+$/;
const LETTER = /[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ]/;

export function nicknameFormatError(value: string): string | null {
  const nickname = value.trim();
  if (nickname.length < 3 || nickname.length > 20) return "nickname_length";
  if (!(LATIN.test(nickname) || CYRILLIC.test(nickname)) || !LETTER.test(nickname)) {
    return "nickname_chars";
  }
  return null;
}

const WORDS: Record<Language, { first: string[]; second: string[] }> = {
  uz: {
    first: ["Yashil", "Quyoshli", "Ziyrak", "Chaqqon", "Mehribon", "Toza"],
    second: ["Barg", "Daraxt", "Lola", "Bulbul", "Chinor", "Sayyora"],
  },
  ru: {
    first: ["Зелёный", "Солнечный", "Быстрый", "Добрый", "Умный", "Чистый"],
    second: ["Лист", "Дуб", "Тигр", "Лис", "Кедр", "Ёж"],
  },
  en: {
    first: ["Green", "Sunny", "Smart", "Quick", "Kind", "Clean"],
    second: ["Leaf", "Tree", "Tiger", "Panda", "Cedar", "Planet"],
  },
};

const pick = <T>(items: T[]): T => items[Math.floor(Math.random() * items.length)];

export function randomNickname(language: Language): string {
  const words = WORDS[language];
  const number = Math.floor(Math.random() * 90) + 10;
  return `${pick(words.first)}_${pick(words.second)}_${number}`;
}
