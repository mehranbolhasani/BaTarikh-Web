import { Signature } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative md:sticky md:bottom-0 mx-auto max-w-full pb-12 pt-24 pl-4 md:pt-0 col-span-1">
      <div className="flex flex-col items-start justify-between text-sm text-neutral-600 leading-relaxed">
        <span className="h-3 w-3 bg-neutral-600 mb-2"></span>
        <p>
          <span>به سعی مهران بوالحسنی، به منظور در دسترس‌تر بودن محتوای ارزشمند تاریخی // برای </span>
          <a href="https://t.me/batarikh" target="_blank" rel="noopener noreferrer" className="text-neutral-700 font-semibold">
کانال تلگرام «با تاریخ»</a>
        <span> و حمیدرضا یوسفی</span>
        </p>
        <p className="py-2">۱۴۰۴ - ۲۰۲۵</p>
        <p>
          <Signature className="inline-block h-6 w-6 text-neutral-400" />
        </p>
      </div>
    </footer>
  )
}

