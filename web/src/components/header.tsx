export function Header() {
  return (
    <header className="sticky top-4 h-[600px] bg-white/60 rounded-2xl flex flex-col items-start overflow-hidden backdrop-blur-lg border border-white col-span-1 gap-8 shadow-sm">
      <div className="w-full h-2/3">
        <div className="bg-[url('./img/batarikh.jpg')] bg-center w-full h-full bg-size-[150%]"></div>
      </div>
      <div className="flex items-center justify-between relative z-10">
        <div className="pr-4 flex flex-col gap-4 border-r-4 border-neutral-600">
          <h1 className="text-4xl font-peyda-extrablack text-neutral-800">با تــاریـخ</h1>
          <p className="text-md text-muted-foreground max-w-2/3">نه بودن‌ِمان نه رفتن‌ِمان فرقی به حال دنیا نمی‌کند.</p>
        </div>
      </div>
    </header>
  )
}

