import Image from "next/image"
import batarikh from "@/app/img/batarikh.jpg"

export function Header() {
  return (
    <header className="relative md:sticky top-0 md:top-4 h-[400px] md:h-[600px] bg-white rounded-2xl flex flex-col items-start overflow-hidden backdrop-blur-lg border border-white col-span-1 gap-8 shadow-sm mb-6 md:mb-0">
      <div className="w-full h-2/3 relative">
        <Image
          src={batarikh}
          alt="پس‌زمینه باتاریخ"
          fill
          priority
          sizes="(min-width:1024px) 100vw, 100vw"
          className="object-cover"
        />
        <span className="absolute bottom-4 right-4 text-xs text-neutral-100 z-10 bg-neutral-950 px-3 py-2 rounded-full font-medium tracking-tighter">از راست: کاوه گلستان، منوچهر دقتی و عباس عطار</span>
      </div>
      <div className="flex items-center justify-between relative z-10">
        <div className="pr-4 flex flex-col gap-4 border-r-4 border-neutral-600">
          <h1 className="text-2xl md:text-4xl font-peyda-extrablack text-neutral-800">با تــاریـخ</h1>
          <p className="text-md text-muted-foreground max-w-full md:max-w-2/3">نه بودن‌ِمان نه رفتن‌ِمان فرقی به حال دنیا نمی‌کند.</p>
        </div>
      </div>
    </header>
  )
}
