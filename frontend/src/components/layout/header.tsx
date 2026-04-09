"use client";

import Image from "next/image";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { KAM_LIST } from "@/lib/constants";
import { useKamSelector } from "@/hooks/use-kam-selector";

export function Header() {
  const { currentKam, setKam } = useKamSelector();

  return (
    <header className="bg-white px-4 py-3 sm:px-6 sm:py-4 flex items-center justify-between">
      <Image
        src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Rappi_logo.svg/1280px-Rappi_logo.svg.png"
        alt="Rappi"
        width={140}
        height={47}
        priority
        unoptimized
      />
      <Select value={currentKam} onValueChange={(v) => v && setKam(v)}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select KAM" />
        </SelectTrigger>
        <SelectContent>
          {KAM_LIST.map((kam) => (
            <SelectItem key={kam} value={kam}>
              {kam}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </header>
  );
}
