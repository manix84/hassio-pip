import { de } from "./de";
import { en } from "./en";
import { es } from "./es";
import { fr } from "./fr";
import { it } from "./it";
import { nl } from "./nl";
import { pl } from "./pl";
import { ptbr } from "./pt-br";
import type { WebsiteContent, WebsiteLocale } from "./types";

export { supportedLocales, type WebsiteContent, type WebsiteLocale } from "./types";

export const websiteContent = {
  en,
  de,
  nl,
  fr,
  es,
  it,
  "pt-br": ptbr,
  pl,
} satisfies Record<WebsiteLocale, WebsiteContent>;

export const faqItems = websiteContent.en.faqItems;
export const translationTiers = websiteContent.en.translations.tiers;
