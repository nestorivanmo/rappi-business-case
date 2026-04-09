"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { kamToSlug, slugToKam } from "@/lib/constants";

export function useKamSelector() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = searchParams.get("kam") || "ana-torres";
  const currentKam = slugToKam(slug);

  const setKam = (kam: string) => {
    router.push(`/dashboard?kam=${kamToSlug(kam)}`);
  };

  return { currentKam, setKam };
}
